from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import httpx

from app.config import settings
from app.sources.aum import filter_large_aum
from app.sources.base import FetchResult, FundSource
from app.sources.ici import ici_as_of_from_name, parse_ici_primary
from app.sources.parser import parse_distribution_html


@dataclass(frozen=True)
class PageSpec:
    name: str
    url: str
    fixture: str
    live: bool = True
    parser: str = "html"  # html | ici
    large_aum_only: bool = False
    role: str = "book"  # estimate | book | history
    empty_ok: bool = False  # seasonal estimate hubs may publish no table yet


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

    def estimate_feed_urls(self) -> list[str]:
        urls = [
            page.url
            for page in self.pages()
            if page.role == "estimate" and not page.url.startswith("fixture://")
        ]
        return list(dict.fromkeys(urls))

    def pages(self) -> list[PageSpec]:
        raise NotImplementedError

    def supports_live(self) -> bool:
        return any(page.live for page in self.pages())

    def fetch(self, *, mode: str = "fixture") -> FetchResult:
        if mode == "live":
            return self._fetch_live_or_fixture()
        pages, notes = self._load_pages(mode="fixture")
        return self._parse_pages(pages, extra_notes=notes)

    def _fetch_live_or_fixture(self) -> FetchResult:
        notes: list[str] = []
        walked = [
            page.url
            for page in self.pages()
            if page.live and not page.url.startswith("fixture://")
        ]
        try:
            live_pages, load_notes = self._load_pages(mode="live")
            notes.extend(load_notes)
        except Exception as exc:
            notes.append(f"Live fetch failed ({exc}). {self.live_limitations or 'Using fixtures.'}")
            fixture_pages, fixture_notes = self._load_pages(mode="fixture")
            fixture = self._parse_pages(fixture_pages, extra_notes=[*notes, *fixture_notes])
            fixture.source_urls = list(dict.fromkeys([*walked, *fixture.source_urls]))
            return fixture

        live_result = self._parse_pages(live_pages, extra_notes=notes)
        if live_result.records:
            live_result.source_urls = list(dict.fromkeys([*walked, *live_result.source_urls]))
            return live_result
        notes.append(
            "Live fetch returned 0 parseable rows (seasonal empty, JavaScript, PDF, or login-walled). "
            + (self.live_limitations or "Falling back to fixtures.")
        )
        fixture_pages, fixture_notes = self._load_pages(mode="fixture")
        fixture = self._parse_pages(fixture_pages, extra_notes=[*notes, *fixture_notes])
        fixture.source_urls = list(dict.fromkeys([*walked, *live_result.source_urls, *fixture.source_urls]))
        return fixture

    def _load_pages(self, *, mode: str) -> tuple[list[dict], list[str]]:
        out: list[dict] = []
        notes: list[str] = []
        live_configured = any(spec.live for spec in self.pages())
        for spec in self.pages():
            if mode == "live" and not spec.live:
                continue
            if mode == "fixture" or spec.url.startswith("fixture://"):
                path = self.fixtures_dir / spec.fixture
                html = path.read_text(encoding="utf-8")
                url = spec.url
            else:
                try:
                    html = self._http_get(spec.url)
                except Exception as exc:
                    kind = "estimate hub" if spec.role == "estimate" or spec.empty_ok else "page"
                    notes.append(
                        f"{spec.name}: live {kind} unavailable ({exc}). "
                        "Seasonal empty / unpublished — no-op."
                    )
                    continue
                url = spec.url
            out.append(
                {
                    "name": spec.name,
                    "url": url,
                    "html": html,
                    "parser": spec.parser,
                    "large_aum_only": spec.large_aum_only,
                }
            )
        if mode == "live" and not live_configured:
            raise RuntimeError(f"No live pages configured for {self.slug}.")
        return out, notes

    def _parse_pages(self, pages: list[dict], extra_notes: list[str]) -> FetchResult:
        records = []
        urls: list[str] = []
        notes = list(extra_notes)
        for page in pages:
            if page.get("parser") == "ici":
                parsed = parse_ici_primary(
                    page["html"],
                    source_url=page["url"],
                    fund_family=self.display_name,
                    default_as_of=ici_as_of_from_name(page["name"]),
                )
            else:
                parsed = parse_distribution_html(
                    page["html"],
                    source_url=page["url"],
                    fund_family=self.display_name,
                )
            if page.get("large_aum_only"):
                before = len(parsed)
                parsed = filter_large_aum(parsed)
                notes.append(
                    f"{page['name']}: {len(parsed)} records "
                    f"(ICI/large-AUM filter kept {len(parsed)} of {before})"
                )
            else:
                notes.append(f"{page['name']}: {len(parsed)} records")
            records.extend(parsed)
            urls.append(page["url"])
        return FetchResult(records=records, source_urls=urls, notes=notes)

    def _http_get(self, url: str) -> str:
        headers = {
            "User-Agent": settings.http_user_agent,
            "Accept": "text/html,application/xhtml+xml,application/pdf,*/*",
        }
        with httpx.Client(timeout=settings.http_timeout_seconds, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            ctype = (response.headers.get("content-type") or "").lower()
            if any(token in ctype for token in ("pdf", "spreadsheet", "excel", "ms-excel", "octet-stream")):
                # Weekly walk hit the real file; HTML parser cannot transcribe bytes.
                return ""
            return response.text
