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
        "Growth / Long Term Global Growth / U.S. Equity Growth omitted."
    )
    live_limitations = (
        "Estimate book is PDF. Fixture transcribes public Institutional / Class K "
        "identifiers from the official prospectus."
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
            )
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
        "Amounts unchanged. Tax-loss Core Plus / SMART omitted."
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
            )
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
        "public Investor-class identifiers."
    )
    live_limitations = (
        "Live HTML is public but fund-name-only table may not attach tickers. Fixture fallback."
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
            )
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
        "Record 12/15/2025; ex 12/16/2025; pay 12/17/2025."
    )
    live_limitations = "Year-end book is PDF. Fixture transcribes public ticker rows."

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
            )
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
        "Cornerstone Growth Investor printed no 2025 distributions — omitted."
    )
    live_limitations = (
        "Live HTML is public but expandable history tables may not parse. "
        "Fixture transcribes official December YE Investor + Institutional rows."
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
            )
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
        "corrected to official Investor FAMFX / Institutional FAMDX."
    )
    live_limitations = (
        "Live HTML is public but class-name rows have no ticker column. Fixture fallback."
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
            )
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
        "Published $0.00 stored."
    )
    live_limitations = (
        "Year-end book is PDF. Fixture transcribes the official full share-class book. "
        "Weekly walk hits the family hub (empty/403/PDF-bytes = no-op success)."
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
            )
        ]
