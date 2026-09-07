from __future__ import annotations

from app.sources.american_funds import AmericanFundsSource
from app.sources.families import BlackRockSource, FidelitySource, InvescoSource, TRowePriceSource
from app.sources.next_tier import DimensionalSource
from app.sources.fifth_tier import HarborSource, VoyaSource


def _funds_and_tickers(source) -> tuple[set[str], set[str]]:
    result = source.fetch(mode="fixture")
    tickers = {(row.ticker or "").upper() for row in result.records if row.ticker}
    funds = {(row.ticker or "").upper() or row.fund_name for row in result.records}
    assert not any(ticker.startswith("ZZ") for ticker in tickers if source.slug != "state_street")
    return funds, tickers


def test_full_book_ishares_fidelity_trp() -> None:
    ishares_funds, ishares_tickers = _funds_and_tickers(BlackRockSource())
    assert "BDVL" in ishares_tickers
    assert len(ishares_tickers) >= 40

    fidelity_funds, fidelity_tickers = _funds_and_tickers(FidelitySource())
    assert "FBGRX" in fidelity_tickers
    assert len(fidelity_tickers) >= 300

    trp_funds, trp_tickers = _funds_and_tickers(TRowePriceSource())
    assert "TRBCX" in trp_tickers
    assert len(trp_tickers) >= 200


def test_full_book_american_funds_invesco_dimensional() -> None:
    af_funds, af_tickers = _funds_and_tickers(AmericanFundsSource())
    assert any("AMCAP" in name.upper() for name in af_funds)
    assert len(af_funds) >= 70

    inv_funds, _inv_tickers = _funds_and_tickers(InvescoSource())
    assert any("American Franchise" in name for name in inv_funds)
    assert len(inv_funds) >= 40

    dfa_funds, dfa_tickers = _funds_and_tickers(DimensionalSource())
    assert "DISVX" in dfa_tickers
    assert len(dfa_tickers) >= 100


def test_full_book_harbor_voya_keep_heroes() -> None:
    harbor_funds, harbor_tickers = _funds_and_tickers(HarborSource())
    assert "HACAX" in harbor_tickers
    assert len(harbor_funds) >= 8

    voya_funds, voya_tickers = _funds_and_tickers(VoyaSource())
    assert "NLCAX" in voya_tickers
    assert len(voya_funds) >= 15
