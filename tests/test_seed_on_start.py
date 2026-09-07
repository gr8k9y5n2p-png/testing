from __future__ import annotations

from fastapi.testclient import TestClient


def test_seed_on_start_loads_american_funds_when_empty(client: TestClient, monkeypatch) -> None:
    from app.main import _seed_fixture_if_empty

    _seed_fixture_if_empty()
    search = client.get("/distributions", params={"q": "AMCAP", "page_size": 5})
    assert search.status_code == 200
    assert search.json()["total"] >= 1
