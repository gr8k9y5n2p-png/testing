from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.sources.parser import NormalizedRecord


@dataclass
class FetchResult:
    records: list[NormalizedRecord]
    source_urls: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


class FundSource(ABC):
    """Pluggable fetcher/parser for one fund family."""

    slug: str
    display_name: str
    implemented: bool = True
    coverage_tier: str = "implemented"  # implemented | stub
    aum_rank: int | None = None
    priority: int | None = None
    notes: str | None = None

    @abstractmethod
    def fetch(self, *, mode: str = "fixture") -> FetchResult:
        """Return normalized distribution estimate records.

        mode: "fixture" reads bundled HTML; "live" performs HTTP GETs.
        """

    def source_urls(self) -> list[str]:
        return []

    def estimate_feed_urls(self) -> list[str]:
        """Public estimate hub / PDF URLs the weekly scrape should walk.

        May be seasonal or empty. Do not invent amounts when the page has no book.
        """
        return []

    def supports_live(self) -> bool:
        """True when at least one public HTML page is marked live=True."""
        return False
