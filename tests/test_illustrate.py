from __future__ import annotations

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from app.models import AmountUnit, EstimateType
from app.schemas import TaxRates
from app.services.illustrate import (
    PAID_HISTORY_MAX_ITEMS,
    RATE_MAPPING,
    _holding_paid_history,
    _holding_upcoming,
    _illustrate_row,
    _response,
    filter_latest_as_of,
)


def _row(**overrides) -> SimpleNamespace:
    payload = dict(
        id="row-1",
        fund_family="American Funds",
        fund_name="AMCAP Fund",
        fund_identifier="amcap-fund",
        ticker=None,
        estimate_type=EstimateType.long_term_capital_gains.value,
        amount_unit=AmountUnit.percent_of_nav.value,
        amount=Decimal("4"),
        amount_min=Decimal("3"),
        amount_max=Decimal("5"),
        as_of=date(2025, 9, 19),
        record_date=date(2025, 12, 12),
        ex_date=date(2025, 12, 12),
        payable_date=date(2025, 12, 15),
        publication_stage="preliminary_estimate",
    )
    payload.update(overrides)
    return SimpleNamespace(**payload)


def test_rate_mapping_covers_every_estimate_type() -> None:
    for item in EstimateType:
        assert item.value in RATE_MAPPING


def test_percent_of_nav_math_and_range() -> None:
    rates = TaxRates(
        long_term_capital_gains=Decimal("0.20"),
        state=Decimal("0.05"),
    )
    component = _illustrate_row(
        _row(),
        holding=Decimal("1000000"),
        shares=None,
        rates=rates,
        combine=True,
    )
    assert component.distribution_dollars == Decimal("40000.00")
    assert component.distribution_dollars_min == Decimal("30000.00")
    assert component.distribution_dollars_max == Decimal("50000.00")
    assert component.applied_rate == Decimal("0.250000")
    assert component.estimated_tax == Decimal("10000.00")
    assert component.estimated_tax_min == Decimal("7500.00")
    assert component.estimated_tax_max == Decimal("12500.00")
    assert component.included_in_totals is True
    assert component.record_date == date(2025, 12, 12)
    assert component.ex_date == date(2025, 12, 12)
    assert component.payable_date == date(2025, 12, 15)


def test_per_share_math() -> None:
    rates = TaxRates(long_term_capital_gains=Decimal("0.20"), state=Decimal("0.05"))
    component = _illustrate_row(
        _row(
            amount_unit=AmountUnit.per_share.value,
            amount=Decimal("3.5365"),
            amount_min=None,
            amount_max=None,
        ),
        holding=Decimal("1000000"),
        shares=Decimal("12500"),
        rates=rates,
        combine=True,
    )
    assert component.distribution_dollars == Decimal("44206.25")
    assert component.estimated_tax == Decimal("11051.56")
    assert component.distribution_dollars_min is None


def test_rate_override_and_uncombined_state() -> None:
    rates = TaxRates(long_term_capital_gains=Decimal("0.15"), state=Decimal("0.093"))
    combined = _illustrate_row(
        _row(amount=Decimal("4"), amount_min=None, amount_max=None),
        holding=Decimal("1000000"),
        shares=None,
        rates=rates,
        combine=True,
    )
    assert combined.applied_rate == Decimal("0.243000")
    assert combined.estimated_tax == Decimal("9720.00")

    split = _illustrate_row(
        _row(amount=Decimal("4"), amount_min=None, amount_max=None),
        holding=Decimal("1000000"),
        shares=None,
        rates=rates,
        combine=False,
    )
    assert split.federal_tax == Decimal("6000.00")
    assert split.state_tax == Decimal("3720.00")
    assert split.estimated_tax == Decimal("9720.00")


def test_percent_unit_skipped() -> None:
    component = _illustrate_row(
        _row(
            estimate_type=EstimateType.qualified_dividend.value,
            amount_unit=AmountUnit.percent.value,
            amount=Decimal("41.94"),
            amount_min=None,
            amount_max=None,
        ),
        holding=Decimal("1000000"),
        shares=None,
        rates=TaxRates(),
        combine=True,
    )
    assert component.included_in_totals is False
    assert component.estimated_tax is None
    assert component.distribution_dollars is None
    assert component.skip_reason and "qualified dividend" in component.skip_reason.lower()


def test_filter_latest_as_of_per_fund() -> None:
    older = _row(id="a", as_of=date(2025, 9, 19), estimate_type="total_capital_gains")
    newer = _row(id="b", as_of=date(2026, 7, 8), amount=Decimal("3.5365"), amount_unit="per_share")
    other = _row(id="c", fund_identifier="other-fund", as_of=date(2025, 1, 1))
    kept = filter_latest_as_of([older, newer, other])
    ids = {item.id for item in kept}
    assert ids == {"b", "c"}


def _upcoming_illustration(**row_overrides):
    rates = TaxRates(long_term_capital_gains=Decimal("0.20"), state=Decimal("0.05"))
    component = _illustrate_row(
        _row(**row_overrides),
        holding=Decimal("10000"),
        shares=None,
        rates=rates,
        combine=True,
    )
    return _response(
        holding=Decimal("10000"),
        shares=None,
        nav_per_share=None,
        rates=rates,
        combine=True,
        components=[component],
        notes=[],
    )


def test_holding_upcoming_record_window_gate(monkeypatch) -> None:
    monkeypatch.setattr("app.services.illustrate._utc_today", lambda: date(2026, 9, 8))
    stage = "preliminary_estimate"

    past = _upcoming_illustration(
        record_date=date(2025, 12, 12),
        ex_date=date(2025, 12, 12),
        payable_date=date(2025, 12, 15),
    )
    assert _holding_upcoming(past, stage) is None

    on_record_day = _upcoming_illustration(
        record_date=date(2026, 9, 8),
        ex_date=date(2026, 9, 9),
        payable_date=date(2026, 9, 10),
    )
    assert _holding_upcoming(on_record_day, stage) is None

    future = _upcoming_illustration(
        record_date=date(2026, 12, 15),
        ex_date=date(2026, 12, 16),
        payable_date=date(2026, 12, 17),
    )
    upcoming = _holding_upcoming(future, stage)
    assert upcoming is not None
    assert upcoming.record_date == date(2026, 12, 15)
    assert upcoming.ex_date == date(2026, 12, 16)
    assert upcoming.payable_date == date(2026, 12, 17)

    record_past_payable_future = _upcoming_illustration(
        record_date=date(2025, 12, 12),
        ex_date=date(2026, 12, 16),
        payable_date=date(2026, 12, 17),
    )
    assert _holding_upcoming(record_past_payable_future, stage) is None

    ex_only_past = _upcoming_illustration(
        record_date=None,
        ex_date=date(2025, 12, 12),
        payable_date=date(2026, 12, 17),
    )
    assert _holding_upcoming(ex_only_past, stage) is None

    ex_only_future = _upcoming_illustration(
        record_date=None,
        ex_date=date(2026, 12, 16),
        payable_date=None,
    )
    assert _holding_upcoming(ex_only_future, stage) is not None

    dateless = _upcoming_illustration(record_date=None, ex_date=None, payable_date=None)
    assert _holding_upcoming(dateless, stage) is not None
    assert _holding_upcoming(dateless, "paid") is None

    paid_future = _upcoming_illustration(
        record_date=date(2026, 12, 15),
        ex_date=date(2026, 12, 16),
        payable_date=date(2026, 12, 17),
    )
    assert _holding_upcoming(paid_future, "paid") is None
    assert _holding_upcoming(paid_future, "final") is None


def _history(rows):
    return _holding_paid_history(
        list(rows),
        holding=Decimal("10000"),
        nav_per_share=None,
        shares=None,
        rates=TaxRates(long_term_capital_gains=Decimal("0.20"), state=Decimal("0.05")),
        combine=True,
    )


def test_holding_paid_history_inverse_of_upcoming_gate(monkeypatch) -> None:
    monkeypatch.setattr("app.services.illustrate._utc_today", lambda: date(2026, 9, 8))

    past = _row(
        id="past",
        publication_stage="preliminary_estimate",
        record_date=date(2025, 12, 12),
        ex_date=date(2025, 12, 12),
        payable_date=date(2025, 12, 15),
    )
    past_items = _history([past])
    assert len(past_items) == 1
    assert past_items[0].payable_date == date(2025, 12, 15)
    assert past_items[0].record_date == date(2025, 12, 12)
    assert past_items[0].ex_date == date(2025, 12, 12)
    assert past_items[0].publication_stage == "preliminary_estimate"
    assert past_items[0].distribution_dollars == Decimal("400.00")
    assert past_items[0].estimated_tax == Decimal("100.00")

    on_record_day = _row(
        id="onrec",
        publication_stage="updated_estimate",
        record_date=date(2026, 9, 8),
        ex_date=date(2026, 9, 9),
        payable_date=date(2026, 9, 10),
        as_of=date(2026, 8, 1),
    )
    on_items = _history([on_record_day])
    assert len(on_items) == 1
    assert on_items[0].publication_stage == "updated_estimate"

    future = _row(
        id="fut",
        publication_stage="preliminary_estimate",
        record_date=date(2026, 12, 15),
        ex_date=date(2026, 12, 16),
        payable_date=date(2026, 12, 17),
        as_of=date(2026, 9, 1),
    )
    assert _history([future]) == []

    dateless = _row(
        id="dl",
        publication_stage="preliminary_estimate",
        record_date=None,
        ex_date=None,
        payable_date=None,
    )
    assert _history([dateless]) == []

    paid_future = _row(
        id="paidf",
        publication_stage="paid",
        record_date=date(2026, 12, 15),
        ex_date=date(2026, 12, 16),
        payable_date=date(2026, 12, 17),
        as_of=date(2026, 9, 1),
    )
    paid_items = _history([paid_future])
    assert len(paid_items) == 1
    assert paid_items[0].publication_stage == "paid"
    assert paid_items[0].record_date == date(2026, 12, 15)

    final_dateless = _row(
        id="final0",
        publication_stage="final",
        record_date=None,
        ex_date=None,
        payable_date=None,
        as_of=date(2024, 12, 31),
    )
    final_items = _history([final_dateless])
    assert len(final_items) == 1
    assert final_items[0].as_of == date(2024, 12, 31)
    assert final_items[0].publication_stage == "final"


def test_holding_paid_history_groups_same_event_and_sorts_newest_first(monkeypatch) -> None:
    monkeypatch.setattr("app.services.illustrate._utc_today", lambda: date(2026, 9, 8))
    older = _row(
        id="old",
        publication_stage="paid",
        as_of=date(2024, 12, 17),
        record_date=date(2024, 12, 17),
        ex_date=date(2024, 12, 17),
        payable_date=date(2024, 12, 18),
        amount=Decimal("2"),
    )
    newer_lt = _row(
        id="new-lt",
        publication_stage="paid",
        as_of=date(2025, 12, 12),
        record_date=date(2025, 12, 12),
        ex_date=date(2025, 12, 12),
        payable_date=date(2025, 12, 15),
        amount=Decimal("4"),
    )
    newer_st = _row(
        id="new-st",
        publication_stage="paid",
        estimate_type="short_term_capital_gains",
        as_of=date(2025, 12, 12),
        record_date=date(2025, 12, 12),
        ex_date=date(2025, 12, 12),
        payable_date=date(2025, 12, 15),
        amount=Decimal("1"),
        amount_min=None,
        amount_max=None,
    )
    items = _history([older, newer_lt, newer_st])
    assert len(items) == 2
    assert items[0].payable_date == date(2025, 12, 15)
    assert items[0].distribution_dollars == Decimal("500.00")
    assert items[1].payable_date == date(2024, 12, 18)
    assert items[1].distribution_dollars == Decimal("200.00")


def test_holding_paid_history_collapses_same_event_window(monkeypatch) -> None:
    monkeypatch.setattr("app.services.illustrate._utc_today", lambda: date(2026, 9, 8))
    prelim = _row(
        id="prelim",
        publication_stage="preliminary_estimate",
        as_of=date(2025, 9, 19),
        record_date=date(2025, 12, 12),
        ex_date=date(2025, 12, 12),
        payable_date=date(2025, 12, 15),
        amount=Decimal("4"),
    )
    reprint = _row(
        id="reprint",
        publication_stage="final",
        as_of=date(2026, 1, 22),
        record_date=date(2025, 12, 12),
        ex_date=date(2025, 12, 12),
        payable_date=date(2025, 12, 15),
        amount=Decimal("3"),
        amount_min=None,
        amount_max=None,
    )
    product = _row(
        id="product",
        publication_stage="final",
        as_of=date(2025, 12, 12),
        record_date=date(2025, 12, 12),
        ex_date=date(2025, 12, 12),
        payable_date=date(2025, 12, 15),
        amount=Decimal("5"),
        amount_min=None,
        amount_max=None,
    )
    items = _history([prelim, reprint, product])
    assert len(items) == 1
    assert items[0].publication_stage == "final"
    assert items[0].distribution_dollars == Decimal("500.00")
    assert items[0].as_of == date(2025, 12, 12)


def test_holding_paid_history_caps_newest_first(monkeypatch) -> None:
    monkeypatch.setattr("app.services.illustrate._utc_today", lambda: date(2026, 9, 8))
    rows = [
        _row(
            id=f"y{year}",
            publication_stage="paid",
            as_of=date(year, 12, 15),
            record_date=date(year, 12, 15),
            ex_date=date(year, 12, 15),
            payable_date=date(year, 12, 16),
            amount=Decimal("1"),
            amount_min=None,
            amount_max=None,
        )
        for year in range(2010, 2010 + PAID_HISTORY_MAX_ITEMS + 3)
    ]
    items = _history(rows)
    assert len(items) == PAID_HISTORY_MAX_ITEMS
    assert items[0].payable_date == date(2010 + PAID_HISTORY_MAX_ITEMS + 2, 12, 16)
    assert items[-1].payable_date == date(2013, 12, 16)
