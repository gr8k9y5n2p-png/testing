"""Compare / leftover 5y Growth of $X fixtures + distribution-day NAV.

Yahoo monthly adj-close and Yahoo last regular close on/before ex/payable.
Never invents returns or NAVs. Digest pins are unchanged (additive only).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import settings
from app.services.nav import load_history_catalog, lookup_nav_on_day
from app.services.performance import FUND_META

PERF_DIR = Path(settings.fixtures_dir) / "performance"

COMPARE_HEROES = (
    ("WHOSX", "fixed_income", "AGG"),
    ("WMCVX", "equity", "SPY"),
    ("GQETX", "equity", "SPY"),
    ("VYCAX", "equity", "SPY"),
    ("BRUSX", "equity", "SPY"),
    ("ARGFX", "equity", "SPY"),
    ("POSKX", "equity", "SPY"),
)

MAX_REACH = (
    "ARAIX",
    "BMDIX",
    "BMDSX",
    "BOSVX",
    "CIPIX",
    "CIPNX",
    "DHIAX",
    "DHMAX",
    "DHPAX",
    "DHSCX",
    "DHTAX",
    "DIAMX",
    "GMUEX",
    "GTMIX",
    "HWAIX",
    "HWLIX",
    "HWNIX",
    "PAXDX",
    "PAXGX",
    "PAXIX",
    "PAXLX",
    "PAXWX",
    "PGINX",
    "PGRNX",
    "POAGX",
    "POGRX",
    "PWGIX",
    "PXDIX",
    "PXEAX",
    "PXGAX",
    "PXGOX",
    "PXINX",
    "PXLIX",
    "PXNIX",
    "PXWEX",
    "PXWGX",
    "PXWIX",
)

YAHOO_WALLS = ("BRAGX", "BRSVX")

HERO_DIST_DAYS = {
    "WHOSX": date(2021, 12, 16),
    "WMCVX": date(2022, 12, 16),
    "GQETX": date(2025, 12, 12),
    "VYCAX": date(2021, 12, 16),
    "BRUSX": date(2025, 12, 16),
    "ARGFX": date(2024, 12, 18),
    "POSKX": date(2025, 12, 15),
}


def test_compare_heroes_gain_performance_fixtures() -> None:
    for ticker, asset_class, _bench in COMPARE_HEROES:
        path = PERF_DIR / f"{ticker}.json"
        assert path.exists(), ticker
        assert FUND_META[ticker]["asset_class"] == asset_class


def test_max_reach_leftover_5y_performance_fixtures() -> None:
    missing = [ticker for ticker in MAX_REACH if not (PERF_DIR / f"{ticker}.json").exists()]
    assert missing == []


def test_yahoo_walls_have_no_invented_performance() -> None:
    for ticker in YAHOO_WALLS:
        assert not (PERF_DIR / f"{ticker}.json").exists(), ticker
        assert ticker not in FUND_META


def test_get_performance_compare_heroes(client: TestClient) -> None:
    for ticker, asset_class, bench in COMPARE_HEROES:
        response = client.get("/performance", params={"ticker": ticker, "mode": "fixture"})
        assert response.status_code == 200, f"{ticker}: {response.text}"
        body = response.json()
        assert body["fund_ticker"] == ticker
        assert body["asset_class"] == asset_class
        assert body["benchmark_id"] == bench
        assert len(body["fund"]["points"]) >= 12
        assert Decimal(body["fund"]["points"][0]["growth_of_x"]) == Decimal("10000.00")


def test_get_performance_yahoo_walls_404(client: TestClient) -> None:
    for ticker in YAHOO_WALLS:
        response = client.get("/performance", params={"ticker": ticker, "mode": "fixture"})
        assert response.status_code == 404, ticker
        assert "No performance fixture" in response.json()["detail"]


def test_hist_nav_on_hero_distribution_days(session) -> None:
    catalog = load_history_catalog()
    for ticker, day in HERO_DIST_DAYS.items():
        quote = lookup_nav_on_day(session, ticker, day, catalog=catalog)
        assert quote is not None, (ticker, day)
        assert quote.nav_per_share > 0
        assert (day - quote.nav_as_of).days <= 7
        assert quote.nav_as_of <= day


def test_hist_nav_is_not_today_weekly_print(session) -> None:
    """Historical % of NAV must use the print on/before ex/payable, not 2026 weekly NAV."""
    catalog = load_history_catalog()
    quote = lookup_nav_on_day(session, "WHOSX", date(2021, 12, 16), catalog=catalog)
    assert quote is not None
    assert quote.nav_as_of == date(2021, 12, 15)
    assert quote.nav_per_share == Decimal("19.150000")
    later = lookup_nav_on_day(session, "WHOSX", date(2025, 12, 18), catalog=catalog)
    assert later is not None
    assert later.nav_as_of == date(2025, 12, 17)
    assert later.nav_per_share == Decimal("10.260000")
    assert later.nav_per_share != quote.nav_per_share
