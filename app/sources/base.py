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
    notes: str | None = None

    @abstractmethod
    def fetch(self, *, mode: str = "fixture") -> FetchResult:
        """Return normalized distribution estimate records.

        mode: "fixture" reads bundled HTML; "live" performs HTTP GETs.
        """

    def source_urls(self) -> list[str]:
        return []
