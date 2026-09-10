#!/usr/bin/env python3
"""Copy a SQLite snapshot into Postgres. Never invents fund amounts.

Usage (from repo root, after `alembic upgrade head` on dest):

  python scripts/copy_sqlite_to_postgres.py \\
    --source sqlite:////path/to/distributions.db \\
    --dest postgresql+psycopg://user:pass@host:5432/distributions

Copy a frozen /var/data snapshot (Eric SSH / disk file), not live writes.
Compares stored amounts, publication_stage, and amount_unit. Null stays null.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import rewrite_database_url
from app.db import make_engine
from app.services.copy_db import CopyVerifyError, copy_all, verify_copy


def _engine(url: str):
    return make_engine(rewrite_database_url(url))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="SQLAlchemy URL of the SQLite snapshot")
    parser.add_argument("--dest", required=True, help="SQLAlchemy URL of Postgres (or rewritten)")
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument(
        "--truncate-dest",
        action="store_true",
        help="Delete dest rows before copy. Refused by default if dest is nonempty.",
    )
    args = parser.parse_args(argv)

    source_url = rewrite_database_url(args.source)
    dest_url = rewrite_database_url(args.dest)
    if not source_url.startswith("sqlite"):
        print("error: --source must be a sqlite URL (frozen snapshot)", file=sys.stderr)
        return 2

    src = _engine(source_url)
    dest = _engine(dest_url)
    try:
        copied = copy_all(
            src,
            dest,
            batch_size=args.batch_size,
            truncate_dest=args.truncate_dest,
        )
        report = verify_copy(src, dest)
    except CopyVerifyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        src.dispose()
        dest.dispose()

    print(json.dumps({"copied": copied, "verify": report}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
