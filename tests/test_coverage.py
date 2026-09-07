from __future__ import annotations

from fastapi.testclient import TestClient


def test_coverage_endpoint_lists_top_100(client: TestClient) -> None:
    response = client.get("/coverage")
    assert response.status_code == 200
    body = response.json()
    assert body["top_n"] == 100
    assert body["implemented_count"] == 100
    assert body["stub_count"] == 0
    assert body["implemented_pct"] == 100.0
    slugs = [row["slug"] for row in body["families"]]
    assert slugs == [
        "blackrock",
        "vanguard",
        "fidelity",
        "state_street",
        "jpmorgan",
        "goldman_sachs",
        "american_funds",
        "pimco",
        "invesco",
        "t_rowe_price",
        "ubs",
        "franklin_templeton",
        "bny_mellon",
        "nuveen",
        "northern_trust",
        "morgan_stanley",
        "schwab",
        "dimensional",
        "columbia_threadneedle",
        "amundi",
        "allspring",
        "janus_henderson",
        "american_century",
        "dodge_cox",
        "mfs",
        "lord_abbett",
        "ab",
        "federated_hermes",
        "virtus",
        "eaton_vance",
        "john_hancock",
        "principal",
        "thrivent",
        "hartford",
        "macquarie",
        "first_eagle",
        "gmo",
        "artisan",
        "calamos",
        "wasatch",
        "harbor",
        "nationwide",
        "voya",
        "oakmark",
        "tweedy",
        "gabelli",
        "royce",
        "nylife",
        "touchstone",
        "victory",
        "sei",
        "brown_advisory",
        "william_blair",
        "vaneck",
        "wisdomtree",
        "aqr",
        "causeway",
        "alger",
        "harding_loevner",
        "matthews_asia",
        "tcw",
        "bridgeway",
        "jensen",
        "diamond_hill",
        "champlain",
        "driehaus",
        "hotchkis",
        "marsico",
        "osterweis",
        "davis",
        "primecap",
        "ariel",
        "baird",
        "longleaf",
        "buffalo",
        "gqg",
        "third_avenue",
        "heartland",
        "fmi",
        "impax",
        "american_beacon",
        "baillie_gifford",
        "brandes",
        "mairs_power",
        "boston_trust",
        "grandeur_peak",
        "hennessy",
        "fam",
        "meridian",
        "kinetics",
        "lazard",
        "manning_napier",
        "westwood",
        "boston_partners",
        "homestead",
        "madison",
        "lsv",
        "lkcm",
        "oberweis",
        "riverpark",
    ]
    assert all(row["coverage_tier"] == "implemented" for row in body["families"])
    assert body["families"][0]["priority"] == 1
    assert body["families"][10]["aum_rank"] == 11
    assert body["families"][19]["slug"] == "amundi"
    assert body["families"][20]["aum_rank"] == 21
    assert body["families"][29]["slug"] == "eaton_vance"
    assert body["families"][30]["aum_rank"] == 31
    assert body["families"][39]["slug"] == "wasatch"
    assert body["families"][40]["aum_rank"] == 41
    assert body["families"][49]["slug"] == "victory"
    assert body["families"][50]["aum_rank"] == 51
    assert body["families"][59]["slug"] == "matthews_asia"
    assert body["families"][60]["aum_rank"] == 61
    assert body["families"][69]["slug"] == "davis"
    assert body["families"][70]["aum_rank"] == 71
    assert body["families"][79]["slug"] == "impax"
    assert body["families"][80]["aum_rank"] == 81
    assert body["families"][89]["slug"] == "kinetics"
    assert body["families"][90]["aum_rank"] == 91
    assert body["families"][99]["slug"] == "riverpark"


def test_coverage_gap_implemented_family(client: TestClient) -> None:
    response = client.post(
        "/coverage/gaps",
        json={"ticker": "FBGRX", "fund_family": "fidelity", "holding_dollars": 250000},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["adapter_exists"] is True
    assert body["adapter_implemented"] is True
    assert body["adapter_slug"] == "fidelity"
    assert body["suggested_next_step"] == "fetch_adapter"
    assert body["ticker"] == "FBGRX"
    assert float(body["holding_dollars"]) == 250000

    listed = client.get("/coverage/gaps")
    assert listed.status_code == 200
    assert any(item["id"] == body["id"] for item in listed.json())

    snap = client.get("/coverage")
    assert snap.json()["logged_gap_count"] >= 1


def test_coverage_gap_unknown_family_manual_ingest(client: TestClient) -> None:
    response = client.post(
        "/coverage/gaps",
        json={"fund_name": "Obscure Small-Cap Trust", "fund_family": "not-a-family"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["adapter_exists"] is False
    assert body["suggested_next_step"] == "manual_ingest"


def test_coverage_gap_alias_ishares(client: TestClient) -> None:
    response = client.post("/coverage/gaps", json={"ticker": "BDVL", "fund_family": "ishares"})
    assert response.status_code == 200
    assert response.json()["adapter_slug"] == "blackrock"


def test_coverage_gap_alias_pioneer_and_dfa(client: TestClient) -> None:
    pioneer = client.post("/coverage/gaps", json={"ticker": "PIODX", "fund_family": "pioneer"})
    assert pioneer.status_code == 200
    assert pioneer.json()["adapter_slug"] == "amundi"
    dfa = client.post("/coverage/gaps", json={"ticker": "DFQTX", "fund_family": "dfa"})
    assert dfa.status_code == 200
    assert dfa.json()["adapter_slug"] == "dimensional"


def test_coverage_gap_alias_third_tier(client: TestClient) -> None:
    wells = client.post("/coverage/gaps", json={"ticker": "WFMIX", "fund_family": "wells_fargo"})
    assert wells.status_code == 200
    assert wells.json()["adapter_slug"] == "allspring"
    janus = client.post("/coverage/gaps", json={"ticker": "JDCAX", "fund_family": "janus"})
    assert janus.status_code == 200
    assert janus.json()["adapter_slug"] == "janus_henderson"
    alliance = client.post("/coverage/gaps", json={"ticker": "AGRFX", "fund_family": "alliancebernstein"})
    assert alliance.status_code == 200
    assert alliance.json()["adapter_slug"] == "ab"


def test_coverage_gap_alias_fourth_tier(client: TestClient) -> None:
    jh = client.post("/coverage/gaps", json={"ticker": "TAGRX", "fund_family": "manulife"})
    assert jh.status_code == 200
    assert jh.json()["adapter_slug"] == "john_hancock"
    delaware = client.post("/coverage/gaps", json={"ticker": "WSTAX", "fund_family": "delaware_funds"})
    assert delaware.status_code == 200
    assert delaware.json()["adapter_slug"] == "macquarie"
    putnam = client.post("/coverage/gaps", json={"ticker": "PEYAX", "fund_family": "putnam"})
    assert putnam.status_code == 200
    assert putnam.json()["adapter_slug"] == "franklin_templeton"


def test_coverage_gap_alias_fifth_tier(client: TestClient) -> None:
    oakmark = client.post("/coverage/gaps", json={"ticker": "OAKEX", "fund_family": "harris"})
    assert oakmark.status_code == 200
    assert oakmark.json()["adapter_slug"] == "oakmark"
    mainstay = client.post("/coverage/gaps", json={"ticker": "MLAIX", "fund_family": "mainstay"})
    assert mainstay.status_code == 200
    assert mainstay.json()["adapter_slug"] == "nylife"
    allianz = client.post("/coverage/gaps", json={"ticker": "NLCAX", "fund_family": "allianzgi"})
    assert allianz.status_code == 200
    assert allianz.json()["adapter_slug"] == "voya"
    pioneer = client.post("/coverage/gaps", json={"ticker": "PIODX", "fund_family": "victory_pioneer"})
    assert pioneer.status_code == 200
    assert pioneer.json()["adapter_slug"] == "amundi"
    victory = client.post("/coverage/gaps", json={"ticker": "MMEAX", "fund_family": "vcm"})
    assert victory.status_code == 200
    assert victory.json()["adapter_slug"] == "victory"


def test_coverage_gap_alias_sixth_tier(client: TestClient) -> None:
    sei = client.post("/coverage/gaps", json={"ticker": "SLGAX", "fund_family": "seic"})
    assert sei.status_code == 200
    assert sei.json()["adapter_slug"] == "sei"
    brown = client.post("/coverage/gaps", json={"ticker": "BAFFX", "fund_family": "brown"})
    assert brown.status_code == 200
    assert brown.json()["adapter_slug"] == "brown_advisory"
    blair = client.post("/coverage/gaps", json={"ticker": "BGFIX", "fund_family": "wbim"})
    assert blair.status_code == 200
    assert blair.json()["adapter_slug"] == "william_blair"
    alger = client.post("/coverage/gaps", json={"ticker": "CHUSX", "fund_family": "fred_alger"})
    assert alger.status_code == 200
    assert alger.json()["adapter_slug"] == "alger"
    hl = client.post("/coverage/gaps", json={"ticker": "HLMGX", "fund_family": "harding"})
    assert hl.status_code == 200
    assert hl.json()["adapter_slug"] == "harding_loevner"
    matthews = client.post("/coverage/gaps", json={"ticker": "MEGMX", "fund_family": "matthews"})
    assert matthews.status_code == 200
    assert matthews.json()["adapter_slug"] == "matthews_asia"


def test_coverage_gap_alias_seventh_tier(client: TestClient) -> None:
    diamond = client.post("/coverage/gaps", json={"ticker": "DHPAX", "fund_family": "diamond"})
    assert diamond.status_code == 200
    assert diamond.json()["adapter_slug"] == "diamond_hill"
    cip = client.post("/coverage/gaps", json={"ticker": "CIPIX", "fund_family": "cipvt"})
    assert cip.status_code == 200
    assert cip.json()["adapter_slug"] == "champlain"
    hw = client.post("/coverage/gaps", json={"ticker": "HWLIX", "fund_family": "hotchkis_wiley"})
    assert hw.status_code == 200
    assert hw.json()["adapter_slug"] == "hotchkis"
    ost = client.post("/coverage/gaps", json={"ticker": "OSTFX", "fund_family": "ost"})
    assert ost.status_code == 200
    assert ost.json()["adapter_slug"] == "osterweis"
    davis = client.post("/coverage/gaps", json={"ticker": "NYVTX", "fund_family": "davis_funds"})
    assert davis.status_code == 200
    assert davis.json()["adapter_slug"] == "davis"


def test_coverage_gap_alias_eighth_tier(client: TestClient) -> None:
    odyssey = client.post("/coverage/gaps", json={"ticker": "POSKX", "fund_family": "odyssey"})
    assert odyssey.status_code == 200
    assert odyssey.json()["adapter_slug"] == "primecap"
    southeastern = client.post(
        "/coverage/gaps", json={"ticker": "LLPFX", "fund_family": "southeastern"}
    )
    assert southeastern.status_code == 200
    assert southeastern.json()["adapter_slug"] == "longleaf"
    thirdave = client.post("/coverage/gaps", json={"ticker": "TAVFX", "fund_family": "thirdave"})
    assert thirdave.status_code == 200
    assert thirdave.json()["adapter_slug"] == "third_avenue"
    pax = client.post("/coverage/gaps", json={"ticker": "PAXLX", "fund_family": "pax"})
    assert pax.status_code == 200
    assert pax.json()["adapter_slug"] == "impax"
    fmimgt = client.post("/coverage/gaps", json={"ticker": "FMIUX", "fund_family": "fmimgt"})
    assert fmimgt.status_code == 200
    assert fmimgt.json()["adapter_slug"] == "fmi"


def test_coverage_gap_alias_tenth_tier(client: TestClient) -> None:
    lazard = client.post("/coverage/gaps", json={"ticker": "LZIEX", "fund_family": "lam"})
    assert lazard.status_code == 200
    assert lazard.json()["adapter_slug"] == "lazard"
    manning = client.post("/coverage/gaps", json={"ticker": "MNHIX", "fund_family": "manning"})
    assert manning.status_code == 200
    assert manning.json()["adapter_slug"] == "manning_napier"
    westwood = client.post("/coverage/gaps", json={"ticker": "WHGLX", "fund_family": "whg"})
    assert westwood.status_code == 200
    assert westwood.json()["adapter_slug"] == "westwood"
    homestead = client.post("/coverage/gaps", json={"ticker": "HOVLX", "fund_family": "nreca"})
    assert homestead.status_code == 200
    assert homestead.json()["adapter_slug"] == "homestead"
    riverpark = client.post("/coverage/gaps", json={"ticker": "RPXIX", "fund_family": "rp"})
    assert riverpark.status_code == 200
    assert riverpark.json()["adapter_slug"] == "riverpark"


def test_coverage_gap_alias_ninth_tier(client: TestClient) -> None:
    beacon = client.post("/coverage/gaps", json={"ticker": "AADEX", "fund_family": "beacon"})
    assert beacon.status_code == 200
    assert beacon.json()["adapter_slug"] == "american_beacon"
    baillie = client.post("/coverage/gaps", json={"ticker": "BGAKX", "fund_family": "baillie"})
    assert baillie.status_code == 200
    assert baillie.json()["adapter_slug"] == "baillie_gifford"
    walden = client.post("/coverage/gaps", json={"ticker": "BTBFX", "fund_family": "walden"})
    assert walden.status_code == 200
    assert walden.json()["adapter_slug"] == "boston_trust"
    fenimore = client.post("/coverage/gaps", json={"ticker": "FAMVX", "fund_family": "fenimore"})
    assert fenimore.status_code == 200
    assert fenimore.json()["adapter_slug"] == "fam"
    arrowmark = client.post("/coverage/gaps", json={"ticker": "MVALX", "fund_family": "arrowmark"})
    assert arrowmark.status_code == 200
    assert arrowmark.json()["adapter_slug"] == "meridian"


def test_coverage_gap_requires_ticker_or_name(client: TestClient) -> None:
    response = client.post("/coverage/gaps", json={"holding_dollars": 1000})
    assert response.status_code == 422


def test_fetch_alias_capital_group_still_works(client: TestClient) -> None:
    response = client.post("/ingest/fetch", json={"fund_family": "capital_group", "mode": "fixture"})
    assert response.status_code == 200
    assert response.json()["created"] > 0


def test_partner_ingest_still_escape_hatch(client: TestClient) -> None:
    response = client.post(
        "/ingest/distributions",
        json={
            "records": [
                {
                    "fund_family": "Dimensional",
                    "fund_name": "DFA US Core Equity 2",
                    "ticker": "DFQTX",
                    "estimate_type": "total_capital_gains",
                    "amount": "1.10",
                    "amount_unit": "percent_of_nav",
                    "as_of": "2025-11-01",
                }
            ]
        },
    )
    assert response.status_code == 200
    found = client.get("/distributions", params={"ticker": "DFQTX"})
    assert found.json()["total"] == 1