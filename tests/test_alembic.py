from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app.db import make_engine

ROOT = Path(__file__).resolve().parent.parent

EXPECTED_TABLES = {
    "distribution_estimates",
    "coverage_gaps",
    "ticker_requests",
    "fund_navs",
    "fund_nav_history",
    "seed_family_state",
    "ingest_runs",
}

EXPECTED_DIST_INDEXES = {
    "ix_dist_ticker",
    "ix_dist_fund_identifier",
    "ix_dist_fund_search",
    "ix_dist_publication_stage",
    "ix_dist_family",
}


def test_alembic_upgrade_head_creates_seven_tables(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "alembic.db"
    url = f"sqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", url)
    from app import config

    config.settings.database_url = url

    cfg = Config(str(ROOT / "alembic.ini"))
    command.upgrade(cfg, "head")

    engine = make_engine(url)
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        assert EXPECTED_TABLES <= tables
        indexes = {idx.get("name") for idx in inspector.get_indexes("distribution_estimates")}
        assert EXPECTED_DIST_INDEXES <= indexes
        uniques = {uc.get("name") for uc in inspector.get_unique_constraints("distribution_estimates")}
        assert "uq_distribution_upsert_key" in uniques
        nav_uniques = {uc.get("name") for uc in inspector.get_unique_constraints("fund_navs")}
        assert "uq_fund_nav_ticker" in nav_uniques
        hist_uniques = {uc.get("name") for uc in inspector.get_unique_constraints("fund_nav_history")}
        assert "uq_fund_nav_history_ticker_as_of" in hist_uniques
    finally:
        engine.dispose()
