from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Index, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db import Base


class EstimateType(str, enum.Enum):
    ordinary_income = "ordinary_income"
    short_term_capital_gains = "short_term_capital_gains"
    long_term_capital_gains = "long_term_capital_gains"
    total_capital_gains = "total_capital_gains"
    total = "total"
    qualified_dividend = "qualified_dividend"
    qualified_short_term_gains = "qualified_short_term_gains"
    special_dividend = "special_dividend"
    return_of_capital = "return_of_capital"
    other = "other"


class AmountUnit(str, enum.Enum):
    per_share = "per_share"
    percent_of_nav = "percent_of_nav"
    percent = "percent"


class PublicationStage(str, enum.Enum):
    preliminary_estimate = "preliminary_estimate"
    updated_estimate = "updated_estimate"
    final = "final"
    paid = "paid"


class DistributionEstimate(Base):
    __tablename__ = "distribution_estimates"
    __table_args__ = (
        UniqueConstraint("upsert_key", name="uq_distribution_upsert_key"),
        Index("ix_dist_family", "fund_family"),
        Index("ix_dist_ticker", "ticker"),
        Index("ix_dist_fund_name", "fund_name"),
        Index("ix_dist_estimate_type", "estimate_type"),
        Index("ix_dist_as_of", "as_of"),
        Index("ix_dist_ex_date", "ex_date"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    upsert_key: Mapped[str] = mapped_column(String(512), nullable=False)
    fund_family: Mapped[str] = mapped_column(String(128), nullable=False)
    fund_name: Mapped[str] = mapped_column(String(512), nullable=False)
    fund_identifier: Mapped[str] = mapped_column(String(256), nullable=False)
    ticker: Mapped[str | None] = mapped_column(String(32), nullable=True)
    cusip: Mapped[str | None] = mapped_column(String(16), nullable=True)
    share_class: Mapped[str | None] = mapped_column(String(32), nullable=True)
    estimate_type: Mapped[str] = mapped_column(String(64), nullable=False)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    amount_min: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    amount_max: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    amount_unit: Mapped[str] = mapped_column(String(32), nullable=False)
    record_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    ex_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    payable_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    as_of: Mapped[date | None] = mapped_column(Date, nullable=True)
    publication_stage: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    needs_review: Mapped[bool] = mapped_column(default=False, nullable=False)
    review_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    data_quality_flags: Mapped[list | None] = mapped_column(JSON, nullable=True)


class CoverageGap(Base):
    """Advisor-reported holding that the website could not match to an adapter."""

    __tablename__ = "coverage_gaps"
    __table_args__ = (Index("ix_gap_created", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ticker: Mapped[str | None] = mapped_column(String(32), nullable=True)
    fund_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    fund_family: Mapped[str | None] = mapped_column(String(128), nullable=True)
    holding_dollars: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    adapter_slug: Mapped[str | None] = mapped_column(String(64), nullable=True)
    adapter_exists: Mapped[bool] = mapped_column(default=False)
    adapter_implemented: Mapped[bool] = mapped_column(default=False)
    suggested_next_step: Mapped[str] = mapped_column(String(32), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class TickerRequest(Base):
    """Website-submitted ticker for issuer-source ingest (never invents amounts)."""

    __tablename__ = "ticker_requests"
    __table_args__ = (
        Index("ix_ticker_request_status", "status"),
        Index("ix_ticker_request_ticker", "ticker"),
        Index("ix_ticker_request_created", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ticker: Mapped[str] = mapped_column(String(32), nullable=False)
    fund_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    fund_family: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="website_ui")
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    adapter_slug: Mapped[str | None] = mapped_column(String(64), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class FundNav(Base):
    """Latest liquid close / mutual-fund NAV per listed ticker. Never invented."""

    __tablename__ = "fund_navs"
    __table_args__ = (
        UniqueConstraint("ticker", name="uq_fund_nav_ticker"),
        Index("ix_nav_ticker", "ticker"),
        Index("ix_nav_fund_identifier", "fund_identifier"),
        Index("ix_nav_as_of", "nav_as_of"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ticker: Mapped[str] = mapped_column(String(32), nullable=False)
    fund_identifier: Mapped[str | None] = mapped_column(String(256), nullable=True)
    fund_family: Mapped[str | None] = mapped_column(String(128), nullable=True)
    fund_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    nav_per_share: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    nav_as_of: Mapped[date] = mapped_column(Date, nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class FundNavHistory(Base):
    """Daily regular close / NAV print, joinable by ticker + date. Never invented."""

    __tablename__ = "fund_nav_history"
    __table_args__ = (
        UniqueConstraint("ticker", "nav_as_of", name="uq_fund_nav_history_ticker_as_of"),
        Index("ix_nav_hist_ticker_as_of", "ticker", "nav_as_of"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ticker: Mapped[str] = mapped_column(String(32), nullable=False)
    nav_per_share: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    nav_as_of: Mapped[date] = mapped_column(Date, nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class SeedFamilyState(Base):
    """Last fixture fingerprint applied per family. Used to skip full rebuilds."""

    __tablename__ = "seed_family_state"

    family_slug: Mapped[str] = mapped_column(String(128), primary_key=True)
    fixture_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class IngestRun(Base):
    __tablename__ = "ingest_runs"
    __table_args__ = (Index("ix_ingest_family_started", "fund_family", "started_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fund_family: Mapped[str] = mapped_column(String(128), nullable=False)
    mode: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    records_created: Mapped[int] = mapped_column(default=0)
    records_updated: Mapped[int] = mapped_column(default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_urls: Mapped[list | None] = mapped_column(JSON, nullable=True)
