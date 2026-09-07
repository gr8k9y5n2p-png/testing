from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import httpx

from app.config import settings
from app.sources.base import FetchResult, FundSource
from app.sources.parser import parse_distribution_html


@dataclass(frozen=True)
class PageSpec:
    name: str
    url: str
    fixture: str
    live: bool = True


class HtmlTableSource(FundSource):
    """Generic HTML-table adapter: fixture files plus optional live GET with fallback."""

    implemented = True
    coverage_tier = "implemented"
    live_limitations: str | None = None

    def __init__(self, fixtures_dir: Path | None = None) -> None:
        root = Path(fixtures_dir or settings.fixtures_dir)
        self.fixtures_dir = root / self.slug

    def source_urls(self) -> list[str]:
        return [page.url for page in self.pages() if not page.url.startswith("fixture://")]

    def pages(self) -> list[PageSpec]:
        raise NotImplementedError

    def fetch(self, *, mode: str = "fixture") -> FetchResult:
        if mode == "live":
            return self._fetch_live_or_fixture()
        return self._parse_pages(self._load_pages(mode="fixture"), extra_notes=[])

    def _fetch_live_or_fixture(self) -> FetchResult:
        notes: list[str] = []
        live_pages: list[dict] = []
        try:
            live_pages = self._load_pages(mode="live")
        except Exception as exc:
            notes.append(f"Live fetch failed ({exc}). {self.live_limitations or 'Using fixtures.'}")
            fixture = self._parse_pages(self._load_pages(mode="fixture"), extra_notes=notes)
            return fixture

        live_result = self._parse_pages(live_pages, extra_notes=notes)
        if live_result.records:
            return live_result
        notes.append(
            "Live fetch returned 0 parseable rows (JavaScript, PDF, or login-walled page). "
            + (self.live_limitations or "Falling back to fixtures.")
        )
        fixture = self._parse_pages(self._load_pages(mode="fixture"), extra_notes=notes)
        fixture.source_urls = list(dict.fromkeys([*live_result.source_urls, *fixture.source_urls]))
        return fixture

    def _load_pages(self, *, mode: str) -> list[dict]:
        out: list[dict] = []
        for spec in self.pages():
            if mode == "live" and not spec.live:
                continue
            if mode == "fixture" or spec.url.startswith("fixture://"):
                path = self.fixtures_dir / spec.fixture
                html = path.read_text(encoding="utf-8")
                url = spec.url
            else:
                html = self._http_get(spec.url)
                url = spec.url
            out.append({"name": spec.name, "url": url, "html": html})
        if mode == "live" and not out:
            raise RuntimeError(f"No live pages configured for {self.slug}.")
        return out

    def _parse_pages(self, pages: list[dict], extra_notes: list[str]) -> FetchResult:
        records = []
        urls: list[str] = []
        notes = list(extra_notes)
        for page in pages:
            parsed = parse_distribution_html(
                page["html"],
                source_url=page["url"],
                fund_family=self.display_name,
            )
            records.extend(parsed)
            urls.append(page["url"])
            notes.append(f"{page['name']}: {len(parsed)} records")
        return FetchResult(records=records, source_urls=urls, notes=notes)

    def _http_get(self, url: str) -> str:
        headers = {
            "User-Agent": settings.http_user_agent,
            "Accept": "text/html,application/xhtml+xml",
        }
        with httpx.Client(timeout=settings.http_timeout_seconds, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
