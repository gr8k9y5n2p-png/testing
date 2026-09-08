from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "american_funds" in body["registered_families"]


def test_ingest_validation_error(client: TestClient) -> None:
    response = client.post("/ingest/distributions", json={"records": [{"fund_family": "X"}]})
    assert response.status_code == 422
    assert response.json()["detail"] == "Validation failed"
    assert "errors" in response.json()


def test_fetch_unknown_family(client: TestClient) -> None:
    response = client.post("/ingest/fetch", json={"fund_family": "not-a-family", "mode": "fixture"})
    assert response.status_code == 404


def test_fetch_vanguard_fixture(client: TestClient) -> None:
    response = client.post("/ingest/fetch", json={"fund_family": "vanguard", "mode": "fixture"})
    assert response.status_code == 200, response.text
    assert response.json()["created"] > 0
    found = client.get("/distributions", params={"ticker": "VBIAX"})
    assert found.json()["total"] >= 1


def test_fixture_fetch_and_search_filters(client: TestClient) -> None:
    fetched = client.post("/ingest/fetch", json={"fund_family": "american_funds", "mode": "fixture"})
    assert fetched.status_code == 200, fetched.text
    body = fetched.json()
    assert body["created"] > 0
    assert body["updated"] == 0

    rerun = client.post("/ingest/fetch", json={"fund_family": "american_funds", "mode": "fixture"})
    assert rerun.status_code == 200
    assert rerun.json()["created"] == 0
    assert rerun.json()["updated"] == body["created"]

    search = client.get("/distributions", params={"q": "AMCAP", "estimate_type": "long_term_capital_gains"})
    assert search.status_code == 200
    payload = search.json()
    assert payload["total"] >= 1
    names = {item["fund_name"] for item in payload["items"]}
    assert "AMCAP Fund" in names
    assert all(item["raw_payload"] is None for item in payload["items"])
    assert all(item["ticker"] == "AMCPX" for item in payload["items"])
    assert all(item["fund_identifier"] == "amcap-fund" for item in payload["items"])

    ticker = client.get("/distributions", params={"ticker": "CGHM"})
    assert ticker.json()["total"] >= 1
    assert all(item["ticker"] == "CGHM" for item in ticker.json()["items"])

    dates = client.get(
        "/distributions",
        params={"ex_date_from": "2026-06-01", "ex_date_to": "2026-06-30", "estimate_type": "long_term_capital_gains"},
    )
    assert dates.json()["total"] >= 1
    assert all(item["ex_date"].startswith("2026-06") for item in dates.json()["items"])

    pct = client.get("/distributions", params={"estimate_type": "total_capital_gains"})
    assert pct.json()["total"] >= 1
    assert any(item["amount_unit"] == "percent_of_nav" for item in pct.json()["items"])

    page1 = client.get("/distributions", params={"page": 1, "page_size": 5})
    page2 = client.get("/distributions", params={"page": 2, "page_size": 5})
    assert page1.json()["page_size"] == 5
    assert page1.json()["total"] == page2.json()["total"]
    assert page1.json()["items"][0]["id"] != page2.json()["items"][0]["id"]

    detail_id = page1.json()["items"][0]["id"]
    detail = client.get(f"/distributions/{detail_id}")
    assert detail.status_code == 200
    assert detail.json()["raw_payload"] is not None

    missing = client.get("/distributions/00000000-0000-0000-0000-000000000000")
    assert missing.status_code == 404


def test_distributions_alias_search_agthx_amcap_amcpx(client: TestClient) -> None:
    fetched = client.post("/ingest/fetch", json={"fund_family": "american_funds", "mode": "fixture"})
    assert fetched.status_code == 200, fetched.text

    for params in (
        {"q": "AGTHX"},
        {"ticker": "AGTHX"},
        {"fund_identifier": "AGTHX"},
    ):
        response = client.get("/distributions", params={**params, "page_size": 50})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["total"] >= 1, params
        assert {item["fund_identifier"] for item in body["items"]} == {"the-growth-fund-of-america"}
        assert {item["ticker"] for item in body["items"]} == {"AGTHX"}

    for params in (
        {"q": "AMCPX"},
        {"ticker": "AMCPX"},
        {"fund_identifier": "AMCPX"},
        {"ticker": "AMCAP"},
        {"fund_identifier": "AMCAP"},
    ):
        response = client.get("/distributions", params={**params, "page_size": 50})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["total"] >= 1, params
        assert {item["fund_identifier"] for item in body["items"]} == {"amcap-fund"}
        assert {item["ticker"] for item in body["items"]} == {"AMCPX"}

    slug = client.get(
        "/distributions",
        params={"fund_identifier": "the-growth-fund-of-america", "page_size": 5},
    )
    assert slug.json()["total"] >= 1
    assert slug.json()["items"][0]["ticker"] == "AGTHX"

    illustrated = client.post(
        "/illustrate",
        json={
            "holding_dollars": 100000,
            "nav_per_share": 50,
            "selectors": {"ticker": "AGTHX"},
        },
    )
    assert illustrated.status_code == 200, illustrated.text
    assert illustrated.json()["components"]
    assert {c["fund_identifier"] for c in illustrated.json()["components"]} == {
        "the-growth-fund-of-america"
    }


def test_distributions_alias_search_blackrock_jpmorgan(client: TestClient) -> None:
    """Name-keyed BR / JPM books resolve newly mapped Investor A / Class A tickers."""
    br = client.post("/ingest/fetch", json={"fund_family": "blackrock", "mode": "fixture"})
    assert br.status_code == 200, br.text
    jpm = client.post("/ingest/fetch", json={"fund_family": "jpmorgan", "mode": "fixture"})
    assert jpm.status_code == 200, jpm.text

    for ticker, ident, family in (
        ("MDDVX", "blackrock-equity-dividend-fund", "BlackRock"),
        ("LIRAX", "blackrock-lifepath-index-retirement-fund", "BlackRock"),
        ("BSPAX", "ishares-s-p-500-index-fund", "BlackRock"),
        ("BMSAX", "blackrock-income-fund", "BlackRock"),
        ("BACAX", "blackrock-energy-opportunities-fund", "BlackRock"),
        ("OIEIX", "jpmorgan-equity-income-fund", "J.P. Morgan"),
        ("UBVAX", "undiscovered-managers-behavioral-value-fund", "J.P. Morgan"),
        ("BBEM", "jpmorgan-betabuilders-emerging-markets-equity-etf", "J.P. Morgan"),
        ("VCAXX", "jpmorgan-california-municipal-money-market-fund", "J.P. Morgan"),
    ):
        response = client.get("/distributions", params={"ticker": ticker, "page_size": 20})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["total"] >= 1, ticker
        assert {item["ticker"] for item in body["items"]} == {ticker}
        assert {item["fund_identifier"] for item in body["items"]} == {ident}
        assert all(family in item["fund_family"] for item in body["items"])


def test_distributions_alias_search_name_keyed_families(client: TestClient) -> None:
    """Name-keyed books resolve Class A / Class S / Investor tickers after maps."""
    for family in (
        "invesco",
        "mfs",
        "john_hancock",
        "bny_mellon",
        "hartford",
        "ab",
        "thrivent",
        "calamos",
        "wasatch",
        "voya",
    ):
        fetched = client.post("/ingest/fetch", json={"fund_family": family, "mode": "fixture"})
        assert fetched.status_code == 200, fetched.text

    for ticker, ident, family in (
        ("VAFAX", "invesco-american-franchise-fund", "Invesco"),
        ("MRGAX", "mfs-core-equity-fund-class-a", "MFS"),
        ("MIEJX", "mfs-international-equity-fund-all-classes", "MFS"),
        ("SVBAX", "john-hancock-balanced-fund", "John Hancock"),
        ("DAGVX", "bny-mellon-dynamic-value-fund", "BNY"),
        ("ITHAX", "the-hartford-capital-appreciation-fund", "Hartford"),
        ("CHCLX", "ab-discovery-growth-fund-inc", "AllianceBernstein"),
        ("TAAIX", "thrivent-aggressive-allocation-fund", "Thrivent"),
        ("CPLSX", "calamos-phineus-long-short-fund", "Calamos"),
        ("WAAEX", "wasatch-small-cap-growth-fund", "Wasatch"),
        ("IEDAX", "voya-large-cap-value-fund", "Voya"),
    ):
        response = client.get("/distributions", params={"ticker": ticker, "page_size": 20})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["total"] >= 1, ticker
        assert {item["ticker"] for item in body["items"]} == {ticker}
        assert {item["fund_identifier"] for item in body["items"]} == {ident}
        assert all(family in item["fund_family"] for item in body["items"])


def test_distributions_alias_search_abalx_class_a(client: TestClient) -> None:
    """Live Cap Group HTML is name-keyed; ABALX must resolve to American Balanced Fund."""
    fetched = client.post("/ingest/fetch", json={"fund_family": "american_funds", "mode": "fixture"})
    assert fetched.status_code == 200, fetched.text

    for params in (
        {"q": "ABALX"},
        {"ticker": "ABALX"},
        {"fund_identifier": "ABALX"},
        {"ticker": "AMBAL"},
    ):
        response = client.get("/distributions", params={**params, "page_size": 50})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["total"] >= 1, params
        assert {item["fund_identifier"] for item in body["items"]} == {"american-balanced-fund"}
        assert {item["ticker"] for item in body["items"]} == {"ABALX"}
        assert {item["cusip"] for item in body["items"] if item.get("cusip")} <= {"024071102"}

    ltcg = client.get(
        "/distributions",
        params={
            "ticker": "ABALX",
            "estimate_type": "long_term_capital_gains",
            "publication_stage": "final",
            "page_size": 50,
        },
    )
    assert ltcg.status_code == 200, ltcg.text
    amounts = {Decimal(item["amount"]) for item in ltcg.json()["items"] if item["amount"] is not None}
    assert Decimal("2.1250") in amounts
    assert all(item["ticker"] == "ABALX" for item in ltcg.json()["items"])
    assert all(item["cusip"] == "024071102" for item in ltcg.json()["items"])

    illustrated = client.post(
        "/illustrate",
        json={
            "holding_dollars": 100000,
            "nav_per_share": 40,
            "selectors": {"ticker": "ABALX"},
        },
    )
    assert illustrated.status_code == 200, illustrated.text
    body = illustrated.json()
    assert body["components"]
    assert {c["fund_identifier"] for c in body["components"]} == {"american-balanced-fund"}
    assert {c["ticker"] for c in body["components"]} == {"ABALX"}
    assert any(
        c["estimate_type"] == "long_term_capital_gains" and Decimal(c["amount"]) == Decimal("2.1250")
        for c in body["components"]
    )


def test_fund_families_coverage_ranks(client: TestClient) -> None:
    fetched = client.post("/ingest/fetch", json={"fund_family": "american_funds", "mode": "fixture"})
    assert fetched.status_code == 200, fetched.text
    families = client.get("/fund-families")
    assert families.status_code == 200
    slugs = {row["slug"]: row for row in families.json()}
    assert slugs["american_funds"]["implemented"] is True
    assert slugs["american_funds"]["coverage_tier"] == "implemented"
    assert slugs["american_funds"]["aum_rank"] == 7
    assert slugs["american_funds"]["last_ingest_status"] == "success"
    assert slugs["vanguard"]["implemented"] is True
    assert slugs["vanguard"]["aum_rank"] == 2
    assert slugs["blackrock"]["aum_rank"] == 1
    assert slugs["ubs"]["aum_rank"] == 11
    assert slugs["amundi"]["aum_rank"] == 20
    assert slugs["allspring"]["aum_rank"] == 21
    assert slugs["eaton_vance"]["aum_rank"] == 30
    assert slugs["john_hancock"]["aum_rank"] == 31
    assert slugs["wasatch"]["aum_rank"] == 40
    assert slugs["harbor"]["aum_rank"] == 41
    assert slugs["victory"]["aum_rank"] == 50
    assert slugs["sei"]["aum_rank"] == 51
    assert slugs["matthews_asia"]["aum_rank"] == 60
    assert slugs["tcw"]["aum_rank"] == 61
    assert slugs["davis"]["aum_rank"] == 70
    assert slugs["primecap"]["aum_rank"] == 71
    assert slugs["impax"]["aum_rank"] == 80
    assert slugs["american_beacon"]["aum_rank"] == 81
    assert slugs["kinetics"]["aum_rank"] == 90
    assert slugs["lazard"]["aum_rank"] == 91
    assert slugs["riverpark"]["aum_rank"] == 100
    assert slugs["amg"]["aum_rank"] == 101
    assert slugs["tocqueville"]["aum_rank"] == 110
    assert slugs["first_trust"]["aum_rank"] == 111
    assert slugs["impax"]["implemented"] is True
    assert slugs["gqg"]["implemented"] is True
    assert slugs["third_avenue"]["implemented"] is True
    assert slugs["baillie_gifford"]["implemented"] is True
    assert slugs["meridian"]["implemented"] is True
    assert slugs["dimensional"]["implemented"] is True
    assert slugs["ab"]["implemented"] is True
    assert slugs["calamos"]["implemented"] is True
    assert slugs["oakmark"]["implemented"] is True
    assert slugs["nylife"]["implemented"] is True
    assert slugs["alger"]["implemented"] is True
    assert slugs["jensen"]["implemented"] is True
    assert slugs["hotchkis"]["implemented"] is True
    assert slugs["lazard"]["implemented"] is True
    assert slugs["manning_napier"]["implemented"] is True
    assert slugs["madison"]["implemented"] is True
    assert slugs["oberweis"]["implemented"] is True
    assert slugs["amg"]["implemented"] is True
    assert slugs["guidestone"]["implemented"] is True
    assert slugs["value_line"]["implemented"] is True
    assert slugs["tocqueville"]["implemented"] is True
    assert slugs["first_trust"]["implemented"] is True
    assert len(slugs) == 111


def test_manual_ingest_partner_feed(client: TestClient) -> None:
    response = client.post(
        "/ingest/distributions",
        json={
            "records": [
                {
                    "fund_family": "Vanguard",
                    "fund_name": "Vanguard 500 Index Fund",
                    "ticker": "VFIAX",
                    "share_class": "Admiral",
                    "estimate_type": "total_capital_gains",
                    "amount_min": "1.2",
                    "amount_max": "1.8",
                    "amount_unit": "percent_of_nav",
                    "as_of": "2025-11-15",
                    "ex_date": "2025-12-17",
                    "source_url": "https://example.invalid/partner",
                }
            ]
        },
    )
    assert response.status_code == 200
    assert response.json()["created"] == 1
    found = client.get("/distributions", params={"ticker": "VFIAX"})
    item = found.json()["items"][0]
    assert item["amount_unit"] == "percent_of_nav"
    assert Decimal(item["amount"]) == Decimal("1.5")
