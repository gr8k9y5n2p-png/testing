from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud import upsert_records
from app.models import AmountUnit, DistributionEstimate, EstimateType
from app.schemas import DistributionIn
from app.services.quality import REVIEW_CATEGORY_OUTLIER, flag_category_outliers


def _ltcg(*, ticker: str, fund_name: str, amount: str, as_of: str = "2025-12-15") -> DistributionIn:
    return DistributionIn(
        fund_family="Example",
        fund_name=fund_name,
        ticker=ticker,
        estimate_type=EstimateType.long_term_capital_gains,
        amount=Decimal(amount),
        amount_unit=AmountUnit.per_share,
        as_of=date.fromisoformat(as_of),
        ex_date=date.fromisoformat(as_of),
        publication_stage="final",
        source_url="https://example.invalid/quality",
    )


def test_category_outlier_flags_plus_minus_50_pct(session: Session) -> None:
    """Large Growth peers at $1; more than ±50% vs median needs review.

    Median $1.00 → high $1.50 / low $0.50. $1.40 stays clean; $1.51 and $0.49 flag.
    Extreme $10 / $0.10 still flag. Does not delete or invent amounts.
    """
    peers = [
        _ltcg(ticker="AGTHX", fund_name="The Growth Fund of America", amount="1.00"),
        _ltcg(ticker="AMCPX", fund_name="AMCAP Fund", amount="1.00"),
        _ltcg(ticker="FBGRX", fund_name="Fidelity Blue Chip Growth", amount="1.00"),
        _ltcg(ticker="FCNTX", fund_name="Fidelity Contrafund", amount="1.40"),
        _ltcg(ticker="ANEFX", fund_name="New Economy Fund", amount="1.51"),
        _ltcg(ticker="VUG", fund_name="Vanguard Growth ETF", amount="0.49"),
        _ltcg(ticker="VIGAX", fund_name="Vanguard Growth Index Admiral", amount="10.00"),
        _ltcg(ticker="VIGRX", fund_name="Vanguard Growth Index Investor", amount="0.10"),
    ]
    created, _updated, _stored = upsert_records(session, peers)
    session.commit()
    assert created == 8

    flagged = flag_category_outliers(session)
    session.commit()
    assert flagged == 4

    rows = {row.ticker: row for row in session.scalars(select(DistributionEstimate)).all()}
    assert rows["VIGAX"].needs_review is True
    assert rows["VIGAX"].review_reason == REVIEW_CATEGORY_OUTLIER
    assert REVIEW_CATEGORY_OUTLIER in (rows["VIGAX"].data_quality_flags or [])
    assert rows["VIGRX"].needs_review is True
    assert rows["ANEFX"].needs_review is True
    assert rows["VUG"].needs_review is True
    assert rows["AGTHX"].needs_review is False
    assert rows["AMCPX"].needs_review is False
    assert rows["FCNTX"].needs_review is False


def test_ingest_api_flags_category_outlier(client: TestClient) -> None:
    response = client.post(
        "/ingest/distributions",
        json={
            "records": [
                {
                    "fund_family": "Example",
                    "fund_name": name,
                    "ticker": ticker,
                    "estimate_type": "long_term_capital_gains",
                    "amount": amount,
                    "amount_unit": "per_share",
                    "as_of": "2025-12-15",
                    "ex_date": "2025-12-15",
                    "publication_stage": "final",
                    "source_url": "https://example.invalid/quality",
                }
                for ticker, name, amount in (
                    ("AGTHX", "The Growth Fund of America", "1.00"),
                    ("AMCPX", "AMCAP Fund", "1.00"),
                    ("FBGRX", "Fidelity Blue Chip Growth", "1.00"),
                    ("VIGAX", "Vanguard Growth Index Admiral", "12.00"),
                )
            ]
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["skipped_characterization"] == 0
    assert body["category_outliers_flagged"] == 1

    flagged = client.get("/distributions", params={"needs_review": True, "page_size": 20})
    assert flagged.status_code == 200
    items = flagged.json()["items"]
    assert flagged.json()["total"] == 1
    assert items[0]["ticker"] == "VIGAX"
    assert items[0]["needs_review"] is True
    assert items[0]["review_reason"] == "category_outlier"

    qdi = client.post(
        "/ingest/distributions",
        json={
            "records": [
                {
                    "fund_family": "American Funds",
                    "fund_name": "The Growth Fund of America",
                    "ticker": "AGTHX",
                    "estimate_type": "qualified_dividend",
                    "amount": "100",
                    "amount_unit": "percent",
                    "as_of": "2026-01-22",
                    "source_url": "https://example.invalid/qdi",
                }
            ]
        },
    )
    assert qdi.status_code == 200
    assert qdi.json()["created"] == 0
    assert qdi.json()["skipped_characterization"] == 1
    stored = client.get("/distributions", params={"estimate_type": "qualified_dividend"})
    assert stored.json()["total"] == 0

    dollar_qdi = client.post(
        "/ingest/distributions",
        json={
            "records": [
                {
                    "fund_family": "American Funds",
                    "fund_name": "The Growth Fund of America",
                    "ticker": "AGTHX",
                    "estimate_type": "qualified_dividend",
                    "amount": "0.1800",
                    "amount_unit": "per_share",
                    "as_of": "2025-12-15",
                    "ex_date": "2025-12-15",
                    "publication_stage": "final",
                    "source_url": "https://example.invalid/qdi-per-share",
                }
            ]
        },
    )
    assert dollar_qdi.status_code == 200
    assert dollar_qdi.json()["created"] == 1
    assert dollar_qdi.json()["skipped_characterization"] == 0
    kept = client.get("/distributions", params={"estimate_type": "qualified_dividend"})
    assert kept.json()["total"] == 1
    assert kept.json()["items"][0]["amount"] == "0.180000"
    assert kept.json()["items"][0]["amount_unit"] == "per_share"
