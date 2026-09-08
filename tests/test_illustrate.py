from __future__ import annotations

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from app.models import AmountUnit, EstimateType
from app.schemas import TaxRates
from app.services.illustrate import RATE_MAPPING, _illustrate_row, filter_latest_as_of


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
