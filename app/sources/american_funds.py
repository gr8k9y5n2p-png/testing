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
TAX_CENTER_URL = "https://www.capitalgroup.com/individual/service-and-support/tax-center.html"
CALENDAR_URL = "https://www.capitalgroup.com/individual/news/distribution-dates.html"


class AmericanFundsSource(FundSource):
    slug = "american_funds"
    display_name = "American Funds"
    implemented = True
    notes = (
        "Parses Capital Group public HTML tables (midyear/year-end per-share amounts, "
        "special dividends, qualified-dividend percentages, and estimate % of NAV). "
        "Live year-end *preliminary* estimate pages are seasonal and often advisor-gated; "
        "fixture mode includes a realistic estimate table plus captured live markup."
    )

    def __init__(self, fixtures_dir: Path | None = None) -> None:
        self.fixtures_dir = Path(fixtures_dir or settings.fixtures_dir) / "american_funds"

    def source_urls(self) -> list[str]:
        return [MIDYEAR_2026_URL, YEAR_END_2025_URL, TAX_CENTER_URL, CALENDAR_URL]

    def fetch(self, *, mode: str = "fixture") -> FetchResult:
        pages = self._pages(mode)
        records = []
        urls: list[str] = []
        notes: list[str] = []
        for page in pages:
            html = page["html"]
            url = page["url"]
            urls.append(url)
            parsed = parse_capital_group_html(html, source_url=url, fund_family=self.display_name)
            records.extend(parsed)
            notes.append(f"{page['name']}: {len(parsed)} records")
        return FetchResult(records=records, source_urls=urls, notes=notes)

    def _pages(self, mode: str) -> list[dict]:
        specs = [
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
        ]
        out = []
        for spec in specs:
            if mode == "live" and not spec["live"]:
                continue
            if mode == "fixture":
                path = self.fixtures_dir / spec["fixture"]
                html = path.read_text(encoding="utf-8")
            else:
                html = self._http_get(spec["url"])
            out.append({"name": spec["name"], "url": spec["url"], "html": html})
        if mode == "live" and not out:
            raise RuntimeError("No live Capital Group pages are configured to fetch.")
        return out

    def _http_get(self, url: str) -> str:
        headers = {"User-Agent": settings.http_user_agent, "Accept": "text/html,application/xhtml+xml"}
        with httpx.Client(timeout=settings.http_timeout_seconds, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
