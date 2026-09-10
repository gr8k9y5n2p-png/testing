from __future__ import annotations

from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import OperationalError


def _agthx_record() -> dict:
    return {
        "fund_family": "American Funds",
        "fund_name": "The Growth Fund of America",
        "ticker": "AGTHX",
        "estimate_type": "long_term_capital_gains",
        "amount": "2.12",
        "amount_unit": "per_share",
        "as_of": "2025-12-18",
        "publication_stage": "final",
    }


def _reset_seed_state() -> None:
    import app.main as main

    main._seed_state.update({"status": "idle", "created": 0, "error": None})


def test_health_stays_up_while_seed_running(client: TestClient, monkeypatch) -> None:
    import app.main as main

    monkeypatch.setitem(main._seed_state, "status", "running")
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["seed"] == "running"


def test_health_ok_when_db_ping_busy(client: TestClient, monkeypatch) -> None:
    import app.api as api
    import app.main as main

    monkeypatch.setattr(api, "ping_db", lambda: "busy: OperationalError")
    monkeypatch.setitem(main._seed_state, "status", "running")
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["db"].startswith("busy")
    assert body["seed"] == "running"


def test_funds_agthx_ok_while_seed_running(client: TestClient, monkeypatch) -> None:
    import app.main as main

    seeded = client.post("/ingest/distributions", json={"records": [_agthx_record()]})
    assert seeded.status_code == 200, seeded.text
    monkeypatch.setitem(main._seed_state, "status", "running")
    response = client.get("/funds", params={"q": "AGTHX"})
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["ticker"] == "AGTHX"


def test_sqlite_file_uses_wal(engine) -> None:
    if engine.dialect.name != "sqlite":
        import pytest

        pytest.skip("PRAGMA journal_mode is SQLite-only")
    with engine.connect() as conn:
        mode = conn.execute(text("PRAGMA journal_mode")).scalar()
    assert str(mode).lower() == "wal"


def test_sqlite_file_uses_null_pool(engine) -> None:
    if engine.dialect.name != "sqlite":
        import pytest

        pytest.skip("NullPool + WAL is the file-SQLite path")
    from sqlalchemy.pool import NullPool

    assert isinstance(engine.pool, NullPool)


def test_sqlite_search_indexes_exist(engine) -> None:
    from sqlalchemy import inspect

    names = {idx.get("name") for idx in inspect(engine).get_indexes("distribution_estimates")}
    assert "ix_dist_fund_identifier" in names
    assert "ix_dist_publication_stage" in names
    assert "ix_dist_fund_search" in names


def test_read_with_lock_retry_recovers_from_locked() -> None:
    from app.db import read_with_lock_retry

    calls = {"n": 0}

    def op() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise OperationalError("SELECT 1", {}, Exception("database is locked"))
        return "ok"

    assert read_with_lock_retry(op) == "ok"
    assert calls["n"] == 3


def test_fixture_fingerprint_is_stable() -> None:
    from app.services.boot_seed import fixture_fingerprint

    first = fixture_fingerprint("american_funds")
    second = fixture_fingerprint("american_funds")
    assert first
    assert first == second
    assert fixture_fingerprint("not_a_real_family_dir") == ""


def test_warm_family_is_not_rebuilt(session) -> None:
    from app.crud import upsert_records
    from app.schemas import DistributionIn
    from app.services.boot_seed import families_needing_seed
    from app.sources.american_funds import AmericanFundsSource
    from app.sources.third_tier import DodgeCoxSource

    upsert_records(session, [DistributionIn(**_agthx_record())], scrub_stale_prelims=False)
    session.commit()
    needed, recorded_warm = families_needing_seed(
        session,
        sources=[AmericanFundsSource(), DodgeCoxSource()],
    )
    slugs = [source.slug for source in needed]
    assert "american_funds" not in slugs
    assert recorded_warm == 1
    assert "dodge_cox" in slugs


def test_changed_fingerprint_densifies_that_family(session) -> None:
    from app.crud import upsert_records
    from app.models import SeedFamilyState
    from app.schemas import DistributionIn
    from app.services.boot_seed import families_needing_seed, fixture_fingerprint
    from app.sources.american_funds import AmericanFundsSource

    upsert_records(session, [DistributionIn(**_agthx_record())], scrub_stale_prelims=False)
    session.commit()
    families_needing_seed(session, sources=[AmericanFundsSource()])
    session.commit()
    row = session.get(SeedFamilyState, "american_funds")
    assert row is not None
    assert row.fixture_fingerprint == fixture_fingerprint("american_funds")
    row.fixture_fingerprint = "stale-fingerprint"
    session.commit()
    needed, _warm = families_needing_seed(session, sources=[AmericanFundsSource()])
    assert [source.slug for source in needed] == ["american_funds"]


def test_boot_seed_ingests_only_missing_family(client: TestClient, monkeypatch) -> None:
    from app.services import boot_seed
    from app.sources.american_funds import AmericanFundsSource
    from app.sources.third_tier import DodgeCoxSource

    _reset_seed_state()
    seeded = client.post("/ingest/distributions", json={"records": [_agthx_record()]})
    assert seeded.status_code == 200, seeded.text

    called: list[str] = []

    def fake_fetch(_session, slug: str, _mode, review_outliers=False):
        called.append(slug)
        return SimpleNamespace(created=0, updated=0)

    monkeypatch.setattr("app.services.ingest.fetch_and_ingest", fake_fetch)
    monkeypatch.setattr(boot_seed, "list_sources", lambda: [AmericanFundsSource(), DodgeCoxSource()])
    monkeypatch.setattr(
        "app.services.nav.refresh_navs",
        lambda *_a, **_k: SimpleNamespace(created=0, updated=0, unknown=0),
    )
    monkeypatch.setattr("app.services.quality.flag_category_outliers", lambda *_a, **_k: 0)

    from app.main import _seed_fixture_if_empty

    _seed_fixture_if_empty()
    assert called == ["dodge_cox"]
    _reset_seed_state()


def test_seed_on_start_loads_full_fixture_book(client: TestClient) -> None:
    from sqlalchemy import func, select

    from app import db as app_db
    from app.main import _seed_fixture_if_empty
    from app.models import DistributionEstimate

    _reset_seed_state()
    _seed_fixture_if_empty()
    assert app_db.SessionLocal is not None
    with app_db.SessionLocal() as session:
        count = session.scalar(select(func.count()).select_from(DistributionEstimate)) or 0
    assert count >= 5000

    amcap = client.get("/distributions", params={"q": "AMCAP", "page_size": 5})
    assert amcap.status_code == 200
    assert amcap.json()["total"] >= 1

    dodix = client.get("/distributions", params={"fund_identifier": "DODIX", "page_size": 5})
    assert dodix.status_code == 200
    assert dodix.json()["total"] >= 1

    dodgx = client.get("/distributions", params={"fund_identifier": "DODGX", "page_size": 5})
    assert dodgx.status_code == 200
    assert dodgx.json()["total"] >= 1

    vfiax = client.get("/distributions", params={"fund_identifier": "VFIAX", "page_size": 5})
    assert vfiax.status_code == 200
    assert vfiax.json()["total"] >= 1

    sgenx = client.get("/distributions", params={"fund_identifier": "SGENX", "page_size": 5})
    assert sgenx.status_code == 200
    assert sgenx.json()["total"] >= 1
    _reset_seed_state()


def test_concurrent_funds_burst_leaves_health_green(client: TestClient) -> None:
    """Acceptance: 8-way Search burst returns 200 and does not take /health down."""
    import asyncio

    import anyio
    from httpx import ASGITransport, AsyncClient

    from app.main import app

    for family in ("american_funds", "fidelity"):
        fetched = client.post("/ingest/fetch", json={"fund_family": family, "mode": "fixture"})
        assert fetched.status_code == 200, fetched.text

    tickers = ["FBGRX", "AGTHX", "FCNTX", "ABALX"]

    async def burst() -> tuple[list[int], list[int], list[str]]:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            responses = await asyncio.gather(
                *[ac.get("/funds", params={"q": ticker}) for ticker in tickers for _ in range(2)]
            )
            healths = [await ac.get("/health") for _ in range(5)]
            return (
                [response.status_code for response in responses],
                [health.status_code for health in healths],
                [health.json()["status"] for health in healths],
            )

    fund_codes, health_codes, health_status = anyio.run(burst)
    assert fund_codes == [200] * 8
    assert health_codes == [200] * 5
    assert health_status == ["ok"] * 5
    for ticker in tickers:
        found = client.get("/funds", params={"q": ticker})
        assert found.status_code == 200
        assert found.json()["total"] >= 1
