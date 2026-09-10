"""GET /funds ticker Search must stay indexable and must not scan raw_payload."""

from __future__ import annotations

import time
import uuid
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import text

from app.crud import (
    _FUND_SEARCH_COLUMNS,
    _filter_stmt,
    looks_like_ticker_token,
    prefer_indexed_fund_match,
    search_funds,
)
from app.models import AmountUnit, DistributionEstimate, EstimateType, PublicationStage


def test_ticker_token_helpers() -> None:
    assert looks_like_ticker_token("AGTHX")
    assert looks_like_ticker_token("fbgrx")
    assert looks_like_ticker_token("AMCAP")
    assert looks_like_ticker_token("Balanced")
    assert not looks_like_ticker_token("ZZNOTAREALFUND")
    assert not looks_like_ticker_token("Growth Fund")

    assert prefer_indexed_fund_match("AGTHX")
    assert prefer_indexed_fund_match("agthx")
    assert prefer_indexed_fund_match("FBGRX")
    assert prefer_indexed_fund_match("AMCAP")
    assert prefer_indexed_fund_match("ZZZZZ")
    assert prefer_indexed_fund_match("VFIAX")
    assert not prefer_indexed_fund_match("Balanced")
    assert not prefer_indexed_fund_match("Growth")
    assert not prefer_indexed_fund_match("ZZNOTAREALFUND")


def _explain_fund_q(session, q: str, *, q_match: str) -> str:
    if session.get_bind().dialect.name != "sqlite":
        pytest.skip("EXPLAIN QUERY PLAN is SQLite-only")
    stmt = _filter_stmt(q=q, columns=_FUND_SEARCH_COLUMNS, q_match=q_match)
    compiled = stmt.compile(compile_kwargs={"literal_binds": True})
    rows = session.execute(text(f"EXPLAIN QUERY PLAN {compiled}")).all()
    return " ".join(str(part).lower() for row in rows for part in row)


def test_indexed_ticker_filter_uses_search_index(session) -> None:
    if session.get_bind().dialect.name != "sqlite":
        pytest.skip("EXPLAIN QUERY PLAN is SQLite-only")
    plan = _explain_fund_q(session, "AGTHX", q_match="indexed")
    assert "index" in plan
    assert "ix_dist_ticker" in plan or "ix_dist_fund_identifier" in plan or "ix_dist_fund_search" in plan
    # Leading-wildcard contains is what made production Search scan raw_payload.
    assert "like" not in plan or "%agthx%" not in plan


def _fat_payload() -> dict:
    return {"html": "x" * 8192, "note": "never invented — filler for disk-scan cost"}


def _seed_fat_book(session, *, n: int = 4000) -> None:
    blob = _fat_payload()
    rows = []
    for i in range(n):
        rows.append(
            {
                "id": str(uuid.uuid4()),
                "upsert_key": f"fat-{i}",
                "fund_family": "Fat Family",
                "fund_name": f"Fat Fund {i:04d}",
                "fund_identifier": f"FAT{i:05d}",
                "ticker": f"Z{i:04d}",
                "estimate_type": EstimateType.ordinary_income.value,
                "amount": Decimal("0.10"),
                "amount_unit": AmountUnit.per_share.value,
                "as_of": date(2025, 12, 15),
                "publication_stage": PublicationStage.paid.value,
                "raw_payload": blob,
            }
        )
    session.bulk_insert_mappings(DistributionEstimate, rows)
    session.add(
        DistributionEstimate(
            upsert_key="agthx-live",
            fund_family="American Funds",
            fund_name="The Growth Fund of America",
            fund_identifier="the-growth-fund-of-america",
            ticker="AGTHX",
            estimate_type=EstimateType.long_term_capital_gains.value,
            amount=Decimal("8.364"),
            amount_unit=AmountUnit.per_share.value,
            as_of=date(2026, 1, 22),
            publication_stage=PublicationStage.final.value,
            raw_payload=blob,
        )
    )
    session.add(
        DistributionEstimate(
            upsert_key="fbgrx-live",
            fund_family="Fidelity",
            fund_name="Fidelity Blue Chip Growth",
            fund_identifier="FBGRX",
            ticker="FBGRX",
            estimate_type=EstimateType.long_term_capital_gains.value,
            amount=Decimal("21.021"),
            amount_unit=AmountUnit.per_share.value,
            as_of=date(2026, 7, 31),
            publication_stage=PublicationStage.preliminary_estimate.value,
            ex_date=date(2026, 12, 11),
            payable_date=date(2026, 12, 15),
            raw_payload=blob,
        )
    )
    session.commit()


def test_funds_exact_ticker_fast_on_fat_book(session) -> None:
    _seed_fat_book(session)
    if session.get_bind().dialect.name == "sqlite":
        plan = _explain_fund_q(session, "AGTHX", q_match="indexed")
        assert "index" in plan
    else:
        plan = "postgresql"

    started = time.perf_counter()
    agthx, agthx_total = search_funds(session, q="AGTHX")
    fbgrx, fbgrx_total = search_funds(session, q="FBGRX")
    miss, miss_total = search_funds(session, q="ZZZZZ")
    elapsed = time.perf_counter() - started

    assert agthx_total == 1
    assert agthx[0].ticker == "AGTHX"
    assert agthx[0].fund_identifier == "the-growth-fund-of-america"
    assert agthx[0].has_estimate is False
    assert fbgrx_total == 1
    assert fbgrx[0].ticker == "FBGRX"
    assert fbgrx[0].has_estimate is True
    assert miss_total == 0
    assert miss == []
    # Three ticker lookups on a production-shaped fat book must stay well under 3s.
    assert elapsed < 1.0, f"exact ticker Search too slow: {elapsed:.3f}s plan={plan}"


def test_funds_http_ticker_and_name_paths(client: TestClient, session) -> None:
    _seed_fat_book(session, n=200)
    session.add(
        DistributionEstimate(
            upsert_key="balanced-1",
            fund_family="Vanguard",
            fund_name="Vanguard Balanced Index Fund",
            fund_identifier="VBIAX",
            ticker="VBIAX",
            estimate_type=EstimateType.ordinary_income.value,
            amount=Decimal("0.10"),
            amount_unit=AmountUnit.per_share.value,
            as_of=date(2024, 12, 17),
            publication_stage=PublicationStage.paid.value,
        )
    )
    session.commit()

    agthx = client.get("/funds", params={"q": "AGTHX"})
    assert agthx.status_code == 200
    assert agthx.json()["total"] == 1
    assert agthx.json()["items"][0]["ticker"] == "AGTHX"
    assert agthx.json()["items"][0]["has_estimate"] is False

    fbgrx = client.get("/funds", params={"q": "FBGRX"})
    assert fbgrx.status_code == 200
    assert fbgrx.json()["items"][0]["ticker"] == "FBGRX"
    assert fbgrx.json()["items"][0]["has_estimate"] is True
    assert fbgrx.json()["items"][0]["coverage_status"] == "estimate_announced"

    name = client.get("/funds", params={"q": "Balanced"})
    assert name.status_code == 200
    assert name.json()["total"] == 1
    assert name.json()["items"][0]["ticker"] == "VBIAX"
