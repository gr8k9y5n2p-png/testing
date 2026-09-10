from __future__ import annotations

import time
from collections.abc import Callable, Generator
from typing import TypeVar

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

T = TypeVar("T")


class Base(DeclarativeBase):
    pass


_engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None


def _sqlite_file_url(url: str) -> bool:
    return url.startswith("sqlite") and ":memory:" not in url


def _sqlite_connect_args(url: str) -> dict:
    if url.startswith("sqlite"):
        # timeout is sqlite3 busy-wait seconds; WAL lets readers proceed during seed.
        return {"check_same_thread": False, "timeout": 8.0}
    return {}


def get_engine() -> Engine:
    global _engine, SessionLocal
    if _engine is None:
        configure_engine(settings.database_url)
    assert _engine is not None
    return _engine


def configure_engine(database_url: str) -> Engine:
    global _engine, SessionLocal
    if _engine is not None:
        _engine.dispose()
    kwargs: dict = {"future": True, "pool_pre_ping": True}
    connect_args = _sqlite_connect_args(database_url)
    if connect_args:
        kwargs["connect_args"] = connect_args
        if database_url in {"sqlite://", "sqlite:///:memory:"}:
            from sqlalchemy.pool import StaticPool

            kwargs["poolclass"] = StaticPool
    _engine = create_engine(database_url, **kwargs)

    if database_url.startswith("sqlite"):

        @event.listens_for(_engine, "connect")
        def _sqlite_pragmas(dbapi_conn, _rec) -> None:  # type: ignore[no-untyped-def]
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            if _sqlite_file_url(database_url):
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA busy_timeout=8000")
                cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()

    SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False, class_=Session)
    return _engine


def _ensure_quality_columns(engine: Engine) -> None:
    """Add review-flag columns on existing SQLite disks (create_all will not ALTER)."""
    inspector = inspect(engine)
    if "distribution_estimates" not in inspector.get_table_names():
        return
    existing = {col["name"] for col in inspector.get_columns("distribution_estimates")}
    statements: list[str] = []
    if "needs_review" not in existing:
        statements.append(
            "ALTER TABLE distribution_estimates ADD COLUMN needs_review BOOLEAN NOT NULL DEFAULT 0"
        )
    if "review_reason" not in existing:
        statements.append("ALTER TABLE distribution_estimates ADD COLUMN review_reason VARCHAR(64)")
    if "data_quality_flags" not in existing:
        statements.append("ALTER TABLE distribution_estimates ADD COLUMN data_quality_flags JSON")
    if not statements:
        return
    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))


def init_db() -> None:
    from app import models  # noqa: F401

    engine = get_engine()
    Base.metadata.create_all(engine)
    _ensure_quality_columns(engine)


def ping_db() -> str:
    """Cheap liveness ping. Never raises — /health must stay 200 once HTTP is up."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return "ok"
    except Exception as exc:
        return f"busy: {type(exc).__name__}"


def read_with_lock_retry(op: Callable[[], T], *, attempts: int = 5) -> T:
    """Retry a read when SQLite reports locked/busy (mid-seed writers)."""
    delay = 0.05
    last: OperationalError | None = None
    for attempt in range(attempts):
        try:
            return op()
        except OperationalError as exc:
            last = exc
            msg = str(exc).lower()
            if attempt == attempts - 1 or not any(token in msg for token in ("locked", "busy")):
                raise
            time.sleep(delay)
            delay = min(delay * 2, 0.4)
    assert last is not None
    raise last


def get_session() -> Generator[Session, None, None]:
    if SessionLocal is None:
        get_engine()
    assert SessionLocal is not None
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
