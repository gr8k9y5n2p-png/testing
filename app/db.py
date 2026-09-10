from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


_engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None


def _sqlite_connect_args(url: str) -> dict:
    if url.startswith("sqlite"):
        return {"check_same_thread": False}
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
        def _fk_on(dbapi_conn, _rec) -> None:  # type: ignore[no-untyped-def]
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
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
