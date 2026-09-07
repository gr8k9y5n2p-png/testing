"""Weekly all-family refresh: live first where supported, fixture fallback."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.crud import record_ingest_run, upsert_records
from app.models import IngestRun
from app.services.ingest import normalized_to_in
from app.sources.base import FetchResult, FundSource
from app.sources.registry import resolve_families

REFRESH_MODES = ("auto", "live", "fixture")


@dataclass
class FamilyRefreshResult:
    slug: str
    status: str
    mode_used: str
    created: int
    updated: int
    error: str | None = None
    notes: list[str] = field(default_factory=list)
    source_urls: list[str] = field(default_factory=list)


@dataclass
class RefreshSummary:
    mode: str
    families_attempted: int
    created: int
    updated: int
    errors: list[str]
    live_vs_fixture: dict[str, int]
    families: list[FamilyRefreshResult] = field(default_factory=list)

    @property
    def hard_failure(self) -> bool:
        return self.families_attempted > 0 and len(self.errors) == self.families_attempted

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "families_attempted": self.families_attempted,
            "created": self.created,
            "updated": self.updated,
            "errors": list(self.errors),
            "live_vs_fixture": dict(self.live_vs_fixture),
            "families": [asdict(row) for row in self.families],
        }

    def format_text(self) -> str:
        lines = [
            f"Weekly refresh (mode={self.mode})",
            f"  families_attempted: {self.families_attempted}",
            f"  created: {self.created}",
            f"  updated: {self.updated}",
            f"  errors: {len(self.errors)}",
            (
                "  live_vs_fixture: "
                f"live={self.live_vs_fixture.get('live', 0)} "
                f"fixture={self.live_vs_fixture.get('fixture', 0)}"
            ),
        ]
        if self.errors:
            lines.append("  failed: " + ", ".join(self.errors))
        for row in self.families:
            extra = f"  ({row.error})" if row.error else ""
            if row.status == "fallback" and row.notes:
                extra = extra or f"  ({row.notes[0][:120]})"
            lines.append(
                f"  {row.slug:22} {row.status:8} {row.mode_used:8} "
                f"created={row.created} updated={row.updated}{extra}"
            )
        return "\n".join(lines)

    def format_markdown(self) -> str:
        lines = [
            "## Weekly ingest refresh",
            "",
            f"- Mode: `{self.mode}`",
            f"- Families attempted: **{self.families_attempted}**",
            f"- Created: **{self.created}**",
            f"- Updated: **{self.updated}**",
            f"- Errors: **{len(self.errors)}**",
            (
                f"- live vs fixture: live={self.live_vs_fixture.get('live', 0)}, "
                f"fixture={self.live_vs_fixture.get('fixture', 0)}"
            ),
            "",
        ]
        if self.errors:
            lines.append("Failed families: " + ", ".join(f"`{slug}`" for slug in self.errors))
            lines.append("")
        lines.extend(
            [
                "| Family | Status | Mode | Created | Updated |",
                "| --- | --- | --- | ---: | ---: |",
            ]
        )
        for row in self.families:
            lines.append(
                f"| `{row.slug}` | {row.status} | {row.mode_used} | {row.created} | {row.updated} |"
            )
        lines.append("")
        return "\n".join(lines)


def _notes_indicate_fixture_fallback(notes: list[str]) -> bool:
    blob = " ".join(notes).lower()
    markers = (
        "live fetch failed",
        "live fetch returned 0",
        "falling back to fixtures",
        "using fixtures",
        "no live pages configured",
    )
    return any(marker in blob for marker in markers)


def _record_run(
    session: Session,
    source: FundSource,
    *,
    mode_used: str,
    status: str,
    created: int = 0,
    updated: int = 0,
    error: str | None = None,
    source_urls: list[str] | None = None,
) -> None:
    now = datetime.now(timezone.utc)
    run = IngestRun(
        fund_family=source.slug,
        mode=mode_used,
        status=status,
        started_at=now,
        finished_at=now,
        records_created=created,
        records_updated=updated,
        error_message=error,
        source_urls=source_urls or source.source_urls(),
    )
    record_ingest_run(session, run)


def _ingest_fetch(session: Session, source: FundSource, mode: str) -> tuple[int, int, FetchResult]:
    result = source.fetch(mode=mode)
    incoming = [normalized_to_in(record) for record in result.records]
    created, updated, _stored = upsert_records(session, incoming)
    return created, updated, result


def _try_live_then_fixture(session: Session, source: FundSource) -> FamilyRefreshResult:
    try:
        created, updated, result = _ingest_fetch(session, source, "live")
        if _notes_indicate_fixture_fallback(result.notes):
            _record_run(
                session,
                source,
                mode_used="fixture",
                status="success",
                created=created,
                updated=updated,
                error="; ".join(result.notes[:2]) or None,
                source_urls=result.source_urls,
            )
            return FamilyRefreshResult(
                slug=source.slug,
                status="fallback",
                mode_used="fixture",
                created=created,
                updated=updated,
                notes=result.notes,
                source_urls=result.source_urls,
            )
        _record_run(
            session,
            source,
            mode_used="live",
            status="success",
            created=created,
            updated=updated,
            source_urls=result.source_urls,
        )
        return FamilyRefreshResult(
            slug=source.slug,
            status="success",
            mode_used="live",
            created=created,
            updated=updated,
            notes=result.notes,
            source_urls=result.source_urls,
        )
    except Exception as live_exc:
        try:
            created, updated, result = _ingest_fetch(session, source, "fixture")
        except Exception as fixture_exc:
            _record_run(
                session,
                source,
                mode_used="live",
                status="error",
                error=f"live: {live_exc}; fixture: {fixture_exc}",
            )
            return FamilyRefreshResult(
                slug=source.slug,
                status="error",
                mode_used="live",
                created=0,
                updated=0,
                error=f"live: {live_exc}; fixture: {fixture_exc}",
            )
        note = f"Live fetch failed ({live_exc}). Fell back to fixture."
        _record_run(
            session,
            source,
            mode_used="fixture",
            status="success",
            created=created,
            updated=updated,
            error=note,
            source_urls=result.source_urls,
        )
        return FamilyRefreshResult(
            slug=source.slug,
            status="fallback",
            mode_used="fixture",
            created=created,
            updated=updated,
            notes=[note, *result.notes],
            source_urls=result.source_urls,
        )


def _try_fixture(session: Session, source: FundSource) -> FamilyRefreshResult:
    try:
        created, updated, result = _ingest_fetch(session, source, "fixture")
    except Exception as exc:
        _record_run(session, source, mode_used="fixture", status="error", error=str(exc))
        return FamilyRefreshResult(
            slug=source.slug,
            status="error",
            mode_used="fixture",
            created=0,
            updated=0,
            error=str(exc),
        )
    _record_run(
        session,
        source,
        mode_used="fixture",
        status="success",
        created=created,
        updated=updated,
        source_urls=result.source_urls,
    )
    return FamilyRefreshResult(
        slug=source.slug,
        status="success",
        mode_used="fixture",
        created=created,
        updated=updated,
        notes=result.notes,
        source_urls=result.source_urls,
    )


def refresh_families(
    session: Session,
    *,
    mode: str = "auto",
    slugs: list[str] | None = None,
) -> RefreshSummary:
    requested = (mode or "auto").strip().lower()
    if requested not in REFRESH_MODES:
        raise ValueError(f"refresh mode must be one of {REFRESH_MODES}, got {mode!r}")

    sources = resolve_families("all")
    if slugs:
        wanted = {slug.strip().lower() for slug in slugs}
        sources = [source for source in sources if source.slug in wanted]
        if not sources:
            raise ValueError(f"No implemented adapters matched: {sorted(wanted)}")

    rows: list[FamilyRefreshResult] = []
    for source in sources:
        if not source.implemented:
            continue
        if requested == "fixture":
            rows.append(_try_fixture(session, source))
        elif requested == "live":
            rows.append(_try_live_then_fixture(session, source))
        elif source.supports_live():
            rows.append(_try_live_then_fixture(session, source))
        else:
            result = _try_fixture(session, source)
            rows.append(result)

    errors = [row.slug for row in rows if row.status == "error"]
    live_count = sum(1 for row in rows if row.mode_used == "live")
    fixture_count = sum(1 for row in rows if row.mode_used == "fixture")
    return RefreshSummary(
        mode=requested,
        families_attempted=len(rows),
        created=sum(row.created for row in rows),
        updated=sum(row.updated for row in rows),
        errors=errors,
        live_vs_fixture={"live": live_count, "fixture": fixture_count},
        families=rows,
    )
