"""Ranks 81–90 boutique US-advisor families with scrapeable public CG books."""

from __future__ import annotations

from app.sources.html_source import HtmlTableSource, PageSpec


class AmericanBeaconSource(HtmlTableSource):
    slug = "american_beacon"
    display_name = "American Beacon"
    aum_rank = 81
    priority = 81
    notes = (
        "Tax center: https://americanbeaconfunds.com/fund-resources/tax-and-distribution-center/ "
        "Official 2025 year-end ordinary-income and capital-gains PDF is the full "
        "printed share-class book (Wayback id_ capture after live WP 403): "
        "https://americanbeaconfunds.com/wp-content/uploads/2025/09/"
        "2025-Annual-Ordinary-Income-and-Capital-Gains-Mutual-Funds-updated.pdf "
        "(Large Cap Value R5 AADEX ST $0.3607 / LT $2.3846; "
        "Stephens Mid-Cap Growth R5 SFMIX ST $0.7583 / LT $8.0356; "
        "London Company Income Equity R5 ABCIX ST $0.0696 / LT $3.0255). "
        "Record 12/19/2025; ex/reinvest 12/22/2025; pay 12/23/2025. "
        "Wave 6 lookback: official 2021–2024 YE PDFs on the same tax-center archive "
        "(2021YearEndDistributions.pdf AADEX income $0.3864 / ST $0.5435 / LT $2.2327; "
        "2022YearEndDistributions.pdf AADEX income $0.4256 / published ST $0.0001 / LT $2.3936; "
        "2023AmericanBeaconFundsYearEndDistributions.pdf AADEX income $0.4571 / ST $0.0709 / LT $0.8312; "
        "AmericanBeaconFundYearEndDistributions12.20.2024.pdf AADEX income $0.4994 / ST $0.2576 / LT $2.5614). "
        "All-dash rows omitted (SFMIX 2023 is unmatched, not invented). "
        "Parallel 5y sweep C leftover years re-extracted from the official "
        "YE PDFs: Stephens Mid-Cap Growth (SFMIX / STMGX / SMFYX / SMFAX / "
        "SMFCX / SFMRX) 2023 is all-dash; SSI Alternative Income (SSIJX / "
        "PSCIX / PSCAX) 2024 is all-dash; Sound Point / FEAC Floating Rate "
        "(SPFYX / SPFLX / SPFPX / SOUAX / SOUCX) 2025 is all-dash. Leftover "
        "3y AHL Multi-Alternatives / Garcia Hamilton Quality Bond / NIS "
        "Core Plus are absent from the 2021 and 2022 YE books (not listed). "
        "Official dashes / absent rows stay unmatched — never invent $0. "
        "Live WP GET 403 this session — weekly walk still hits the tax-center hub + "
        "2025 PDF URL (empty/403 = no-op success)."
    )
    live_limitations = (
        "Year-end book is PDF. Live WP path is sometimes 403; fixture transcribes "
        "the official Wayback / issuer full share-class books."
    )

    def pages(self) -> list[PageSpec]:
        archive = "https://americanbeaconfunds.com/wp-content/uploads/2025/08"
        return [
            PageSpec(
                name="tax_and_distribution_center_hub",
                url="https://americanbeaconfunds.com/fund-resources/tax-and-distribution-center/",
                fixture="tax_and_distribution_center_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_annual_ordinary_income_and_capital_gains",
                url=(
                    "https://americanbeaconfunds.com/wp-content/uploads/2025/09/"
                    "2025-Annual-Ordinary-Income-and-Capital-Gains-Mutual-Funds-updated.pdf"
                ),
                fixture="2025_annual_ordinary_income_and_capital_gains.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2024_annual_ordinary_income_and_capital_gains",
                url=f"{archive}/AmericanBeaconFundYearEndDistributions12.20.2024.pdf",
                fixture="2024_annual_ordinary_income_and_capital_gains.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2023_annual_ordinary_income_and_capital_gains",
                url=f"{archive}/2023AmericanBeaconFundsYearEndDistributions.pdf",
                fixture="2023_annual_ordinary_income_and_capital_gains.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2022_annual_ordinary_income_and_capital_gains",
                url=f"{archive}/2022YearEndDistributions.pdf",
                fixture="2022_annual_ordinary_income_and_capital_gains.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2021_annual_ordinary_income_and_capital_gains",
                url=f"{archive}/2021YearEndDistributions.pdf",
                fixture="2021_annual_ordinary_income_and_capital_gains.html",
                live=False,
                role="history",
            ),
        ]


class BaillieGiffordSource(HtmlTableSource):
    slug = "baillie_gifford"
    display_name = "Baillie Gifford"
    aum_rank = 82
    priority = 82
    notes = (
        "Public 10/31/2025 estimate PDF (dated 12/17/2025): "
        "https://www.bailliegifford.com/literature-library/funds/mutual-funds/"
        "estimated-capital-gain-distribution/ "
        "(Developed EAFE All Cap BSGPX LT $4.7303; "
        "Global Alpha Equities BGAKX LT $4.8350; "
        "International Growth BGESX LT $0.7461). "
        "Record 12/26/2025; ex/pay 12/29/2025. The PDF is fund-level; Institutional / "
        "Class K tickers from official Baillie Gifford Funds prospectus "
        "(BSGPX / BGCSX / BGAKX / BINSX / BGESX). Amounts unchanged. "
        "All-dash China / Emerging Markets / Concentrated "
        "Growth / Long Term Global Growth / U.S. Equity Growth omitted. "
        "Leftover paid 2025 Final product-page tables for in-book leftovers "
        "BGAKX Class K and BINSX / BGESX / BSGPX Institutional only "
        "(official printed $0.00000 ST stored). Class-level — never copy K onto "
        "Institutional. BGCSX has no Final table. Official 5y WAVE BF leftover "
        "(existing in-book only): Baillie Gifford Funds FYE December 31 N-CSR "
        "Financial Highlights unlock leftover 2021–2024 on the 2025 paid Final "
        "book. Calendar-safe as_of 12/31. Class-level Class K / Institutional — "
        "never sibling-copied onto Class 2 / 3 / K or Institutional siblings "
        "(BGIKX / BGEKX / BGPKX / Global Alpha Institutional). China Equities "
        "BGCSX has no 2025 Final and is not an in-book leftover on this page. "
        "Income is ordinary income; net realized gain is unsplit total capital "
        "gains. Issuer dashes omitted (BGAKX 2023 CG; BINSX 2023–2022 CG; "
        "BGESX 2022 OI; BSGPX 2024–2023 CG and 2022 OI). 2025 stays on the "
        "existing paid Final product-page book (BGAKX LT $5.18723 is not "
        "overwritten by N-CSR 2-decimal highlights). N-CSR "
        "https://www.sec.gov/Archives/edgar/data/1120543/000110465925020192/"
        "tm251686d1_ncsr.htm verified against 2023 N-CSR "
        "0001104659-24-030888. WAVE BF leftover N-CSR paid history is "
        "fixture-only. Live most-recent product-page tables still omit "
        "2021–2024; Wayback CDX offline."
    )
    live_limitations = (
        "Estimate book is PDF. Fixture transcribes public Institutional / Class K "
        "identifiers from the official prospectus. Leftover 2021–2024 N-CSR "
        "paid history is fixture-only."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_capital_gains",
                url=(
                    "https://www.bailliegifford.com/literature-library/funds/"
                    "mutual-funds/estimated-capital-gain-distribution/"
                ),
                fixture="2025_estimated_capital_gains.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="leftover_paid_history_parallel_v",
                url=(
                    "https://www.bailliegifford.com/en/usa/institutional-investor/"
                    "funds/baillie-gifford-global-alpha-equities-fund/"
                ),
                fixture="leftover_paid_history_parallel_v.html",
                live=False,
                role="history",
                large_aum_only=False,
            ),
            PageSpec(
                name="leftover_ncsr_2021_2024_wave_bf",
                url=(
                    "https://www.sec.gov/Archives/edgar/data/1120543/"
                    "000110465925020192/tm251686d1_ncsr.htm"
                ),
                fixture="leftover_ncsr_2021_2024_wave_bf.html",
                live=False,
                role="history",
            ),
        ]


class BrandesSource(HtmlTableSource):
    slug = "brandes"
    display_name = "Brandes"
    aum_rank = 83
    priority = 83
    notes = (
        "Public 11/20/2025 estimate PDF: "
        "https://www.brandes.com/docs/librariesprovider6/default-library/publication/"
        "handout/brandes-mutual-funds-capital-gains-distribution-estimates-mutual-funds.pdf"
        "?sfvrsn=1329da10_43 "
        "(Global Equity BGVIX ST $0.05 / LT $3.88; "
        "International Equity BIIEX ST $0.04 / LT $0.95; "
        "Small Cap Value BSCMX ST $0.32 / LT $0.49). "
        "Record 12/09/2025; ex/pay 12/10/2025. The PDF is fund-level; Class I tickers "
        "from official brandes.com fund pages (BISMX / BGVIX / BIIEX / BEMIX / BSCMX). "
        "Amounts unchanged. Tax-loss Core Plus / SMART omitted. "
        "Leftover paid Class I product-page Distributions 2021–2025 "
        "(December YE income + December CG; paid ≠ estimate — BGVIX 2025 LT "
        "$3.624675 vs estimate $3.88). Official printed $0.000000 stored "
        "(BEMIX 2022 December income). A / C / R6 not in-book."
    )
    live_limitations = (
        "Estimate book is PDF. Fixture transcribes public Class I identifiers "
        "from official brandes.com fund pages."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_capital_gains",
                url=(
                    "https://www.brandes.com/docs/librariesprovider6/default-library/"
                    "publication/handout/"
                    "brandes-mutual-funds-capital-gains-distribution-estimates-mutual-funds.pdf"
                    "?sfvrsn=1329da10_43"
                ),
                fixture="2025_estimated_capital_gains.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="leftover_paid_history_parallel_v",
                url="https://www.brandes.com/funds/fund/brandes-global-equity-fund/bgvix",
                fixture="leftover_paid_history_parallel_v.html",
                live=False,
                role="history",
                large_aum_only=False,
            ),
        ]


class MairsPowerSource(HtmlTableSource):
    slug = "mairs_power"
    display_name = "Mairs & Power"
    aum_rank = 84
    priority = 84
    notes = (
        "Public 12/16/2025 paid HTML: "
        "https://www.mairsandpower.com/about-us/company-news/290-2025-capital-gains-and-dividends "
        "(Growth MPGFX income $0.50829 / LT $6.77074; "
        "Balanced MAPOX income $0.62548 / LT $0.90734; "
        "Small Cap MSCFX income $0.00096 / LT $0.70684). "
        "Record 12/12/2025; ex/pay 12/15/2025. The HTML is fund-level; tickers are "
        "public Investor-class identifiers. "
        "Official 5y WAVE BC leftover (existing in-book only): Trust for "
        "Professional Managers FYE December 31 N-CSR Financial Highlights unlock "
        "leftover 2021–2024 on the 2025 paid year-end book (Growth MPGFX, "
        "Balanced MAPOX, Small Cap MSCFX). Calendar-safe as_of 12/31. "
        "Class-level Investor — never sibling-copied. Minnesota Municipal Bond "
        "ETF MINN is not on the 2025 paid book and is not an in-book leftover. "
        "Income is ordinary income; capital gains are unsplit total capital "
        "gains. Issuer printed $0.00 less-than / rounded footnotes omitted "
        "(MAPOX 2024 CG). 2025 stays on the existing paid year-end book "
        "(MPGFX LT $6.77074 is not overwritten by N-CSR CG $6.77). N-CSR "
        "https://www.sec.gov/Archives/edgar/data/1141819/000113322826003081/"
        "tmpf-efp22286_ncsr.htm verified against 2023 "
        "0001104659-24-031743. WAVE BC leftover N-CSR paid history is fixture-only."
    )
    live_limitations = (
        "Live HTML is public but fund-name-only table may not attach tickers. Fixture fallback. "
        "Leftover 2021–2024 N-CSR paid history is fixture-only."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_capital_gains_and_dividends",
                url=(
                    "https://www.mairsandpower.com/about-us/company-news/"
                    "290-2025-capital-gains-and-dividends"
                ),
                fixture="2025_capital_gains_and_dividends.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="leftover_ncsr_2021_2024_wave_bc",
                url=(
                    "https://www.sec.gov/Archives/edgar/data/1141819/"
                    "000113322826003081/tmpf-efp22286_ncsr.htm"
                ),
                fixture="leftover_ncsr_2021_2024_wave_bc.html",
                live=False,
                role="history",
            ),
        ]


class BostonTrustSource(HtmlTableSource):
    slug = "boston_trust"
    display_name = "Boston Trust Walden"
    aum_rank = 85
    priority = 85
    notes = (
        "Hub: https://www.bostontrustwalden.com/strategies-funds/mutual-funds/ "
        "Public 2025 income and capital-gain distribution-factor PDF: "
        "https://www.bostontrustwalden.com/wp-content/uploads/2025/12/"
        "Boston-Trust-Mutual-Funds-2025-Ex-Date-ending-NAV.pdf "
        "(Asset Management BTBFX ST $0.014659 / LT $6.205293; "
        "Midcap BTMFX ST $0.058862 / LT $2.253903; "
        "Walden Equity WSEFX LT $3.989025). "
        "Record 12/15/2025; ex 12/16/2025; pay 12/17/2025. "
        "Official 5y WAVE BB leftover (existing in-book only): May 1, 2026 "
        "prospectus Financial Highlights unlock leftover 2021–2024 on the "
        "2025 paid PDF book (BTBFX / BTMFX / WSEFX). Calendar-safe as_of "
        "12/31. Single-class in-book identities — never sibling-copied and "
        "never attached to out-of-book BTEFX / BTSMX / WSBFX / WAMFX / "
        "WASMX / BOSOX / WIEFX. Income is ordinary income; net realized "
        "gain is unsplit total capital gains. 2025 stays on the existing "
        "paid PDF. Official source "
        "https://www.sec.gov/Archives/edgar/data/882748/000139834426007318/"
        "fp0098118-14_485bposixbrl.htm (accession 0001398344-26-007318; "
        "audited by Cohen & Company, Ltd.). Cross-checked against the 2023 "
        "N-CSR Financial Highlights "
        "https://www.sec.gov/Archives/edgar/data/882748/000139834424005166/"
        "fp0087387-1_ncsr.htm (2023 / 2022 / 2021 columns match). The "
        "10/31/24 estimated capital-gains PDF is not used. WAVE BB leftover "
        "N-CSR / prospectus paid history is fixture-only."
    )
    live_limitations = (
        "Year-end book is PDF. Fixture transcribes public ticker rows. "
        "Weekly walk hits the 2025 paid PDF (empty/403/PDF-bytes = no-op "
        "success). Leftover 2021–2024 N-CSR / prospectus paid history is "
        "fixture-only."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_distribution_factors",
                url=(
                    "https://www.bostontrustwalden.com/wp-content/uploads/2025/12/"
                    "Boston-Trust-Mutual-Funds-2025-Ex-Date-ending-NAV.pdf"
                ),
                fixture="2025_distribution_factors.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="leftover_ncsr_2021_2024_wave_bb",
                url=(
                    "https://www.sec.gov/Archives/edgar/data/882748/"
                    "000139834426007318/fp0098118-14_485bposixbrl.htm"
                ),
                fixture="leftover_ncsr_2021_2024_wave_bb.html",
                live=False,
                role="history",
            ),
        ]


class GrandeurPeakSource(HtmlTableSource):
    slug = "grandeur_peak"
    display_name = "Grandeur Peak"
    aum_rank = 86
    priority = 86
    notes = (
        "Public 2025 paid HTML: https://grandeurpeakglobal.com/distributions/ "
        "(Emerging Markets Opportunities Inst GPEIX ST $0.10530 / LT $2.30240; "
        "Global Contrarian Inst GPGCX ST $0.49440 / LT $1.26100; "
        "Global Reach Investor GPROX ST $0.14570 / LT $2.26220). "
        "Record 12/18/2025; ex/pay 12/19/2025."
    )
    live_limitations = (
        "Live HTML is public but multi-year accordion tables may not parse. Fixture fallback."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_year_end_distributions",
                url="https://grandeurpeakglobal.com/distributions/",
                fixture="2025_year_end_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            )
        ]


class HennessySource(HtmlTableSource):
    slug = "hennessy"
    display_name = "Hennessy"
    aum_rank = 87
    priority = 87
    notes = (
        "Public 2025 paid HTML: https://www.hennessyfunds.com/funds/distributions "
        "Full Investor + Institutional December YE "
        "(Focus Investor HFCSX LT $17.84742; "
        "Cornerstone Large Growth Investor HFLGX ST $0.00693 / LT $0.57633; "
        "Cornerstone Value Investor HFCVX ST $0.01310 / LT $1.06282). "
        "Capital-gains record 12/03/2025; pay 12/04/2025. "
        "March/June/September quarterly income-only omitted. Monthly Midstream omitted. "
        "Cornerstone Growth Investor printed no 2025 distributions — omitted. "
        "Official 5y WAVE AY leftover (existing in-book only): Hennessy Funds "
        "Trust FYE October 31 N-CSR Financial Highlights unlock leftover "
        "2021–2024 on the 2025 distributions paid book (Focus HFCSX / HFCIX, "
        "Large Growth HFLGX / HILGX, Value HFCVX / HICVX, Total Return HDOGX, "
        "Equity and Income HEIFX / HEIIX, Balanced HBFBX, Gas GASFX / HGASX, "
        "Japan Small Cap HJPSX / HJSIX, Small Cap Financial HSFNX / HISFX). "
        "Calendar-safe as_of 10/31. Class-level Investor / Institutional — "
        "never sibling-copied. Cornerstone Growth Investor HFCGX is not on the "
        "2025 paid book and is not an in-book leftover. Midstream HMSFX / "
        "HMSIX monthly income was omitted from the 2025 paid book. Income is "
        "ordinary income; net realized gain is unsplit total capital gains. "
        "Issuer dashes and between-$(0.005)-and-$0.005 footnotes omitted "
        "(Cornerstone Growth Inst 2021; Mid Cap 30 2021; Energy 2021+2024; "
        "Japan 2021+2023; Large Cap Financial 2021; Technology 2024). 2025 "
        "N-CSR https://www.sec.gov/Archives/edgar/data/891944/000199937126000464/"
        "hft-ncsr_103125.htm verified against 2024 "
        "0001999371-25-000211 / hft_hf-ncsr.htm. WAVE AY leftover N-CSR paid "
        "history is fixture-only."
    )
    live_limitations = (
        "Live HTML is public but expandable history tables may not parse. "
        "Fixture transcribes official December YE Investor + Institutional rows. "
        "Leftover 2021–2024 N-CSR paid history is fixture-only."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_year_end_distributions",
                url="https://www.hennessyfunds.com/funds/distributions",
                fixture="2025_year_end_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="leftover_ncsr_2021_2024_wave_ay",
                url=(
                    "https://www.sec.gov/Archives/edgar/data/891944/"
                    "000199937126000464/hft-ncsr_103125.htm"
                ),
                fixture="leftover_ncsr_2021_2024_wave_ay.html",
                live=False,
                role="history",
            ),
        ]


class FamSource(HtmlTableSource):
    slug = "fam"
    display_name = "FAM / Fenimore"
    aum_rank = 88
    priority = 88
    notes = (
        "Public 2025 paid HTML: https://fenimoreasset.com/resources/fam-funds-tax-center/ "
        "(Value Investor FAMVX / Institutional FAMWX LT $4.8682; "
        "Dividend Focus Investor FAMEX LT $1.9884 / income $0.017; "
        "Small Cap Investor FAMFX / Institutional FAMDX LT $0.773). "
        "Record 12/29/2025; ex/pay 12/30/2025. Published $0.00 stored. "
        "The HTML is class-level without tickers; tickers from official "
        "fenimoreasset.com product pages. Prior FAMDX-on-Investor assignment "
        "corrected to official Investor FAMFX / Institutional FAMDX. "
        "Official 5y WAVE AX leftover (existing in-book only): Fenimore Asset "
        "Management Trust FYE December 31 N-CSR Financial Highlights unlock "
        "leftover 2021–2024 on the 2025 tax-center paid book (FAMVX / FAMWX / "
        "FAMEX / FAMFX / FAMDX). Calendar-safe as_of 12/31. Class-level Investor "
        "/ Institutional — never sibling-copied. Dividend Focus Institutional "
        "is not offered and is not an in-book leftover. Income is ordinary "
        "income; net realized gain is unsplit total capital gains. Issuer dashes "
        "omitted (Value 2024 OI; Dividend Focus 2021 OI). Small Cap leftover "
        "years have no ordinary-income distribution. 2024 N-CSR "
        "https://www.sec.gov/Archives/edgar/data/797136/000158064225001402/fam_ncsr.htm "
        "verified against 2023/2022/2021 N-CSR siblings. WAVE AX leftover N-CSR "
        "paid history is fixture-only."
    )
    live_limitations = (
        "Live HTML is public but class-name rows have no ticker column. Fixture fallback. "
        "Leftover 2021–2024 N-CSR paid history is fixture-only."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_year_end_distributions",
                url="https://fenimoreasset.com/resources/fam-funds-tax-center/",
                fixture="2025_year_end_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="leftover_ncsr_2021_2024_wave_ax",
                url="https://www.sec.gov/Archives/edgar/data/797136/000158064225001402/fam_ncsr.htm",
                fixture="leftover_ncsr_2021_2024_wave_ax.html",
                live=False,
                role="history",
            ),
        ]


class MeridianSource(HtmlTableSource):
    slug = "meridian"
    display_name = "Meridian"
    aum_rank = 89
    priority = 89
    notes = (
        "Hub: https://www.arrowmarkpartners.com/meridian/investor-resources/ "
        "Public 12/19/2025 final PDF: "
        "https://www.arrowmarkpartners.com/meridian/wp-content/uploads/sites/2/"
        "2025-Final-Distributions-Meridian-Funds-121925.pdf "
        "(Contrarian Legacy MVALX ST $0.86910 / LT $4.10477; "
        "Hedged Equity Legacy MEIFX LT $0.75498; "
        "Small Cap Growth Legacy MSGGX LT $0.95996). "
        "Record 12/18/2025; ex/pay 12/19/2025. Full printed share-class book. "
        "Published $0.00 stored."
    )
    live_limitations = (
        "Year-end book is PDF. Fixture transcribes the official full share-class book. "
        "Weekly walk hits the investor-resources hub (empty/403/PDF-bytes = no-op success)."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="investor_resources_hub",
                url="https://www.arrowmarkpartners.com/meridian/investor-resources/",
                fixture="investor_resources_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_final_distributions",
                url=(
                    "https://www.arrowmarkpartners.com/meridian/wp-content/uploads/sites/2/"
                    "2025-Final-Distributions-Meridian-Funds-121925.pdf"
                ),
                fixture="2025_final_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            )
        ]


class KineticsSource(HtmlTableSource):
    slug = "kinetics"
    display_name = "Kinetics"
    aum_rank = 90
    priority = 90
    notes = (
        "Public 12/30/2025 final PDF: "
        "https://kineticsfunds.com/wp-content/uploads/2025/12/"
        "2025-Q4-Kinetics-Funds-Final-Distributions.pdf "
        "(Paradigm No Load WWNPX LT $8.68572; "
        "Internet No Load WWWFX ST $0.02951 / LT $1.62421; "
        "Spin-Off and Corporate Restructuring No Load LSHEX LT $2.64639). "
        "Record 12/29/2025; ex/pay 12/30/2025. Full printed share-class book. "
        "Published $0.00 stored. "
        "Official 5y WAVE AZ leftover (existing in-book only): Kinetics Mutual "
        "Funds, Inc. FYE December 31 N-CSR Financial Highlights unlock leftover "
        "2021–2024 on the 2025 Q4 final paid book (WWWFX / KINAX / KINCX / WWWEX "
        "/ KGLAX / KGLCX / WWNPX / KNPAX / KNPCX / KNPYX / KSCOX / KSOAX / "
        "KSOCX / KSCYX / KMKNX / KMKAX / KMKCX / KMKYX / KMDNX / LSHEX / LSHAX "
        "/ LSHCX / LSHUX). Calendar-safe as_of 12/31. Class-level No Load / "
        "Advisor A / Advisor C / Institutional — never sibling-copied. Income is "
        "ordinary income; net realized gain is unsplit total capital gains. "
        "Issuer dashes omitted (Internet 2023–2021 OI; Paradigm Advisor A/C OI; "
        "Small Cap 2022 both-dash years stay 4y; Market Opportunities 2023 CG; "
        "Spin-Off 2021 CG). 2025 stays on the existing Q4 final PDF. Issuer "
        "annual report https://kineticsfunds.com/files/annual-report. WAVE AZ "
        "leftover N-CSR paid history is fixture-only."
    )
    live_limitations = (
        "Year-end book is PDF. Fixture transcribes the official full share-class book. "
        "Weekly walk hits the family hub (empty/403/PDF-bytes = no-op success). "
        "Leftover 2021–2024 N-CSR paid history is fixture-only."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="distributions_hub",
                url="https://kineticsfunds.com/",
                fixture="distributions_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_final_distributions",
                url=(
                    "https://kineticsfunds.com/wp-content/uploads/2025/12/"
                    "2025-Q4-Kinetics-Funds-Final-Distributions.pdf"
                ),
                fixture="2025_final_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="leftover_ncsr_2021_2024_wave_az",
                url="https://kineticsfunds.com/files/annual-report",
                fixture="leftover_ncsr_2021_2024_wave_az.html",
                live=False,
                role="history",
            ),
        ]
