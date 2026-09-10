from __future__ import annotations

import time
from collections.abc import Callable, Generator
from typing import TypeVar

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool, StaticPool

from app.config import is_postgres_url, is_sqlite_url, rewrite_database_url, settings

# Lean QueuePool for Postgres (2 workers × 10 checkouts = 20; Basic-1gb allows 100).
PG_POOL_SIZE = 5
PG_MAX_OVERFLOW = 5
PG_POOL_RECYCLE_SECONDS = 1800

T = TypeVar("T")


class Base(DeclarativeBase):
    pass


_engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None


def _sqlite_file_url(url: str) -> bool:
    return is_sqlite_url(url) and ":memory:" not in url


def _sqlite_connect_args(url: str) -> dict:
    if is_sqlite_url(url):
        # timeout is sqlite3 busy-wait seconds; WAL lets readers proceed during seed.
        return {"check_same_thread": False, "timeout": 15.0}
    return {}


def engine_kwargs(database_url: str) -> dict:
    """Dialect-aware create_engine kwargs. Does not connect."""
    database_url = rewrite_database_url(database_url)
    kwargs: dict = {"future": True, "pool_pre_ping": True}
    connect_args = _sqlite_connect_args(database_url)
    if is_postgres_url(database_url):
        kwargs.update(
            {
                "poolclass": QueuePool,
                "pool_size": PG_POOL_SIZE,
                "max_overflow": PG_MAX_OVERFLOW,
                "pool_recycle": PG_POOL_RECYCLE_SECONDS,
            }
        )
    elif connect_args:
        kwargs["connect_args"] = connect_args
        if database_url in {"sqlite://", "sqlite:///:memory:"}:
            kwargs["poolclass"] = StaticPool
        elif _sqlite_file_url(database_url):
            # File SQLite + QueuePool deadlocks under concurrent /funds
            # (pool wait + writer lock). One connection per checkout.
            kwargs["poolclass"] = NullPool
    return kwargs


def make_engine(database_url: str) -> Engine:
    """Create an engine without replacing the process-global SessionLocal."""
    database_url = rewrite_database_url(database_url)
    engine = create_engine(database_url, **engine_kwargs(database_url))
    if is_sqlite_url(database_url):

        @event.listens_for(engine, "connect")
        def _sqlite_pragmas(dbapi_conn, _rec) -> None:  # type: ignore[no-untyped-def]
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            if _sqlite_file_url(database_url):
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA busy_timeout=15000")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.close()

    return engine


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
    _engine = make_engine(database_url)
    SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False, class_=Session)
    return _engine


def _ensure_quality_columns(engine: Engine) -> None:
    """Add review-flag columns on existing SQLite disks (create_all will not ALTER)."""
    if engine.dialect.name != "sqlite":
        return
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


def _ensure_search_indexes(engine: Engine) -> None:
    """Add search indexes on existing SQLite disks (create_all will not ALTER)."""
    if engine.dialect.name != "sqlite":
        return
    inspector = inspect(engine)
    if "distribution_estimates" not in inspector.get_table_names():
        return
    existing = {idx.get("name") for idx in inspector.get_indexes("distribution_estimates")}
    statements: list[str] = []
    if "ix_dist_fund_identifier" not in existing:
        statements.append(
            "CREATE INDEX IF NOT EXISTS ix_dist_fund_identifier "
            "ON distribution_estimates (fund_identifier)"
        )
    if "ix_dist_publication_stage" not in existing:
        statements.append(
            "CREATE INDEX IF NOT EXISTS ix_dist_publication_stage "
            "ON distribution_estimates (publication_stage)"
        )
    if "ix_dist_fund_search" not in existing:
        statements.append(
            "CREATE INDEX IF NOT EXISTS ix_dist_fund_search "
            "ON distribution_estimates ("
            "ticker, fund_identifier, fund_name, fund_family, as_of, ingested_at, id)"
        )
    if not statements:
        return
    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))


def init_db() -> None:
    from app import models  # noqa: F401

    engine = get_engine()
    # Soft-beta / pytest SQLite: create_all + additive _ensure_* patches.
    # Postgres production schema is Alembic (`alembic upgrade head` pre-deploy).
    # create_all remains a no-op when tables already exist (local PG / tests).
    Base.metadata.create_all(engine)
    if engine.dialect.name == "sqlite":
        _ensure_quality_columns(engine)
        _ensure_search_indexes(engine)


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
