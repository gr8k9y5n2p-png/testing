"""Boot-time fixture seed: full book only when empty; otherwise densify deltas.

Does not invent distribution amounts. Parses fixtures only for families that
are missing from the disk book or whose fixture files changed since last seed.
"""

from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app import db as app_db
from app.config import settings
from app.models import DistributionEstimate, FundNav, SeedFamilyState
from app.sources.base import FundSource
from app.sources.registry import list_sources

logger = logging.getLogger(__name__)


def fixture_fingerprint(slug: str, fixtures_dir: Path | None = None) -> str:
    """Cheap hash of fixture file names/sizes/mtimes. Does not parse HTML."""
    root = Path(fixtures_dir or settings.fixtures_dir) / slug
    if not root.is_dir():
        return ""
    parts: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        stat = path.stat()
        rel = path.relative_to(root).as_posix()
        parts.append(f"{rel}:{stat.st_size}:{int(stat.st_mtime)}")
    if not parts:
        return ""
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def family_estimate_count(session: Session, source: FundSource) -> int:
    return int(
        session.scalar(
            select(func.count())
            .select_from(DistributionEstimate)
            .where(
                or_(
                    DistributionEstimate.fund_family == source.display_name,
                    DistributionEstimate.fund_family == source.slug,
                )
            )
        )
        or 0
    )


def nav_row_count(session: Session) -> int:
    return int(session.scalar(select(func.count()).select_from(FundNav)) or 0)


def _state_map(session: Session) -> dict[str, SeedFamilyState]:
    rows = session.scalars(select(SeedFamilyState)).all()
    return {row.family_slug: row for row in rows}


def upsert_family_fingerprint(session: Session, slug: str, fingerprint: str) -> None:
    row = session.get(SeedFamilyState, slug)
    now = datetime.now(timezone.utc)
    if row is None:
        session.add(
            SeedFamilyState(
                family_slug=slug,
                fixture_fingerprint=fingerprint,
                updated_at=now,
            )
        )
        return
    row.fixture_fingerprint = fingerprint
    row.updated_at = now


def families_needing_seed(
    session: Session,
    *,
    sources: list[FundSource] | None = None,
    force_full: bool = False,
) -> tuple[list[FundSource], int]:
    """Return (families to ingest, warm families recorded without ingest).

    Warm disk without a stored fingerprint is treated as already seeded so a
    Manual Deploy does not rebuild ~11k rows. New or changed fixture files
    change the fingerprint and that family is ingested (densify deltas).
    Missing families (0 stored rows) are always ingested.
    """
    implemented = [s for s in (sources if sources is not None else list_sources()) if s.implemented]
    states = _state_map(session)
    needed: list[FundSource] = []
    recorded_warm = 0
    for source in implemented:
        fingerprint = fixture_fingerprint(source.slug)
        count = family_estimate_count(session, source)
        stored = states.get(source.slug)
        if force_full or count == 0:
            needed.append(source)
            continue
        if stored is None:
            upsert_family_fingerprint(session, source.slug, fingerprint)
            recorded_warm += 1
            continue
        if stored.fixture_fingerprint != fingerprint:
            needed.append(source)
    return needed, recorded_warm


def force_full_seed() -> bool:
    raw = os.getenv("SEED_FORCE_FULL")
    if raw is not None:
        return raw.strip().lower() in {"1", "true", "yes", "on"}
    return bool(settings.seed_force_full)


def run_boot_seed(seed_state: dict[str, Any], seed_lock: Any) -> None:
    """Ingest fixture deltas (or a full book when the disk is empty)."""
    from app.services.ingest import fetch_and_ingest

    if app_db.SessionLocal is None:
        return
    with seed_lock:
        if seed_state["status"] == "running":
            return
        seed_state["status"] = "running"
        seed_state["error"] = None
    created_total = 0
    mode = settings.fetch_mode or "fixture"
    try:
        try:
            from app.crud import scrub_qdi_percent_characterizations, scrub_stale_preliminary_estimates

            with app_db.SessionLocal() as session:
                removed = scrub_qdi_percent_characterizations(session)
                stale = scrub_stale_preliminary_estimates(session)
                session.commit()
            if removed:
                logger.info("Scrubbed %s QDI percent characterization rows", removed)
            if stale:
                logger.info("Scrubbed %s stale preliminary_estimate rows", stale)
        except Exception:
            logger.exception("QDI / stale-prelim scrub failed; continuing")

        force_full = force_full_seed()
        with app_db.SessionLocal() as session:
            needed, recorded_warm = families_needing_seed(session, force_full=force_full)
            session.commit()
        logger.info(
            "Boot seed ingest=%s skip_warm=%s force_full=%s",
            [source.slug for source in needed],
            recorded_warm,
            force_full,
        )

        for source in needed:
            try:
                with app_db.SessionLocal() as session:
                    result = fetch_and_ingest(session, source.slug, mode, review_outliers=False)
                    upsert_family_fingerprint(session, source.slug, fixture_fingerprint(source.slug))
                    session.commit()
                    created_total += int(result.created or 0)
            except Exception:
                logger.exception("Fixture seed failed for %s; continuing", source.slug)

        if needed:
            try:
                from app.crud import scrub_stale_preliminary_estimates as scrub_stale_after_seed

                with app_db.SessionLocal() as session:
                    stale = scrub_stale_after_seed(session)
                    session.commit()
                if stale:
                    logger.info("Post-seed scrubbed %s stale preliminary_estimate rows", stale)
            except Exception:
                logger.exception("Post-seed stale-prelim scrub failed; continuing")
            try:
                from app.services.nav import refresh_navs

                with app_db.SessionLocal() as session:
                    nav = refresh_navs(session, mode=mode if mode in {"fixture", "live", "auto"} else "fixture")
                    session.commit()
                logger.info(
                    "Fixture NAV seed created=%s updated=%s unknown=%s",
                    nav.created,
                    nav.updated,
                    nav.unknown,
                )
            except Exception:
                logger.exception("Fixture NAV seed failed; continuing with null NAV")
            try:
                from app.services.quality import flag_category_outliers

                with app_db.SessionLocal() as session:
                    flagged = flag_category_outliers(session)
                    session.commit()
                logger.info("Category-outlier review flagged=%s", flagged)
            except Exception:
                logger.exception("Category-outlier review failed; continuing")
        else:
            with app_db.SessionLocal() as session:
                if nav_row_count(session) == 0:
                    try:
                        from app.services.nav import refresh_navs

                        nav = refresh_navs(
                            session, mode=mode if mode in {"fixture", "live", "auto"} else "fixture"
                        )
                        session.commit()
                        logger.info(
                            "Fixture NAV seed (empty nav table) created=%s updated=%s unknown=%s",
                            nav.created,
                            nav.updated,
                            nav.unknown,
                        )
                    except Exception:
                        logger.exception("Fixture NAV seed failed; continuing with null NAV")
                else:
                    logger.info("Boot seed skipped NAV refresh; disk already has NAV rows")

        seed_state["created"] = created_total
        seed_state["status"] = "complete"
        logger.info("Fixture seed complete created=%s", created_total)
    except Exception as exc:
        seed_state["status"] = "error"
        seed_state["error"] = str(exc)
        logger.exception("Fixture seed aborted")
