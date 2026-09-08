from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_stays_up_while_seed_running(client: TestClient, monkeypatch) -> None:
    import app.main as main

    monkeypatch.setitem(main._seed_state, "status", "running")
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["seed"] == "running"


def test_seed_on_start_loads_full_fixture_book(client: TestClient) -> None:
    from sqlalchemy import func, select

    from app import db as app_db
    from app.main import _seed_fixture_if_empty
    from app.models import DistributionEstimate

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
