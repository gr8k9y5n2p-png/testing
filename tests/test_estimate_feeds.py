from __future__ import annotations

from app.services.coverage import coverage_snapshot
from app.services.refresh import refresh_families
from app.sources.families import PimcoSource
from app.sources.readiness import estimate_feed_status
from app.sources.registry import list_sources


def test_top40_have_live_estimate_feed() -> None:
    missing: list[str] = []
    for source in list_sources():
        if source.aum_rank is None or source.aum_rank > 40:
            continue
        if not source.supports_live():
            missing.append(f"{source.slug}: supports_live=False")
        if not source.estimate_feed_urls():
            missing.append(f"{source.slug}: no estimate_feed_urls")
    assert missing == []


def test_ranks_41_to_53_have_live_estimate_feed() -> None:
    missing: list[str] = []
    for source in list_sources():
        if source.aum_rank is None or source.aum_rank < 41 or source.aum_rank > 53:
            continue
        if not source.supports_live():
            missing.append(f"{source.slug}: supports_live=False")
        if not source.estimate_feed_urls():
            missing.append(f"{source.slug}: no estimate_feed_urls")
    assert missing == []


def test_ranks_56_to_62_have_live_estimate_feed() -> None:
    missing: list[str] = []
    for source in list_sources():
        if source.aum_rank is None or source.aum_rank < 56 or source.aum_rank > 62:
            continue
        if not source.supports_live():
            missing.append(f"{source.slug}: supports_live=False")
        if not source.estimate_feed_urls():
            missing.append(f"{source.slug}: no estimate_feed_urls")
    assert missing == []


def test_amundi_is_on_estimate_ladder() -> None:
    amundi = next(s for s in list_sources() if s.slug == "amundi")
    assert estimate_feed_status("amundi") == "prelim_updated"
    assert amundi.supports_live() is True
    urls = amundi.estimate_feed_urls()
    assert any("pioneerinvestments.com/resources/tax-center" in url for url in urls)
    assert any("amundi.com/usinvestors/Resources/Tax-Center" in url for url in urls)
    assert any("investor.vcm.com/tools-resources/tax-center" in url for url in urls)
    assert any("10152025-mutual-funds-2025-capital-gain-estimates.pdf" in url for url in urls)
    assert any("2025-final-ord-inc-cap-gain-distributions.pdf" in url for url in urls)
    assert any("Victory-Portfolios-IV-Mutual-Funds-2025-Final-Capital-Gains.pdf" in url for url in urls)


def test_seasonal_empty_estimate_hub_falls_back_without_error() -> None:
    class EmptyPimco(PimcoSource):
        def _http_get(self, url: str) -> str:
            return "<html><body><p>2026 estimates will be posted in October.</p></body></html>"

    result = EmptyPimco().fetch(mode="live")
    assert result.records, "empty seasonal hub must fall back to fixtures, not invent zeros"
    blob = " ".join(result.notes).lower()
    assert "0 parseable" in blob or "seasonal" in blob
    assert any("pimco.com" in url for url in result.source_urls)
    assert all(
        (row.ticker or "").startswith("ZZ") or row.amount is not None for row in result.records
    )


def test_estimate_hub_403_is_noop_success(session) -> None:
    def boom(self, url: str) -> str:
        raise RuntimeError("403 Forbidden")

    original = PimcoSource._http_get
    try:
        PimcoSource._http_get = boom  # type: ignore[method-assign]
        summary = refresh_families(session, mode="auto", slugs=["pimco"])
        session.commit()
    finally:
        PimcoSource._http_get = original  # type: ignore[method-assign]

    assert summary.hard_failure is False
    assert summary.errors == []
    row = summary.families[0]
    assert row.slug == "pimco"
    assert row.status in {"fallback", "success"}
    assert row.created > 0
    assert any("pimco.com" in url for url in row.source_urls)


def test_coverage_exposes_estimate_feed_readiness(session) -> None:
    snap = coverage_snapshot(session)
    by_slug = {row.slug: row for row in snap["families"]}
    fidelity = by_slug["fidelity"]
    assert fidelity.estimate_feed_ready is True
    assert fidelity.estimate_feed_status == "prelim_updated"
    assert any("FIIS_SP52_DPL6" in url for url in fidelity.estimate_feed_urls)
    assert fidelity.has_multi_year_history is True
    assert fidelity.history_years == [2021, 2022, 2023, 2024, 2025, 2026]
    assert "FBGRX" in fidelity.performance_tickers
    assert "FCNTX" in fidelity.performance_tickers

    amundi = by_slug["amundi"]
    assert amundi.estimate_feed_status == "prelim_updated"
    assert amundi.estimate_feed_ready is True
    assert amundi.history_years == [2023, 2024, 2025]
    assert "PIODX" in amundi.performance_tickers
    assert "PIGFX" in amundi.performance_tickers
    assert any("pioneerinvestments.com" in url for url in amundi.estimate_feed_urls)

    pimco = by_slug["pimco"]
    assert pimco.estimate_feed_ready is True
    assert pimco.estimate_feed_status == "deferred"
    assert pimco.estimate_feed_urls

    federated = by_slug["federated_hermes"]
    assert federated.estimate_feed_status == "prelim_updated"
    assert federated.history_years == [2025]

    vaneck = by_slug["vaneck"]
    assert vaneck.estimate_feed_ready is True
    assert vaneck.estimate_feed_status == "prelim_updated"
    assert vaneck.history_years == [2023, 2024, 2025]
    assert "MWMIX" in vaneck.performance_tickers
    assert "INIVX" in vaneck.performance_tickers

    first_eagle = by_slug["first_eagle"]
    assert first_eagle.estimate_feed_ready is True
    assert "FEGE" in first_eagle.performance_tickers
    assert "FEOE" in first_eagle.performance_tickers
    assert "FEFAX" in first_eagle.performance_tickers

    harbor = by_slug["harbor"]
    assert harbor.estimate_feed_ready is True
    assert "HACAX" in harbor.performance_tickers
    assert "HAVLX" in harbor.performance_tickers

    amg = by_slug["amg"]
    assert amg.estimate_feed_ready is True
    assert amg.history_years == [2025]
    assert "YACKX" in amg.performance_tickers

    beacon = by_slug["american_beacon"]
    assert beacon.estimate_feed_ready is True
    assert "AADEX" in beacon.performance_tickers

    lazard = by_slug["lazard"]
    assert lazard.estimate_feed_ready is True
    assert "LZIEX" in lazard.performance_tickers

    baird = by_slug["baird"]
    assert baird.estimate_feed_ready is True
    assert "BSVIX" in baird.performance_tickers

    gqg = by_slug["gqg"]
    assert gqg.estimate_feed_ready is True
    assert "GQEIX" in gqg.performance_tickers

    lsv = by_slug["lsv"]
    assert lsv.estimate_feed_ready is True
    assert "LSVEX" in lsv.performance_tickers

    hennessy = by_slug["hennessy"]
    assert hennessy.estimate_feed_ready is True
    assert "HFCSX" in hennessy.performance_tickers

    kinetics = by_slug["kinetics"]
    assert kinetics.estimate_feed_ready is True
    assert "WWNPX" in kinetics.performance_tickers

    meridian = by_slug["meridian"]
    assert meridian.estimate_feed_ready is True
    assert "MERDX" in meridian.performance_tickers

    marsico = by_slug["marsico"]
    assert marsico.estimate_feed_ready is True
    assert "MFOCX" in marsico.performance_tickers

    first_trust = by_slug["first_trust"]
    assert first_trust.estimate_feed_ready is True
    assert "BGLD" in first_trust.performance_tickers
    assert "FVD" in first_trust.performance_tickers

    wisdomtree = by_slug["wisdomtree"]
    assert wisdomtree.estimate_feed_ready is True
    assert wisdomtree.history_years == [2024, 2025]
    assert "XC" in wisdomtree.performance_tickers

    jensen = by_slug["jensen"]
    assert jensen.estimate_feed_ready is True
    assert jensen.history_years == [2024, 2025]
    assert "JENSX" in jensen.performance_tickers

    diamond = by_slug["diamond_hill"]
    assert diamond.estimate_feed_ready is True
    assert diamond.history_years == [2024, 2025]
    assert "DHLAX" in diamond.performance_tickers

    guidestone = by_slug["guidestone"]
    assert guidestone.estimate_feed_ready is True
    assert "GGEZX" in guidestone.performance_tickers

    baillie = by_slug["baillie_gifford"]
    assert baillie.estimate_feed_ready is True
    assert "BGAKX" in baillie.performance_tickers

    brandes = by_slug["brandes"]
    assert brandes.estimate_feed_ready is True
    assert "BGVIX" in brandes.performance_tickers

    fam = by_slug["fam"]
    assert fam.estimate_feed_ready is True
    assert "FAMVX" in fam.performance_tickers

    driehaus = by_slug["driehaus"]
    assert driehaus.estimate_feed_ready is True
    assert "DMCRX" in driehaus.performance_tickers

    first_trust = by_slug["first_trust"]
    assert first_trust.estimate_feed_ready is True
    assert first_trust.estimate_feed_status == "prelim_updated"
    assert any("ftportfolios.com" in url for url in first_trust.estimate_feed_urls)

    dws = by_slug["dws"]
    assert dws.estimate_feed_ready is True
    assert dws.estimate_feed_status == "prelim_updated"
    assert dws.history_years == [2025, 2026]
    assert "DBEF" in dws.performance_tickers
    assert any("dws.com/en-us/resources/tax-center" in url for url in dws.estimate_feed_urls)
    assert any("9a1f54ed-fcf9-4b50-9d74-ae2343ee5bef" in url for url in dws.estimate_feed_urls)
    assert any("xtrackers_etf_capital_gains.pdf" in url for url in dws.estimate_feed_urls)
    assert any("capital-gains-retail-final.pdf" in url for url in dws.estimate_feed_urls)
    assert any("2026-dws-mutual-funds-estimated-mid-year-capital-gains.pdf" in url for url in dws.estimate_feed_urls)
    assert any("2025-xtrackers-etfs-primary-layout.pdf" in url for url in dws.estimate_feed_urls)
    assert any("2025_xtrackers_etfs_secondary_layout.pdf" in url for url in dws.estimate_feed_urls)
    assert any("dividend-schedules-2026" in url for url in dws.estimate_feed_urls)
    assert any("products/mutual-funds" in url for url in dws.estimate_feed_urls)

    catalyst = by_slug["catalyst"]
    assert catalyst.estimate_feed_ready is True
    assert catalyst.estimate_feed_status == "paid_history_only"
    assert catalyst.history_years == [2025]
    assert "CPEAX" in catalyst.performance_tickers
    assert any("catalystmf.com/literature-and-forms" in url for url in catalyst.estimate_feed_urls)
    assert any("2025%20Capital%20Gains%20Distributions.pdf" in url for url in catalyst.estimate_feed_urls)
    assert any("catalyst-fund-data.js" in url for url in catalyst.estimate_feed_urls)
    assert any(url.rstrip("/") == "https://catalystmf.com" for url in catalyst.estimate_feed_urls)

    voya = by_slug["voya"]
    assert voya.estimate_feed_ready is True
    assert voya.history_years == [2024, 2025]
    assert "NLCAX" in voya.performance_tickers

    oakmark = by_slug["oakmark"]
    assert oakmark.estimate_feed_ready is True
    assert oakmark.history_years == [2024, 2025]

    tweedy = by_slug["tweedy"]
    assert tweedy.estimate_feed_ready is True
    assert tweedy.history_years == [2024, 2025]

    gabelli = by_slug["gabelli"]
    assert gabelli.estimate_feed_ready is True
    assert gabelli.history_years == [2024, 2025]

    royce = by_slug["royce"]
    assert royce.estimate_feed_ready is True
    assert royce.history_years == [2024, 2025]

    victory = by_slug["victory"]
    assert victory.estimate_feed_ready is True
    assert victory.history_years == [2024, 2025]
    assert "MMEAX" in victory.performance_tickers
    assert "VETAX" in victory.performance_tickers

    sei = by_slug["sei"]
    assert sei.estimate_feed_ready is True
    assert sei.history_years == [2024, 2025]

    brown = by_slug["brown_advisory"]
    assert brown.estimate_feed_ready is True
    assert brown.history_years == [2024, 2025]

    blair = by_slug["william_blair"]
    assert blair.estimate_feed_ready is True
    assert blair.history_years == [2024, 2025]

    aqr = by_slug["aqr"]
    assert aqr.estimate_feed_ready is True
    assert aqr.estimate_feed_status == "prelim_updated"
    assert aqr.history_years == [2024, 2025]
    assert "AQGIX" in aqr.performance_tickers

    causeway = by_slug["causeway"]
    assert causeway.estimate_feed_ready is True
    assert causeway.history_years == [2024, 2025]
    assert "CIVIX" in causeway.performance_tickers

    matthews = by_slug["matthews_asia"]
    assert matthews.estimate_feed_ready is True
    assert matthews.history_years == [2021, 2022, 2023, 2024, 2025]
    assert "MAPTX" in matthews.performance_tickers

    bridgeway = by_slug["bridgeway"]
    assert bridgeway.estimate_feed_ready is True
    assert bridgeway.history_years == [2024, 2025]


def test_ranks_63_to_80_have_live_estimate_feed() -> None:
    missing: list[str] = []
    for source in list_sources():
        if source.aum_rank is None or source.aum_rank < 63 or source.aum_rank > 80:
            continue
        if not source.supports_live():
            missing.append(f"{source.slug}: supports_live=False")
        if not source.estimate_feed_urls():
            missing.append(f"{source.slug}: no estimate_feed_urls")
    assert missing == []


def test_ranks_81_to_90_have_live_estimate_feed() -> None:
    missing: list[str] = []
    for source in list_sources():
        if source.aum_rank is None or source.aum_rank < 81 or source.aum_rank > 90:
            continue
        if not source.supports_live():
            missing.append(f"{source.slug}: supports_live=False")
        if not source.estimate_feed_urls():
            missing.append(f"{source.slug}: no estimate_feed_urls")
    assert missing == []


def test_ranks_91_to_110_have_live_estimate_feed() -> None:
    missing: list[str] = []
    for source in list_sources():
        if source.aum_rank is None or source.aum_rank < 91 or source.aum_rank > 110:
            continue
        if not source.supports_live():
            missing.append(f"{source.slug}: supports_live=False")
        if not source.estimate_feed_urls():
            missing.append(f"{source.slug}: no estimate_feed_urls")
    assert missing == []
