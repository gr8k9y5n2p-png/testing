from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.config import settings
from app.db import configure_engine, get_engine, init_db
from app import db as app_db
from app.schemas import DistributionIn, IngestRequest
from app.services.ingest import fetch_and_ingest, ingest_records
from app.services.refresh import REFRESH_MODES, refresh_families
from app.services.ticker_requests import process_ticker_requests
from app.sources.registry import list_sources, resolve_slug


def _ensure_db() -> None:
    if settings.database_url.startswith("sqlite:///"):
        db_path = settings.database_url.replace("sqlite:///", "", 1)
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    configure_engine(settings.database_url)
    get_engine()
    init_db()


def cmd_seed(_args: argparse.Namespace) -> int:
    _ensure_db()
    assert app_db.SessionLocal is not None
    with app_db.SessionLocal() as session:
        result = fetch_and_ingest(session, "american_funds", "fixture")
        session.commit()
        feed_path = Path(settings.fixtures_dir) / "american_funds" / "partner_feed.json"
        payload = json.loads(feed_path.read_text(encoding="utf-8"))
        partner = IngestRequest(records=[DistributionIn.model_validate(r) for r in payload["records"]])
        partner_result = ingest_records(session, partner.records)
        session.commit()

        from app.crud import search_distributions

        rows, total = search_distributions(
            session, fund_family="American Funds", estimate_type="long_term_capital_gains", page_size=5
        )
        print(f"Fixture fetch: created={result.created} updated={result.updated} urls={result.source_urls}")
        print(f"Partner feed: created={partner_result.created} updated={partner_result.updated}")
        print(f"Search example: LTCG for American Funds, total={total}, showing {len(rows)}")
        for row in rows:
            print(
                f"  - {row.fund_name} {row.ticker or ''} {row.amount} {row.amount_unit} "
                f"ex={row.ex_date} as_of={row.as_of}"
            )
    return 0


def cmd_fetch(args: argparse.Namespace) -> int:
    _ensure_db()
    assert app_db.SessionLocal is not None
    with app_db.SessionLocal() as session:
        result = fetch_and_ingest(session, args.family, args.mode)
        session.commit()
        print(json.dumps(result.model_dump(mode="json"), indent=2, default=str)[:4000])
    return 0


def cmd_families(_args: argparse.Namespace) -> int:
    for source in list_sources():
        flag = source.coverage_tier
        rank = source.aum_rank if source.aum_rank is not None else "-"
        print(f"{rank!s:>2} {source.slug:20} {flag:12} {source.display_name}")
    return 0


def cmd_refresh(args: argparse.Namespace) -> int:
    _ensure_db()
    assert app_db.SessionLocal is not None
    mode = (args.mode or settings.refresh_mode or "auto").strip().lower()
    if mode not in REFRESH_MODES:
        print(f"error: refresh mode must be one of {', '.join(REFRESH_MODES)}", file=sys.stderr)
        return 2
    slugs = None
    if args.family and args.family.strip().lower() not in {"all", "*"}:
        resolved = resolve_slug(args.family) or args.family.strip().lower()
        slugs = [resolved]
    with app_db.SessionLocal() as session:
        try:
            summary = refresh_families(session, mode=mode, slugs=slugs)
            session.commit()
        except ValueError as exc:
            session.rollback()
            print(f"error: {exc}", file=sys.stderr)
            return 2
        except Exception:
            session.rollback()
            raise
    text = summary.format_text()
    print(text)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(summary.to_dict(), indent=2, default=str) + "\n", encoding="utf-8")
        print(f"Wrote {path}")
    if args.markdown:
        md_path = Path(args.markdown)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(summary.format_markdown(), encoding="utf-8")
        print(f"Wrote {md_path}")
    return 1 if summary.hard_failure else 0


def cmd_ticker_requests(args: argparse.Namespace) -> int:
    """Pick up queued Website ticker requests. Fetch matched adapters. Never invent amounts."""
    _ensure_db()
    assert app_db.SessionLocal is not None
    mode = (args.mode or settings.refresh_mode or settings.fetch_mode or "auto").strip().lower()
    if mode not in REFRESH_MODES:
        print(f"error: mode must be one of {', '.join(REFRESH_MODES)}", file=sys.stderr)
        return 2
    if mode == "auto":
        # Adapters treat live as live-then-fixture. fetch_and_ingest has no auto path.
        mode = "live"
    with app_db.SessionLocal() as session:
        items = process_ticker_requests(session, mode=mode, limit=args.limit)
        session.commit()
    payload = {
        "processed": len(items),
        "items": [item.model_dump(mode="json") for item in items],
    }
    print(json.dumps(payload, indent=2, default=str))
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
        print(f"Wrote {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fund distribution estimates CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_seed = sub.add_parser("seed", help="Load American Funds fixtures and print a search example")
    p_seed.set_defaults(func=cmd_seed)

    p_fetch = sub.add_parser("fetch", help="Run a fetch+ingest job")
    p_fetch.add_argument("--family", default="american_funds")
    p_fetch.add_argument("--mode", default="fixture", choices=["fixture", "live"])
    p_fetch.set_defaults(func=cmd_fetch)

    p_fam = sub.add_parser("families", help="List registered fund-family adapters")
    p_fam.set_defaults(func=cmd_families)

    p_refresh = sub.add_parser(
        "refresh",
        help="Weekly all-family ingest: live where supported, fixture fallback",
    )
    p_refresh.add_argument(
        "--mode",
        default=None,
        choices=list(REFRESH_MODES),
        help="Override REFRESH_MODE (default auto: live then fixture)",
    )
    p_refresh.add_argument(
        "--family",
        default="all",
        help='Fund-family slug or "all" (default all implemented adapters)',
    )
    p_refresh.add_argument(
        "--output",
        default=None,
        help="Write JSON summary to this path",
    )
    p_refresh.add_argument(
        "--markdown",
        default=None,
        help="Write Markdown summary to this path (GitHub job summary)",
    )
    p_refresh.set_defaults(func=cmd_refresh)

    p_tr = sub.add_parser(
        "ticker-requests",
        help="Pick up queued Website ticker requests and fetch matched adapters",
    )
    p_tr.add_argument(
        "--mode",
        default=None,
        choices=list(REFRESH_MODES),
        help="Override FETCH/REFRESH mode (default auto: live then fixture)",
    )
    p_tr.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Max queued/search/matched rows to process (default 50)",
    )
    p_tr.add_argument(
        "--output",
        default=None,
        help="Write JSON pickup summary to this path",
    )
    p_tr.set_defaults(func=cmd_ticker_requests)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
