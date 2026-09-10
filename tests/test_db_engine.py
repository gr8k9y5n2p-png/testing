from __future__ import annotations

from sqlalchemy.pool import NullPool, QueuePool

from app.config import is_postgres_url, is_sqlite_url, rewrite_database_url
from app.db import (
    PG_MAX_OVERFLOW,
    PG_POOL_RECYCLE_SECONDS,
    PG_POOL_SIZE,
    make_engine,
)


def test_rewrite_postgres_and_postgresql_to_psycopg3() -> None:
    assert (
        rewrite_database_url("postgres://u:p@host:5432/distributions")
        == "postgresql+psycopg://u:p@host:5432/distributions"
    )
    assert (
        rewrite_database_url("postgresql://u:p@host/distributions?sslmode=require")
        == "postgresql+psycopg://u:p@host/distributions?sslmode=require"
    )
    assert (
        rewrite_database_url("postgresql+psycopg2://u:p@host/db")
        == "postgresql+psycopg://u:p@host/db"
    )
    already = "postgresql+psycopg://u:p@host/db"
    assert rewrite_database_url(already) == already
    sqlite = "sqlite:////var/data/distributions.db"
    assert rewrite_database_url(sqlite) == sqlite
    assert is_postgres_url("postgres://u:p@h/db")
    assert is_sqlite_url(sqlite)
    assert not is_postgres_url(sqlite)


def test_postgres_engine_uses_queue_pool_without_connecting() -> None:
    engine = make_engine("postgresql+psycopg://distributions:distributions@localhost:5432/distributions")
    try:
        assert isinstance(engine.pool, QueuePool)
        assert engine.pool.size() == PG_POOL_SIZE
        assert engine.pool._max_overflow == PG_MAX_OVERFLOW
        assert engine.pool._recycle == PG_POOL_RECYCLE_SECONDS
        assert engine.dialect.name == "postgresql"
    finally:
        engine.dispose()


def test_file_sqlite_engine_keeps_null_pool(tmp_path) -> None:
    url = f"sqlite:///{tmp_path / 'beta.db'}"
    engine = make_engine(url)
    try:
        assert isinstance(engine.pool, NullPool)
        with engine.connect() as conn:
            mode = conn.exec_driver_sql("PRAGMA journal_mode").scalar()
        assert str(mode).lower() == "wal"
    finally:
        engine.dispose()
