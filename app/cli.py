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
from app.sources.registry import list_sources


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
        flag = "ready" if source.implemented else "stub"
        print(f"{source.slug:20} {flag:6} {source.display_name}")
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

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
