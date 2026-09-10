"""GET /distributions?sort=&order= — server-side Paid History sort.

Sorts the full filtered set before limit/offset. Never invents amounts.
Schema hard-freeze: no model / migration changes.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.crud import (
    _distribution_order_by,
    _filter_stmt,
    resolve_distribution_sort,
    search_distributions,
)


def _record(
    *,
    fund_family: str,
    fund_name: str,
    ticker: str,
    estimate_type: str,
    amount: str,
    as_of: str,
    publication_stage: str,
    ex_date: str | None = None,
    amount_unit: str = "per_share",
) -> dict:
    payload = {
        "fund_family": fund_family,
        "fund_name": fund_name,
        "ticker": ticker,
        "estimate_type": estimate_type,
        "amount": amount,
        "amount_unit": amount_unit,
        "as_of": as_of,
        "publication_stage": publication_stage,
    }
    if ex_date:
        payload["ex_date"] = ex_date
    return payload


def _seed_paid_history_sort(client: TestClient) -> None:
    """Stored flagship rows only. Amounts are test fixtures, not invented live data."""
    response = client.post(
        "/ingest/distributions",
        json={
            "records": [
                _record(
                    fund_family="Vanguard",
                    fund_name="Vanguard 500 Index Fund",
                    ticker="VFIAX",
                    estimate_type="long_term_capital_gains",
                    amount="1.10",
                    as_of="2025-12-16",
                    publication_stage="final",
                    ex_date="2025-12-16",
                ),
                _record(
                    fund_family="Vanguard",
                    fund_name="Vanguard 500 Index Fund",
                    ticker="VFIAX",
                    estimate_type="short_term_capital_gains",
                    amount="0.20",
                    as_of="2025-12-16",
                    publication_stage="final",
                    ex_date="2025-12-16",
                ),
                _record(
                    fund_family="Vanguard",
                    fund_name="Vanguard 500 Index Fund",
                    ticker="VFIAX",
                    estimate_type="long_term_capital_gains",
                    amount="0.90",
                    as_of="2024-12-17",
                    publication_stage="final",
                    ex_date="2024-12-17",
                ),
                _record(
                    fund_family="Vanguard",
                    fund_name="Vanguard Balanced Index Fund",
                    ticker="VBIAX",
                    estimate_type="ordinary_income",
                    amount="0.10",
                    as_of="2025-12-17",
                    publication_stage="final",
                    ex_date="2025-12-17",
                ),
                _record(
                    fund_family="Dodge & Cox",
                    fund_name="Dodge & Cox Income Fund",
                    ticker="DODIX",
                    estimate_type="ordinary_income",
                    amount="0.13",
                    as_of="2025-12-15",
                    publication_stage="final",
                    ex_date="2025-12-15",
                ),
                _record(
                    fund_family="American Funds",
                    fund_name="AMCAP Fund",
                    ticker="AMCPX",
                    estimate_type="long_term_capital_gains",
                    amount="2.15",
                    as_of="2025-12-12",
                    publication_stage="final",
                    ex_date="2025-12-12",
                ),
                _record(
                    fund_family="American Funds",
                    fund_name="AMCAP Fund",
                    ticker="AMCPX",
                    estimate_type="total_capital_gains",
                    amount="9.99",
                    as_of="2025-12-12",
                    publication_stage="final",
                    ex_date="2025-12-12",
                    amount_unit="percent_of_nav",
                ),
                _record(
                    fund_family="Vanguard",
                    fund_name="Vanguard 500 Index Fund",
                    ticker="VFIAX",
                    estimate_type="ordinary_income",
                    amount="0.00",
                    as_of="2025-12-16",
                    publication_stage="final",
                    ex_date="2025-12-16",
                ),
            ]
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["created"] == 8


def _year_params(**extra) -> dict:
    params = {
        "publication_stage": "final",
        "ex_date_from": "2025-01-01",
        "ex_date_to": "2025-12-31",
        "limit": 50,
    }
    params.update(extra)
    return params


def _amounts(items: list[dict]) -> list[Decimal]:
    return [Decimal(item["amount"]) for item in items]


def test_sort_amount_desc_year_window(client: TestClient) -> None:
    _seed_paid_history_sort(client)

    response = client.get("/distributions", params=_year_params(sort="amount", order="desc"))
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 7
    assert body["page"] == 1
    assert body["page_size"] == 50
    assert len(body["items"]) == 7
    assert all(item["ex_date"].startswith("2025-") for item in body["items"])
    assert all(item["publication_stage"] == "final" for item in body["items"])

    per_share = [item for item in body["items"] if item["amount_unit"] == "per_share"]
    pct_nav = [item for item in body["items"] if item["amount_unit"] == "percent_of_nav"]
    assert _amounts(per_share) == [
        Decimal("2.15"),
        Decimal("1.10"),
        Decimal("0.20"),
        Decimal("0.13"),
        Decimal("0.10"),
        Decimal("0.00"),
    ]
    assert _amounts(per_share) == sorted(_amounts(per_share), reverse=True)
    assert len(pct_nav) == 1
    assert Decimal(pct_nav[0]["amount"]) == Decimal("9.99")
    assert body["items"][-1]["amount_unit"] == "percent_of_nav"
    assert body["items"][0]["ticker"] == "AMCPX"
    assert all(item["raw_payload"] is None for item in body["items"])


def test_sort_amount_asc_year_window(client: TestClient) -> None:
    _seed_paid_history_sort(client)

    response = client.get("/distributions", params=_year_params(sort="amount", order="asc"))
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 7
    per_share = [item for item in body["items"] if item["amount_unit"] == "per_share"]
    assert _amounts(per_share) == [
        Decimal("0.00"),
        Decimal("0.10"),
        Decimal("0.13"),
        Decimal("0.20"),
        Decimal("1.10"),
        Decimal("2.15"),
    ]
    assert _amounts(per_share) == sorted(_amounts(per_share))
    assert body["items"][-1]["amount_unit"] == "percent_of_nav"


def test_omit_sort_preserves_default_order(client: TestClient) -> None:
    _seed_paid_history_sort(client)

    baseline = client.get("/distributions", params=_year_params())
    assert baseline.status_code == 200
    default_ids = [item["id"] for item in baseline.json()["items"]]
    assert default_ids
    assert baseline.json()["items"][0]["ticker"] == "VBIAX"

    omitted = client.get("/distributions", params=_year_params())
    assert [item["id"] for item in omitted.json()["items"]] == default_ids

    order_only = client.get("/distributions", params=_year_params(order="asc"))
    assert order_only.status_code == 200
    assert [item["id"] for item in order_only.json()["items"]] == default_ids

    amount_desc = client.get("/distributions", params=_year_params(sort="amount", order="desc"))
    amount_ids = [item["id"] for item in amount_desc.json()["items"]]
    assert amount_ids != default_ids
    assert amount_desc.json()["items"][0]["ticker"] == "AMCPX"
    assert amount_desc.json()["total"] == baseline.json()["total"] == 7


def test_sort_amount_paginates_full_filtered_set(client: TestClient) -> None:
    _seed_paid_history_sort(client)

    page1 = client.get(
        "/distributions",
        params=_year_params(sort="amount", order="desc", limit=2, offset=0),
    )
    page2 = client.get(
        "/distributions",
        params=_year_params(sort="amount", order="desc", limit=2, offset=2),
    )
    assert page1.status_code == page2.status_code == 200
    assert page1.json()["total"] == page2.json()["total"] == 7
    assert page1.json()["page"] == 1
    assert page2.json()["page"] == 2
    assert _amounts(page1.json()["items"]) == [Decimal("2.15"), Decimal("1.10")]
    assert _amounts(page2.json()["items"]) == [Decimal("0.20"), Decimal("0.13")]
    assert {item["id"] for item in page1.json()["items"]}.isdisjoint(
        {item["id"] for item in page2.json()["items"]}
    )


def test_sort_amount_combines_with_category_and_family(client: TestClient) -> None:
    _seed_paid_history_sort(client)

    blend = client.get(
        "/distributions",
        params=_year_params(sort="amount", order="desc", category="Large Blend"),
    )
    assert blend.status_code == 200
    body = blend.json()
    assert body["total"] == 3
    assert {item["ticker"] for item in body["items"]} == {"VFIAX"}
    assert all(item["category"] == "Large Blend" for item in body["items"])
    assert _amounts(body["items"]) == [Decimal("1.10"), Decimal("0.20"), Decimal("0.00")]

    vanguard = client.get(
        "/distributions",
        params=_year_params(sort="amount", order="asc", fund_family="Vanguard"),
    )
    assert vanguard.status_code == 200
    family = vanguard.json()
    assert family["total"] == 4
    assert {item["ticker"] for item in family["items"]} == {"VFIAX", "VBIAX"}
    assert _amounts(family["items"]) == [
        Decimal("0.00"),
        Decimal("0.10"),
        Decimal("0.20"),
        Decimal("1.10"),
    ]

    dodge_blend = client.get(
        "/distributions",
        params=_year_params(sort="amount", order="desc", category="Large Blend", fund_family="Dodge"),
    )
    assert dodge_blend.json()["total"] == 0
    assert dodge_blend.json()["items"] == []


def test_sort_aliases_and_optional_fields(client: TestClient) -> None:
    _seed_paid_history_sort(client)

    primary = client.get("/distributions", params=_year_params(sort="amount", order="desc"))
    alias = client.get("/distributions", params=_year_params(sort_by="amount", sort_dir="desc"))
    assert [item["id"] for item in primary.json()["items"]] == [
        item["id"] for item in alias.json()["items"]
    ]

    by_ticker = client.get("/distributions", params=_year_params(sort="ticker", order="asc"))
    assert by_ticker.status_code == 200
    tickers = [item["ticker"] for item in by_ticker.json()["items"]]
    assert tickers == sorted(tickers)

    by_ex = client.get("/distributions", params=_year_params(sort="ex_date", order="desc"))
    dates = [item["ex_date"] for item in by_ex.json()["items"]]
    assert dates == sorted(dates, reverse=True)


def test_sort_invalid_values_are_422(client: TestClient) -> None:
    _seed_paid_history_sort(client)

    bad_sort = client.get("/distributions", params=_year_params(sort="nav", order="desc"))
    assert bad_sort.status_code == 422
    bad_order = client.get("/distributions", params=_year_params(sort="amount", order="up"))
    assert bad_order.status_code == 422


def test_sort_in_openapi(client: TestClient) -> None:
    spec = client.get("/openapi.json").json()
    params = spec["paths"]["/distributions"]["get"]["parameters"]
    by_name = {item["name"]: item for item in params}
    assert "sort" in by_name
    assert "order" in by_name
    assert "sort_by" in by_name
    assert "sort_dir" in by_name
    sort_desc = by_name["sort"]["description"]
    assert "amount" in sort_desc
    assert "ex_date" in sort_desc
    assert "per_share" in sort_desc
    sort_schema = by_name["sort"]["schema"]
    sort_enum = sort_schema.get("enum") or next(
        option["enum"] for option in sort_schema.get("anyOf", []) if "enum" in option
    )
    assert set(sort_enum) == {"amount", "ex_date", "ticker", "fund_name", "as_of"}
    order_schema = by_name["order"]["schema"]
    order_enum = order_schema.get("enum") or next(
        option["enum"] for option in order_schema.get("anyOf", []) if "enum" in option
    )
    assert set(order_enum) == {"asc", "desc"}
    order_desc = by_name["order"]["description"]
    assert "omitted" in order_desc


def test_sort_order_by_is_column_sql_not_raw_payload(session) -> None:
    clauses = _distribution_order_by("amount", "desc")
    blob = " ".join(
        str(clause.compile(compile_kwargs={"literal_binds": True})).lower() for clause in clauses
    )
    assert "raw_payload" not in blob
    assert "per_share" in blob
    assert "amount" in blob

    filtered = _filter_stmt(
        publication_stage="final",
        ex_date_from=date(2025, 1, 1),
        ex_date_to=date(2025, 12, 31),
    ).order_by(*clauses)
    compiled = filtered.compile(compile_kwargs={"literal_binds": True})
    sql = str(compiled).lower()
    assert "raw_payload" not in sql.split("order by")[-1]
    assert "order by" in sql

    plan = session.execute(text(f"EXPLAIN QUERY PLAN {compiled}")).all()
    plan_blob = " ".join(str(part).lower() for row in plan for part in row)
    assert "index" in plan_blob
    assert "ix_dist_ex_date" in plan_blob or "ix_dist_publication_stage" in plan_blob


@pytest.mark.parametrize(
    ("sort", "sort_by", "order", "sort_dir", "expected"),
    [
        (None, None, None, None, (None, None)),
        (None, None, "desc", None, (None, None)),
        ("amount", None, None, None, ("amount", "desc")),
        (None, "amount", None, "asc", ("amount", "asc")),
        ("ex_date", None, "asc", "desc", ("ex_date", "asc")),
        ("ticker", None, None, None, ("ticker", "asc")),
    ],
)
def test_resolve_distribution_sort_aliases(sort, sort_by, order, sort_dir, expected) -> None:
    assert resolve_distribution_sort(
        sort=sort, sort_by=sort_by, order=order, sort_dir=sort_dir
    ) == expected


def test_resolve_distribution_sort_rejects_unknown() -> None:
    with pytest.raises(ValueError, match="sort must be one of"):
        resolve_distribution_sort(sort="nav")
    with pytest.raises(ValueError, match="order must be"):
        resolve_distribution_sort(sort="amount", order="up")


def test_search_distributions_sort_amount_nulls_last(session) -> None:
    from app.models import AmountUnit, DistributionEstimate, PublicationStage

    rows = [
        DistributionEstimate(
            upsert_key="sort-high",
            fund_family="Vanguard",
            fund_name="High",
            fund_identifier="HIGHX",
            ticker="HIGHX",
            estimate_type="long_term_capital_gains",
            amount=Decimal("3.00"),
            amount_unit=AmountUnit.per_share.value,
            as_of=date(2025, 12, 1),
            ex_date=date(2025, 12, 1),
            publication_stage=PublicationStage.final.value,
        ),
        DistributionEstimate(
            upsert_key="sort-null",
            fund_family="Vanguard",
            fund_name="NullAmt",
            fund_identifier="NULLX",
            ticker="NULLX",
            estimate_type="long_term_capital_gains",
            amount=None,
            amount_unit=AmountUnit.per_share.value,
            as_of=date(2025, 12, 1),
            ex_date=date(2025, 12, 1),
            publication_stage=PublicationStage.final.value,
        ),
        DistributionEstimate(
            upsert_key="sort-zero",
            fund_family="Vanguard",
            fund_name="Zero",
            fund_identifier="ZEROX",
            ticker="ZEROX",
            estimate_type="ordinary_income",
            amount=Decimal("0"),
            amount_unit=AmountUnit.per_share.value,
            as_of=date(2025, 12, 1),
            ex_date=date(2025, 12, 1),
            publication_stage=PublicationStage.final.value,
        ),
    ]
    session.add_all(rows)
    session.commit()

    desc_rows, total = search_distributions(
        session, sort="amount", order="desc", page_size=50
    )
    assert total == 3
    assert [row.ticker for row in desc_rows] == ["HIGHX", "ZEROX", "NULLX"]
    assert desc_rows[-1].amount is None
    assert desc_rows[1].amount == Decimal("0")

    asc_rows, _ = search_distributions(session, sort="amount", order="asc", page_size=50)
    assert [row.ticker for row in asc_rows] == ["ZEROX", "HIGHX", "NULLX"]
