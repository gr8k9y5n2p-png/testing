from __future__ import annotations

import re

from app.sources.american_funds import AmericanFundsSource
from app.sources.families import (
    BlackRockSource,
    FidelitySource,
    InvescoSource,
    JPMorganSource,
    StateStreetSource,
    TRowePriceSource,
    VanguardSource,
)
from app.sources.next_tier import (
    AmundiSource,
    BnyMellonSource,
    ColumbiaThreadneedleSource,
    DimensionalSource,
    FranklinTempletonSource,
    MorganStanleySource,
    NorthernTrustSource,
    SchwabSource,
)
from app.sources.ark import ArkSource
from app.sources.eleventh_tier import AmgSource, GuidestoneSource
from app.sources.eighth_tier import BairdSource, BuffaloSource, GqgSource, HeartlandSource, LongleafSource
from app.sources.fifth_tier import (
    HarborSource,
    NylifeSource,
    OakmarkSource,
    TouchstoneSource,
    VictorySource,
    VoyaSource,
    RoyceSource,
)
from app.sources.ninth_tier import (
    AmericanBeaconSource,
    BaillieGiffordSource,
    BrandesSource,
    FamSource,
    HennessySource,
    KineticsSource,
    MeridianSource,
)
from app.sources.seventh_tier import DiamondHillSource, DriehausSource, MarsicoSource
from app.sources.tenth_tier import (
    BostonPartnersSource,
    LazardSource,
    LsvSource,
    MadisonSource,
    ManningNapierSource,
    RiverparkSource,
)
from app.sources.fourth_tier import (
    ArtisanSource,
    CalamosSource,
    FirstEagleSource,
    HartfordSource,
    JohnHancockSource,
    MacquarieSource,
    ThriventSource,
    WasatchSource,
)
from app.sources.third_tier import AmericanCenturySource, JanusHendersonSource, MfsSource
from app.sources.dws import DwsSource
from app.sources.catalyst import CatalystSource
from app.sources.sixth_tier import (
    AqrSource,
    AlgerSource,
    FirstTrustSource,
    HardingLoevnerSource,
    SeiSource,
    VaneckSource,
    WisdomtreeSource,
)


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
    assert {"IVV", "IWM", "EFA", "AGG", "ACWX", "IEMG", "IEFA", "ITOT", "TLT", "LQD", "HYG"} <= ishares_tickers
    assert len(ishares_tickers) >= 350
    assert len(ishares_funds) >= 350
    assert not any(re.search(r"\bSMA\b", name, re.I) for name in ishares_funds)

    fidelity_funds, fidelity_tickers = _funds_and_tickers(FidelitySource())
    assert "FBGRX" in fidelity_tickers
    assert "FCNTX" in fidelity_tickers
    assert len(fidelity_tickers) >= 300

    trp_funds, trp_tickers = _funds_and_tickers(TRowePriceSource())
    assert "TRBCX" in trp_tickers
    assert len(trp_tickers) >= 200


def test_full_book_american_funds_invesco_dimensional() -> None:
    af_funds, af_tickers = _funds_and_tickers(AmericanFundsSource())
    assert {"AMCPX", "ABALX", "AGTHX"} <= af_tickers
    # Dollar tables only. QDI "% qualified" characterization rows are not funds.
    assert len(af_funds) >= 45

    inv_funds, inv_tickers = _funds_and_tickers(InvescoSource())
    assert {"VAFAX", "ACSTX", "CHTRX", "OPOCX", "QQQ"} <= inv_tickers
    assert len(inv_funds) >= 50
    assert len(inv_tickers) >= 500
    assert not any(re.search(r"\bSMA\b", name, re.I) for name in inv_funds)

    dfa_funds, dfa_tickers = _funds_and_tickers(DimensionalSource())
    assert {"DISVX", "DFELX", "DFQTX"} <= dfa_tickers
    assert len(dfa_tickers) >= 130

    columbia_funds, columbia_tickers = _funds_and_tickers(ColumbiaThreadneedleSource())
    assert {"LBSAX", "CBLAX", "LEGAX", "ELGAX"} <= columbia_tickers
    assert len(columbia_tickers) >= 40


def test_full_book_vanguard_ici_and_next_wave() -> None:
    vg_funds, vg_tickers = _funds_and_tickers(VanguardSource())
    assert {"VFIAX", "VTSAX", "VOO", "VFINX", "VNQ", "BNDX"} <= vg_tickers
    assert len(vg_tickers) >= 250

    bny_funds, bny_tickers = _funds_and_tickers(BnyMellonSource())
    assert {"DGAGX", "DAGVX", "DREVX", "DREQX", "DNLDX", "PGROX", "DGLAX", "BKCG", "BKLC"} <= bny_tickers
    assert len(bny_funds) >= 40

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
    assert {"OIEIX", "UBVAX", "BBEM", "JFLI", "VCAXX", "MJMXX", "VNYXX", "JEPI", "JEPQ"} <= jpm_tickers
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
    assert {"HACAX", "HAVLX", "HSICX"} <= harbor_tickers
    assert len(harbor_funds) >= 8
    assert len(harbor_tickers) >= 9

    nylife_funds, nylife_tickers = _funds_and_tickers(NylifeSource())
    assert "MLAIX" in nylife_tickers
    assert len(nylife_tickers) >= 20

    touchstone_funds, touchstone_tickers = _funds_and_tickers(TouchstoneSource())
    assert {"TVLAX", "TSEC", "SIO", "TUSI", "TGVFX", "TEGAX", "TSNAX", "SAGWX"} <= touchstone_tickers
    assert len(touchstone_tickers) >= 14
    assert len(touchstone_funds) >= 15

    victory_funds, victory_tickers = _funds_and_tickers(VictorySource())
    assert {"MMEAX", "VETAX", "USSPX", "RSGRX"} <= victory_tickers
    assert len(victory_tickers) >= 80

    amg_funds, amg_tickers = _funds_and_tickers(AmgSource())
    assert "YACKX" in amg_tickers
    assert {"YAFIX", "MCGIX", "ARIDX"} <= amg_tickers
    assert len(amg_tickers) >= 60

    voya_funds, voya_tickers = _funds_and_tickers(VoyaSource())
    assert {"NLCAX", "IEDAX", "NAWGX", "VWYFX"} <= voya_tickers
    assert len(voya_funds) >= 15

    thrivent_funds, thrivent_tickers = _funds_and_tickers(ThriventSource())
    assert {"TMSIX", "THLCX", "TAAIX", "TWAIX", "TSCSX"} <= thrivent_tickers
    assert len(thrivent_funds) >= 12

    calamos_funds, calamos_tickers = _funds_and_tickers(CalamosSource())
    assert {"CVGRX", "CPLSX", "CAGCX", "CIGRX", "CVAAX"} <= calamos_tickers
    assert len(calamos_funds) >= 12

    wasatch_funds, wasatch_tickers = _funds_and_tickers(WasatchSource())
    assert {"WGROX", "WAAEX", "WAINX", "WAMVX", "FMIEX"} <= wasatch_tickers
    assert len(wasatch_funds) >= 12


def test_full_book_jh_hartford_macquarie_msim() -> None:
    jh_funds, jh_tickers = _funds_and_tickers(JohnHancockSource())
    assert {"TAGRX", "SVBAX", "JVLAX", "JHHY"} <= jh_tickers
    assert len(jh_funds) >= 50
    assert not any("Closed-End" in name or "Premium Dividend" in name for name in jh_funds)

    hartford_funds, hartford_tickers = _funds_and_tickers(HartfordSource())
    assert {"HFMCX", "ITHAX", "HQIAX", "HSLAX", "HGHAX", "HILAX", "HSMAX"} <= hartford_tickers
    assert len(hartford_funds) >= 25

    mac_funds, mac_tickers = _funds_and_tickers(MacquarieSource())
    assert {"WSTAX", "WASAX", "DEVLX"} <= mac_tickers
    assert len(mac_tickers) >= 20

    msim_funds, msim_tickers = _funds_and_tickers(MorganStanleySource())
    assert "CVLC" in msim_tickers
    assert len(msim_tickers) >= 15


def test_full_book_artisan_ici_and_first_eagle() -> None:
    ssga_funds, ssga_tickers = _funds_and_tickers(StateStreetSource())
    assert {"SPY", "SPYM", "ALLW", "DIA", "GLD"} <= ssga_tickers
    assert len(ssga_tickers) >= 160
    assert len(ssga_funds) >= 160

    schwab_funds, schwab_tickers = _funds_and_tickers(SchwabSource())
    assert {"SWTSX", "SWPPX", "SWANX", "SWSSX", "SWISX", "SWLGX", "SCHD", "SCHX", "SCHB", "SCHF", "SCHG"} <= schwab_tickers
    assert len(schwab_tickers) >= 70
    assert len(schwab_funds) >= 70

    ft_funds, ft_tickers = _funds_and_tickers(FranklinTempletonSource())
    assert {"FT", "FTF", "TEI", "SMDLX"} <= ft_tickers
    assert len(ft_tickers) >= 4

    artisan_funds, artisan_tickers = _funds_and_tickers(ArtisanSource())
    assert {"ARTKX", "ARTIX"} <= artisan_tickers
    assert len(artisan_tickers) >= 50

    fe_funds, fe_tickers = _funds_and_tickers(FirstEagleSource())
    assert {"SGENX", "FEVAX", "SGGDX", "FEGRX", "FEGE", "FEOE", "FEFAX"} <= fe_tickers
    assert len(fe_tickers) >= 35
    assert len(fe_funds) >= 35
    assert not any("Credit Opportunities" in name for name in fe_funds)
    assert not any("Tactical Municipal" in name for name in fe_funds)

    mfs_funds, mfs_tickers = _funds_and_tickers(MfsSource())
    assert {
        "MIGHX",
        "MITTX",
        "MEIAX",
        "MFEGX",
        "MFRFX",
        "MGIAX",
        "MAAGX",
        "MRGAX",
        "MIEJX",
        "MDIDX",
        "MWEFX",
        "MAGWX",
    } <= mfs_tickers
    assert len(mfs_tickers) >= 80
    assert len(mfs_funds) >= 80
    assert any("Value Fund" in name for name in mfs_funds)

    vaneck_funds, vaneck_tickers = _funds_and_tickers(VaneckSource())
    assert {"MWMIX", "INIVX", "GDX", "SMH", "CLOI"} <= vaneck_tickers
    assert len(vaneck_tickers) >= 50

    wt_funds, wt_tickers = _funds_and_tickers(WisdomtreeSource())
    assert {"GTR", "XC", "WTPI", "INDH", "DGRW", "DHS", "XSOE"} <= wt_tickers
    assert len(wt_tickers) >= 80

    first_trust_funds, first_trust_tickers = _funds_and_tickers(FirstTrustSource())
    assert {"BFAP", "BGLD", "IGLD", "BFJL", "FVD", "FTHI", "FPE"} <= first_trust_tickers
    assert len(first_trust_tickers) >= 140

    dws_funds, dws_tickers = _funds_and_tickers(DwsSource())
    assert {"DBEF", "HYLB", "HDEF", "ASHR", "PSWD", "DBAW", "HAUZ"} <= dws_tickers
    assert {"SDGAX", "SUWAX", "KTCAX", "SXPAX", "TOLLX", "BTIEX"} <= dws_tickers
    assert len(dws_tickers) >= 55
    assert "ASHS" not in dws_tickers
    assert "IND" not in dws_tickers
    assert not any("Municipal Income Trust" in name for name in dws_funds)
    assert not any("New Germany" in name for name in dws_funds)

    catalyst_funds, catalyst_tickers = _funds_and_tickers(CatalystSource())
    assert {
        "CPEAX",
        "CPEIX",
        "CLTAX",
        "CLTIX",
        "CAXIX",
        "CLPAX",
        "MLXAX",
        "CASIX",
        "SHIIX",
        "CWXIX",
        "MBXAX",
        "MBXIX",
        "EIXAX",
        "ATRAX",
        "CWEAX",
        "SHIEX",
        "CASAX",
        "CWXAX",
    } <= catalyst_tickers
    assert len(catalyst_tickers) == 54
    assert "CSIOX" not in catalyst_tickers
    assert "MBXFX" not in catalyst_tickers
    assert "CFRFX" not in catalyst_tickers


def test_full_book_ranks_41_plus_thin_family_harvest() -> None:
    beacon_funds, beacon_tickers = _funds_and_tickers(AmericanBeaconSource())
    assert {"AADEX", "SFMIX", "ABCIX", "AVFIX", "AHLIX"} <= beacon_tickers
    assert len(beacon_tickers) >= 100

    amg_funds, amg_tickers = _funds_and_tickers(AmgSource())
    assert {"YACKX", "YAFIX", "MCGIX", "ARIDX"} <= amg_tickers
    assert len(amg_tickers) >= 70

    lazard_funds, lazard_tickers = _funds_and_tickers(LazardSource())
    assert {"LZIEX", "LEAIX", "ICMPX", "LISIX", "LZUSX"} <= lazard_tickers
    assert len(lazard_tickers) >= 35

    harding_funds, harding_tickers = _funds_and_tickers(HardingLoevnerSource())
    assert {"HLMNX", "HLMGX", "HLEMX", "HLMIX", "HLMVX"} <= harding_tickers
    assert len(harding_tickers) >= 15

    baird_funds, baird_tickers = _funds_and_tickers(BairdSource())
    assert {"BSVIX", "BSVSX", "BMDIX", "CCGIX", "CCWIX"} <= baird_tickers
    assert len(baird_tickers) >= 8

    gqg_funds, gqg_tickers = _funds_and_tickers(GqgSource())
    assert {"GQEIX", "GQRIX", "GQFIX", "GQGIX", "GQGU"} <= gqg_tickers
    assert len(gqg_tickers) >= 15

    lsv_funds, lsv_tickers = _funds_and_tickers(LsvSource())
    assert {"LSVEX", "LVAEX", "LSVVX", "LSVMX"} <= lsv_tickers
    assert len(lsv_tickers) >= 14

    boston_funds, boston_tickers = _funds_and_tickers(BostonPartnersSource())
    assert {"BPAIX", "BPAVX", "BPSIX", "BPGIX"} <= boston_tickers
    assert len(boston_tickers) >= 12

    manning_funds, manning_tickers = _funds_and_tickers(ManningNapierSource())
    assert {"CEIIX", "MNDFX", "EXEYX", "MNHIX", "RAIIX", "MNHAX", "MNBIX", "MNMIX"} <= manning_tickers
    assert len(manning_tickers) >= 30
    assert len(manning_funds) >= 30

    buffalo_funds, buffalo_tickers = _funds_and_tickers(BuffaloSource())
    assert {"BUFEX", "BUFGX", "BUFTX", "BUFOX", "BUFBX", "BUFDX", "BUFIX", "BUFMX"} <= buffalo_tickers
    assert len(buffalo_tickers) >= 8
    assert len(buffalo_funds) >= 8


def test_full_book_wave20_thin_family_harvest() -> None:
    royce_funds, royce_tickers = _funds_and_tickers(RoyceSource())
    assert {"RYTRX", "RYOTX", "PENNX", "RIPIX"} <= royce_tickers
    assert len(royce_tickers) >= 30

    oakmark_funds, oakmark_tickers = _funds_and_tickers(OakmarkSource())
    assert {"OAKEX", "OAKMX", "OAYMX", "OANMX", "OAZMX"} <= oakmark_tickers
    assert len(oakmark_tickers) >= 30

    kinetics_funds, kinetics_tickers = _funds_and_tickers(KineticsSource())
    assert {"WWNPX", "WWWFX", "LSHEX", "KNPYX"} <= kinetics_tickers
    assert len(kinetics_tickers) >= 20

    meridian_funds, meridian_tickers = _funds_and_tickers(MeridianSource())
    assert {"MVALX", "MERDX", "MEIFX", "MSGGX"} <= meridian_tickers
    assert len(meridian_tickers) >= 15

    hennessy_funds, hennessy_tickers = _funds_and_tickers(HennessySource())
    assert {"HFCSX", "HFLGX", "HFCVX", "HFCIX"} <= hennessy_tickers
    assert len(hennessy_tickers) >= 20

    marsico_funds, marsico_tickers = _funds_and_tickers(MarsicoSource())
    assert {"MFOCX", "MGRIX", "MXXIX", "MIFOX"} <= marsico_tickers
    assert len(marsico_tickers) >= 10

    heartland_funds, heartland_tickers = _funds_and_tickers(HeartlandSource())
    assert {"HRTVX", "HRMDX", "HNTVX"} <= heartland_tickers
    assert len(heartland_tickers) >= 6

    riverpark_funds, riverpark_tickers = _funds_and_tickers(RiverparkSource())
    assert {"RPXIX", "RPXFX", "RWGIX", "RPNLX"} <= riverpark_tickers
    assert len(riverpark_tickers) >= 6

    longleaf_funds, longleaf_tickers = _funds_and_tickers(LongleafSource())
    assert {"LLPFX", "LLSCX", "LLGLX"} <= longleaf_tickers

    guidestone_funds, guidestone_tickers = _funds_and_tickers(GuidestoneSource())
    assert {"GGEZX", "GVEZX", "GSCZX", "GMZXX", "GVIZX", "GEIZX", "GFSZX", "GMGZX"} <= guidestone_tickers
    assert len(guidestone_tickers) >= 20
    assert len(guidestone_funds) >= 15

    diamond_funds, diamond_tickers = _funds_and_tickers(DiamondHillSource())
    assert {"DHLAX", "DHSCX", "DHPAX", "DHMAX", "DHTAX", "DIAMX", "DHIAX"} <= diamond_tickers
    assert len(diamond_tickers) >= 7
    assert len(diamond_funds) >= 7

    baillie_funds, baillie_tickers = _funds_and_tickers(BaillieGiffordSource())
    assert {"BSGPX", "BGAKX", "BGESX", "BGCSX", "BINSX"} <= baillie_tickers
    assert len(baillie_tickers) >= 5
    assert len(baillie_funds) >= 5

    brandes_funds, brandes_tickers = _funds_and_tickers(BrandesSource())
    assert {"BGVIX", "BIIEX", "BSCMX", "BISMX", "BEMIX"} <= brandes_tickers
    assert len(brandes_tickers) >= 5
    assert len(brandes_funds) >= 5

    fam_funds, fam_tickers = _funds_and_tickers(FamSource())
    assert {"FAMVX", "FAMWX", "FAMEX", "FAMFX", "FAMDX"} <= fam_tickers

    madison_funds, madison_tickers = _funds_and_tickers(MadisonSource())
    assert {"MAGG", "MSTI", "MNVAX"} <= madison_tickers

    driehaus_funds, driehaus_tickers = _funds_and_tickers(DriehausSource())
    assert {"DMCRX", "DMAGX", "DVSMX", "DNSMX", "DSMDX", "DIDEX", "DREGX"} <= driehaus_tickers
    assert len(driehaus_tickers) >= 11
    assert len(driehaus_funds) >= 8


def test_full_book_amundi_pioneer_included() -> None:
    funds, tickers = _funds_and_tickers(AmundiSource())
    assert {
        "PIODX",
        "PIGFX",
        "PEQIX",
        "PIOTX",
        "AOBLX",
        "PINDX",
        "CVFCX",
        "GLOSX",
        "PIIFX",
        "PCGRX",
        "PGOFX",
        "PIALX",
        "PYODX",
        "ACBAX",
        "PMAIX",
        "PGSVX",
        "PISVX",
        "PICYX",
        "STRYX",
    } <= tickers
    assert "XILSX" not in tickers
    assert len(tickers) >= 60
    assert len(funds) >= 60
    assert not any(re.search(r"\bInterval\b", name, re.I) for name in funds)


def test_full_book_ark_2021_final() -> None:
    funds, tickers = _funds_and_tickers(ArkSource())
    assert {"ARKK", "ARKQ", "ARKW", "ARKG"} <= tickers
    assert "ARKF" not in tickers
    assert len(tickers) >= 6
