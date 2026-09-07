from __future__ import annotations

from app.sources.base import FetchResult, FundSource


class StubFundSource(FundSource):
    """Placeholder so additional families can be registered before a parser exists."""

    implemented = False

    def __init__(self, slug: str, display_name: str, notes: str, urls: list[str] | None = None) -> None:
        self.slug = slug
        self.display_name = display_name
        self.notes = notes
        self._urls = urls or []

    def source_urls(self) -> list[str]:
        return list(self._urls)

    def fetch(self, *, mode: str = "fixture") -> FetchResult:
        raise NotImplementedError(
            f"{self.display_name} adapter is registered but not implemented yet. "
            f"See README (Adding a fund-family adapter). Notes: {self.notes}"
        )
