from __future__ import annotations

from fastapi.testclient import TestClient


BETA = "https://testing-seven-umber-19.vercel.app"
LOCAL = "http://localhost:3000"


def test_cors_allows_website_beta_and_localhost(client: TestClient) -> None:
    for origin in (BETA, LOCAL):
        response = client.options(
            "/health",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code in {200, 204}
        assert response.headers.get("access-control-allow-origin") == origin


def test_cors_allows_other_vercel_previews(client: TestClient) -> None:
    origin = "https://testing-abc123-aftertax.vercel.app"
    response = client.get("/health", headers={"Origin": origin})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
