from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import Base, configure_engine, init_db
from app import db as app_db


@pytest.fixture()
def db_url(tmp_path) -> str:
    return f"sqlite:///{tmp_path / 'test.db'}"


@pytest.fixture()
def engine(db_url: str, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DATABASE_URL", db_url)
    from app import config

    config.settings.database_url = db_url
    engine = configure_engine(db_url)
    init_db()
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def session(engine) -> Generator[Session, None, None]:
    assert app_db.SessionLocal is not None
    db = app_db.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(engine) -> Generator[TestClient, None, None]:
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
