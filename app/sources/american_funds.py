from __future__ import annotations

from pathlib import Path

import httpx

from app.config import settings
from app.sources.base import FetchResult, FundSource
from app.sources.parser import parse_capital_group_html


# Verified public Capital Group / American Funds tax-center pages (2026-09-07).
# Advisor tax-center copies of some URLs require login and 302 to authentication.
MIDYEAR_2026_URL = (
    "https://www.capitalgroup.com/individual/service-and-support/tax-center/midyear-cap-gains.html"
)
YEAR_END_2025_URL = (
    "https://www.capitalgroup.com/individual/service-and-support/tax-center/2025-year-end-distributions.html"
)
YEAR_END_2024_URL = "https://www.capitalgroup.com/advisor/tax/2024-year-end-distributions.html"
TAX_CENTER_URL = "https://www.capitalgroup.com/individual/service-and-support/tax-center.html"
CALENDAR_URL = "https://www.capitalgroup.com/individual/news/distribution-dates.html"
HISTORICAL_TOOL_URL = "https://www.capitalgroup.com/individual/investments/historicaldistributions/"


class AmericanFundsSource(FundSource):
    slug = "american_funds"
    display_name = "American Funds"
    implemented = True
    coverage_tier = "implemented"
    aum_rank = 7
    priority = 7
    notes = (
        "Parses Capital Group public HTML tables (midyear/year-end per-share amounts, "
        "special dividends, and estimate % of NAV). Qualified-dividend income "
        "percentages (% of dividends that are qualified) are 1099 characterizations, "
        "not $/share distributions — skipped, never invented as QDI dollars. "
        "Live year-end *preliminary* estimate pages are seasonal and often advisor-gated; "
        "fixture mode includes estimate + final snapshots for 2024 and 2025 so time-series "
        "(as_of + publication_stage) coexist, plus product-page paid history for AMCAP / "
        "Growth Fund of America / American Balanced (ABALX 2021–2025 December OI; "
        "2022–2023 LTCG published $0 omitted) and ICA / WMIF / New Perspective / "
        "EUPAC / New World / American Mutual / Capital Income Builder / "
        "Fundamental Investors / SMALLCAP World / Income Fund of America / "
        "Bond Fund of America / New Economy / High-Income Trust / Capital "
        "World Bond / U.S. Government Securities / International Growth and "
        "Income Class A pages (2021–2025 tax-year as_of; unpublished December "
        "years stay unmatched). Full public YE CG books for "
        "2021–2024 are Wayback id_ snapshots of the individual tax-center pages (live "
        "URLs now 404; advisor copies 302 to login) stored as year_end_*_tax_year.html "
        "with as_of = published December ex-date so lookback counts the tax year. 2025 "
        "tax-year as_of is the same official YE table as the January 2026 reprint. "
        "Bare QDI % columns omitted. 2024 advisor HTML now 302s to "
        "login; per-fund history also lives at the Historical Distributions tool and on "
        "each fund’s product page (historicalDistributions JSON). "
        "CGHM (inception 6/25/24) has no 2021–2023 history. Official 2024 and 2025 "
        "YE tables list CGHM with em-dash ST/LT (no capital gain — not stored as $0). "
        "The only published CG amounts today are 2026 midyear (LT $0.0030 / ST $0.0169). "
        "Monthly income lives on the JS historical-distributions tool (SPA — skipped)."
    )

    def __init__(self, fixtures_dir: Path | None = None) -> None:
        self.fixtures_dir = Path(fixtures_dir or settings.fixtures_dir) / "american_funds"

    def source_urls(self) -> list[str]:
        return [
            MIDYEAR_2026_URL,
            YEAR_END_2025_URL,
            YEAR_END_2024_URL,
            TAX_CENTER_URL,
            CALENDAR_URL,
            HISTORICAL_TOOL_URL,
            "https://www.capitalgroup.com/individual/investments/mutual-funds/details/amcap-a",
            "https://www.capitalgroup.com/individual/investments/mutual-funds/details/gfa-a",
            "https://www.capitalgroup.com/individual/investments/mutual-funds/details/ambal-a",
        ]

    def estimate_feed_urls(self) -> list[str]:
        return [TAX_CENTER_URL, MIDYEAR_2026_URL, YEAR_END_2025_URL, CALENDAR_URL]

    def supports_live(self) -> bool:
        return True

    def fetch(self, *, mode: str = "fixture") -> FetchResult:
        if mode == "live":
            return self._fetch_live_or_fixture()
        return self._parse_pages(self._pages("fixture"), extra_notes=[])

    def _fetch_live_or_fixture(self) -> FetchResult:
        notes: list[str] = []
        pages = self._pages("live", notes)
        live_result = self._parse_pages(pages, extra_notes=notes)
        if live_result.records:
            live_result.source_urls = list(dict.fromkeys([*self.estimate_feed_urls(), *live_result.source_urls]))
            return live_result
        notes.append(
            "Live fetch returned 0 parseable rows (seasonal estimate page). Falling back to fixtures."
        )
        fixture = self._parse_pages(self._pages("fixture"), extra_notes=notes)
        fixture.source_urls = list(dict.fromkeys([*self.estimate_feed_urls(), *fixture.source_urls]))
        return fixture

    def _parse_pages(self, pages: list[dict], extra_notes: list[str]) -> FetchResult:
        records = []
        urls: list[str] = []
        notes = list(extra_notes)
        for page in pages:
            parsed = parse_capital_group_html(
                page["html"], source_url=page["url"], fund_family=self.display_name
            )
            records.extend(parsed)
            urls.append(page["url"])
            notes.append(f"{page['name']}: {len(parsed)} records")
        return FetchResult(records=records, source_urls=urls, notes=notes)

    def _pages(self, mode: str, notes: list[str] | None = None) -> list[dict]:
        notes = notes if notes is not None else []
        specs = [
            {
                "name": "tax_center",
                "url": TAX_CENTER_URL,
                "fixture": "tax_center_hub.html",
                "live": True,
            },
            {
                "name": "midyear_2026",
                "url": MIDYEAR_2026_URL,
                "fixture": "midyear_2026_cap_gains.html",
                "live": True,
            },
            {
                "name": "year_end_2025",
                "url": YEAR_END_2025_URL,
                "fixture": "year_end_2025_distributions.html",
                "live": True,
            },
            {
                "name": "year_end_estimates",
                "url": "fixture://american_funds/year_end_estimates_sample.html",
                "fixture": "year_end_estimates_sample.html",
                "live": False,
            },
            {
                "name": "year_end_2024",
                "url": YEAR_END_2024_URL,
                "fixture": "year_end_2024_distributions.html",
                "live": False,
            },
            {
                "name": "year_end_2024_estimates",
                "url": "fixture://american_funds/year_end_2024_estimates_sample.html",
                "fixture": "year_end_2024_estimates_sample.html",
                "live": False,
            },
            {
                "name": "paid_history_2021_2025",
                "url": "https://www.capitalgroup.com/individual/investments/mutual-funds/details/amcap-a",
                "fixture": "paid_history_2021_2025.html",
                "live": False,
            },
            {
                "name": "year_end_2021_tax_year",
                "url": "https://www.capitalgroup.com/individual/service-and-support/tax-center/2021-year-end-distributions.html",
                "fixture": "year_end_2021_tax_year.html",
                "live": False,
            },
            {
                "name": "year_end_2022_tax_year",
                "url": "https://www.capitalgroup.com/individual/service-and-support/tax-center/2022-year-end-distributions.html",
                "fixture": "year_end_2022_tax_year.html",
                "live": False,
            },
            {
                "name": "year_end_2023_tax_year",
                "url": "https://www.capitalgroup.com/individual/service-and-support/tax-center/2023-year-end-distributions.html",
                "fixture": "year_end_2023_tax_year.html",
                "live": False,
            },
            {
                "name": "year_end_2024_tax_year",
                "url": "https://www.capitalgroup.com/individual/service-and-support/tax-center/2024-year-end-distributions.html",
                "fixture": "year_end_2024_tax_year.html",
                "live": False,
            },
            {
                "name": "year_end_2025_tax_year",
                "url": YEAR_END_2025_URL,
                "fixture": "year_end_2025_tax_year.html",
                "live": False,
            },
        ]
        out = []
        for spec in specs:
            if mode == "live" and not spec["live"]:
                continue
            if mode == "fixture" or spec["url"].startswith("fixture://"):
                path = self.fixtures_dir / spec["fixture"]
                html = path.read_text(encoding="utf-8")
            else:
                try:
                    html = self._http_get(spec["url"])
                except Exception as exc:
                    notes.append(
                        f"{spec['name']}: live estimate hub unavailable ({exc}). "
                        "Seasonal empty / unpublished — no-op."
                    )
                    continue
            out.append({"name": spec["name"], "url": spec["url"], "html": html})
        if mode == "live" and not any(spec["live"] for spec in specs):
            raise RuntimeError("No live Capital Group pages are configured to fetch.")
        return out

    def _http_get(self, url: str) -> str:
        headers = {"User-Agent": settings.http_user_agent, "Accept": "text/html,application/xhtml+xml"}
        with httpx.Client(timeout=settings.http_timeout_seconds, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
