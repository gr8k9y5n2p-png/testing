from __future__ import annotations

import re

from app.sources.american_funds import AmericanFundsSource
from app.sources.families import (
    BlackRockSource,
    FidelitySource,
    InvescoSource,
    JPMorganSource,
    TRowePriceSource,
    VanguardSource,
)
from app.sources.next_tier import (
    BnyMellonSource,
    DimensionalSource,
    MorganStanleySource,
    NorthernTrustSource,
)
from app.sources.fifth_tier import HarborSource, VoyaSource
from app.sources.fourth_tier import (
    ArtisanSource,
    FirstEagleSource,
    HartfordSource,
    JohnHancockSource,
    MacquarieSource,
)
from app.sources.third_tier import AmericanCenturySource, JanusHendersonSource, MfsSource
from app.sources.sixth_tier import AqrSource, AlgerSource, SeiSource


def _funds_and_tickers(source) -> tuple[set[str], set[str]]:
    result = source.fetch(mode="fixture")
    tickers = {
        (row.ticker or "").upper()
        for row in result.records
        if row.ticker and row.ticker not in {"—", "-", "–"}
    }
    funds = {(row.ticker or "").upper() or row.fund_name for row in result.records}
    assert not any(ticker.startswith("ZZ") for ticker in tickers if source.slug != "state_street")
    return funds, tickers


def test_full_book_ishares_fidelity_trp() -> None:
    ishares_funds, ishares_tickers = _funds_and_tickers(BlackRockSource())
    assert "BDVL" in ishares_tickers
    assert {"MDDVX", "LIRAX", "BSPAX", "BAGPX", "BMSAX", "BACAX", "MDGCX"} <= ishares_tickers
    assert len(ishares_tickers) >= 40
    assert len(ishares_funds) >= 50
    assert not any(re.search(r"\bSMA\b", name, re.I) for name in ishares_funds)

    fidelity_funds, fidelity_tickers = _funds_and_tickers(FidelitySource())
    assert "FBGRX" in fidelity_tickers
    assert len(fidelity_tickers) >= 300

    trp_funds, trp_tickers = _funds_and_tickers(TRowePriceSource())
    assert "TRBCX" in trp_tickers
    assert len(trp_tickers) >= 200


def test_full_book_american_funds_invesco_dimensional() -> None:
    af_funds, af_tickers = _funds_and_tickers(AmericanFundsSource())
    assert {"AMCPX", "ABALX", "AGTHX"} <= af_tickers
    assert len(af_funds) >= 70

    inv_funds, _inv_tickers = _funds_and_tickers(InvescoSource())
    assert any("American Franchise" in name for name in inv_funds)
    assert len(inv_funds) >= 50
    assert not any(re.search(r"\bSMA\b", name, re.I) for name in inv_funds)

    dfa_funds, dfa_tickers = _funds_and_tickers(DimensionalSource())
    assert {"DISVX", "DFELX", "DFQTX"} <= dfa_tickers
    assert len(dfa_tickers) >= 130


def test_full_book_vanguard_ici_and_next_wave() -> None:
    vg_funds, vg_tickers = _funds_and_tickers(VanguardSource())
    assert {"VFIAX", "VTSAX", "VOO", "VFINX"} <= vg_tickers
    assert len(vg_tickers) >= 250

    bny_funds, bny_tickers = _funds_and_tickers(BnyMellonSource())
    assert "DGAGX" in bny_tickers
    assert len(bny_funds) >= 40
    assert any("Concentrated Growth ETF" in name for name in bny_funds)

    nt_funds, nt_tickers = _funds_and_tickers(NorthernTrustSource())
    assert {"NOSIX", "NOMIX", "NSGRX", "NMMEX"} <= nt_tickers
    assert {"NENGX", "NMIEX", "NOSGX"} <= nt_tickers
    assert len(nt_tickers) >= 20

    janus_funds, janus_tickers = _funds_and_tickers(JanusHendersonSource())
    assert "JDCAX" in janus_tickers
    assert len(janus_tickers) >= 140


def test_full_book_jpm_aci_sei_aqr_alger() -> None:
    jpm_funds, jpm_tickers = _funds_and_tickers(JPMorganSource())
    assert "SEEGX" in jpm_tickers
    assert {"OIEIX", "UBVAX", "BBEM", "JFLI", "VCAXX", "MJMXX", "VNYXX"} <= jpm_tickers
    assert len(jpm_funds) >= 35

    aci_funds, aci_tickers = _funds_and_tickers(AmericanCenturySource())
    assert "TWCGX" in aci_tickers
    assert len(aci_tickers) >= 300

    sei_funds, _sei_tickers = _funds_and_tickers(SeiSource())
    assert any("Large Cap Growth" in name for name in sei_funds)
    assert len(sei_funds) >= 40

    aqr_funds, aqr_tickers = _funds_and_tickers(AqrSource())
    assert "AQGIX" in aqr_tickers
    assert len(aqr_tickers) >= 50

    alger_funds, alger_tickers = _funds_and_tickers(AlgerSource())
    assert "CHUSX" in alger_tickers
    assert len(alger_tickers) >= 50


def test_full_book_harbor_voya_keep_heroes() -> None:
    harbor_funds, harbor_tickers = _funds_and_tickers(HarborSource())
    assert "HACAX" in harbor_tickers
    assert len(harbor_funds) >= 8

    voya_funds, voya_tickers = _funds_and_tickers(VoyaSource())
    assert "NLCAX" in voya_tickers
    assert len(voya_funds) >= 15


def test_full_book_jh_hartford_macquarie_msim() -> None:
    jh_funds, jh_tickers = _funds_and_tickers(JohnHancockSource())
    assert "TAGRX" in jh_tickers
    assert len(jh_funds) >= 50
    assert not any("Closed-End" in name or "Premium Dividend" in name for name in jh_funds)

    hartford_funds, hartford_tickers = _funds_and_tickers(HartfordSource())
    assert "HFMCX" in hartford_tickers
    assert len(hartford_funds) >= 25
    assert any("Small Cap Growth" in name for name in hartford_funds)

    mac_funds, mac_tickers = _funds_and_tickers(MacquarieSource())
    assert {"WSTAX", "WASAX", "DEVLX"} <= mac_tickers
    assert len(mac_tickers) >= 20

    msim_funds, msim_tickers = _funds_and_tickers(MorganStanleySource())
    assert "CVLC" in msim_tickers
    assert len(msim_tickers) >= 15


def test_full_book_artisan_ici_and_first_eagle() -> None:
    artisan_funds, artisan_tickers = _funds_and_tickers(ArtisanSource())
    assert {"ARTKX", "ARTIX"} <= artisan_tickers
    assert len(artisan_tickers) >= 50

    fe_funds, fe_tickers = _funds_and_tickers(FirstEagleSource())
    assert {"SGENX", "FEVAX", "SGGDX", "FEGRX"} <= fe_tickers
    assert len(fe_tickers) >= 35
    assert len(fe_funds) >= 35
    assert not any("Credit Opportunities" in name for name in fe_funds)
    assert not any("Tactical Municipal" in name for name in fe_funds)

    mfs_funds, mfs_tickers = _funds_and_tickers(MfsSource())
    assert {"MIGHX", "MITTX", "MEIAX", "MFEGX", "MFRFX", "MGIAX"} <= mfs_tickers
    assert len(mfs_tickers) >= 10
    assert len(mfs_funds) >= 80
    assert any("Value Fund" in name for name in mfs_funds)
