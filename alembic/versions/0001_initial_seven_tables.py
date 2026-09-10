"""Initial seven tables matching current SQLAlchemy models.

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-10

Hard freeze: VARCHAR(36) text PKs (not native UUID), upsert_key unique,
fund_navs.ticker unique, fund_nav_history (ticker, nav_as_of) unique,
publication_stage + amount_unit preserved as strings, raw_payload kept,
JSON→JSONB on Postgres only. Do not invent amounts.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON

revision: str = "0001_initial"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PortableJSON = JSON().with_variant(JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "distribution_estimates",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("upsert_key", sa.String(length=512), nullable=False),
        sa.Column("fund_family", sa.String(length=128), nullable=False),
        sa.Column("fund_name", sa.String(length=512), nullable=False),
        sa.Column("fund_identifier", sa.String(length=256), nullable=False),
        sa.Column("ticker", sa.String(length=32), nullable=True),
        sa.Column("cusip", sa.String(length=16), nullable=True),
        sa.Column("share_class", sa.String(length=32), nullable=True),
        sa.Column("estimate_type", sa.String(length=64), nullable=False),
        sa.Column("amount", sa.Numeric(18, 6), nullable=True),
        sa.Column("amount_min", sa.Numeric(18, 6), nullable=True),
        sa.Column("amount_max", sa.Numeric(18, 6), nullable=True),
        sa.Column("amount_unit", sa.String(length=32), nullable=False),
        sa.Column("record_date", sa.Date(), nullable=True),
        sa.Column("ex_date", sa.Date(), nullable=True),
        sa.Column("payable_date", sa.Date(), nullable=True),
        sa.Column("as_of", sa.Date(), nullable=True),
        sa.Column("publication_stage", sa.String(length=64), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("raw_payload", PortableJSON, nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("needs_review", sa.Boolean(), nullable=False),
        sa.Column("review_reason", sa.String(length=64), nullable=True),
        sa.Column("data_quality_flags", PortableJSON, nullable=True),
        sa.UniqueConstraint("upsert_key", name="uq_distribution_upsert_key"),
    )
    op.create_index("ix_dist_family", "distribution_estimates", ["fund_family"])
    op.create_index("ix_dist_ticker", "distribution_estimates", ["ticker"])
    op.create_index("ix_dist_fund_name", "distribution_estimates", ["fund_name"])
    op.create_index("ix_dist_fund_identifier", "distribution_estimates", ["fund_identifier"])
    op.create_index("ix_dist_publication_stage", "distribution_estimates", ["publication_stage"])
    op.create_index("ix_dist_estimate_type", "distribution_estimates", ["estimate_type"])
    op.create_index("ix_dist_as_of", "distribution_estimates", ["as_of"])
    op.create_index("ix_dist_ex_date", "distribution_estimates", ["ex_date"])
    op.create_index(
        "ix_dist_fund_search",
        "distribution_estimates",
        ["ticker", "fund_identifier", "fund_name", "fund_family", "as_of", "ingested_at", "id"],
    )

    op.create_table(
        "coverage_gaps",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("ticker", sa.String(length=32), nullable=True),
        sa.Column("fund_name", sa.String(length=512), nullable=True),
        sa.Column("fund_family", sa.String(length=128), nullable=True),
        sa.Column("holding_dollars", sa.Numeric(18, 2), nullable=True),
        sa.Column("adapter_slug", sa.String(length=64), nullable=True),
        sa.Column("adapter_exists", sa.Boolean(), nullable=False),
        sa.Column("adapter_implemented", sa.Boolean(), nullable=False),
        sa.Column("suggested_next_step", sa.String(length=32), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_gap_created", "coverage_gaps", ["created_at"])

    op.create_table(
        "ticker_requests",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("ticker", sa.String(length=32), nullable=False),
        sa.Column("fund_name", sa.String(length=512), nullable=True),
        sa.Column("fund_family", sa.String(length=128), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("adapter_slug", sa.String(length=64), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ticker_request_status", "ticker_requests", ["status"])
    op.create_index("ix_ticker_request_ticker", "ticker_requests", ["ticker"])
    op.create_index("ix_ticker_request_created", "ticker_requests", ["created_at"])

    op.create_table(
        "fund_navs",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("ticker", sa.String(length=32), nullable=False),
        sa.Column("fund_identifier", sa.String(length=256), nullable=True),
        sa.Column("fund_family", sa.String(length=128), nullable=True),
        sa.Column("fund_name", sa.String(length=512), nullable=True),
        sa.Column("nav_per_share", sa.Numeric(18, 6), nullable=False),
        sa.Column("nav_as_of", sa.Date(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("ticker", name="uq_fund_nav_ticker"),
    )
    op.create_index("ix_nav_ticker", "fund_navs", ["ticker"])
    op.create_index("ix_nav_fund_identifier", "fund_navs", ["fund_identifier"])
    op.create_index("ix_nav_as_of", "fund_navs", ["nav_as_of"])

    op.create_table(
        "fund_nav_history",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("ticker", sa.String(length=32), nullable=False),
        sa.Column("nav_per_share", sa.Numeric(18, 6), nullable=False),
        sa.Column("nav_as_of", sa.Date(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("ticker", "nav_as_of", name="uq_fund_nav_history_ticker_as_of"),
    )
    op.create_index("ix_nav_hist_ticker_as_of", "fund_nav_history", ["ticker", "nav_as_of"])

    op.create_table(
        "seed_family_state",
        sa.Column("family_slug", sa.String(length=128), primary_key=True, nullable=False),
        sa.Column("fixture_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "ingest_runs",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("fund_family", sa.String(length=128), nullable=False),
        sa.Column("mode", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("records_created", sa.Integer(), nullable=False),
        sa.Column("records_updated", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("source_urls", PortableJSON, nullable=True),
    )
    op.create_index("ix_ingest_family_started", "ingest_runs", ["fund_family", "started_at"])


def downgrade() -> None:
    op.drop_index("ix_ingest_family_started", table_name="ingest_runs")
    op.drop_table("ingest_runs")
    op.drop_table("seed_family_state")
    op.drop_index("ix_nav_hist_ticker_as_of", table_name="fund_nav_history")
    op.drop_table("fund_nav_history")
    op.drop_index("ix_nav_as_of", table_name="fund_navs")
    op.drop_index("ix_nav_fund_identifier", table_name="fund_navs")
    op.drop_index("ix_nav_ticker", table_name="fund_navs")
    op.drop_table("fund_navs")
    op.drop_index("ix_ticker_request_created", table_name="ticker_requests")
    op.drop_index("ix_ticker_request_ticker", table_name="ticker_requests")
    op.drop_index("ix_ticker_request_status", table_name="ticker_requests")
    op.drop_table("ticker_requests")
    op.drop_index("ix_gap_created", table_name="coverage_gaps")
    op.drop_table("coverage_gaps")
    op.drop_index("ix_dist_fund_search", table_name="distribution_estimates")
    op.drop_index("ix_dist_ex_date", table_name="distribution_estimates")
    op.drop_index("ix_dist_as_of", table_name="distribution_estimates")
    op.drop_index("ix_dist_estimate_type", table_name="distribution_estimates")
    op.drop_index("ix_dist_publication_stage", table_name="distribution_estimates")
    op.drop_index("ix_dist_fund_identifier", table_name="distribution_estimates")
    op.drop_index("ix_dist_fund_name", table_name="distribution_estimates")
    op.drop_index("ix_dist_ticker", table_name="distribution_estimates")
    op.drop_index("ix_dist_family", table_name="distribution_estimates")
    op.drop_table("distribution_estimates")
