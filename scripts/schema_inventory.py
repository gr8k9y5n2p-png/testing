#!/usr/bin/env python3
"""Print SQLAlchemy table / index inventory. Local only — no Render, no copy.

SPIKE helper for docs/postgres-scale-spike.md. Does not invent amounts or
connect to production.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models import Base  # noqa: F401 — registers all tables


def main() -> None:
    print("table\tcolumn\ttype\tnullable\tpk")
    for table in Base.metadata.sorted_tables:
        for col in table.columns:
            print(
                f"{table.name}\t{col.name}\t{col.type!s}\t{col.nullable}\t{col.primary_key}"
            )
    print()
    print("index\ttable\tunique\tcolumns")
    for table in Base.metadata.sorted_tables:
        for index in table.indexes:
            cols = ",".join(c.name for c in index.columns)
            print(f"{index.name}\t{table.name}\t{index.unique}\t{cols}")
        for constraint in table.constraints:
            if getattr(constraint, "name", None) and constraint.name:
                cols = ",".join(c.name for c in constraint.columns)
                kind = type(constraint).__name__
                print(f"{constraint.name}\t{table.name}\t{kind}\t{cols}")


if __name__ == "__main__":
    main()
