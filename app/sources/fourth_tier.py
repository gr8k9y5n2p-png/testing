from __future__ import annotations

from app.sources.html_source import HtmlTableSource, PageSpec


class JohnHancockSource(HtmlTableSource):
    slug = "john_hancock"
    display_name = "John Hancock / Manulife"
    aum_rank = 31
    priority = 31
    notes = (
        "Press release HTML: "
        "https://www.jhinvestments.com/about-us/press-releases/2025-estimated-capital-gain-and-income-distributions "
        "Public 2025 estimate PDF (as of 9/30/2025, starred rows 10/31/2025): "
        "https://www.jhinvestments.com/content/dam/jhi-investments/JHINV/public/Corporate/News/"
        "CorporatePressReleases/estimated-capital-gain-and-income-distribution-press-release-2025-jhi.pdf "
        "(e.g. Fundamental Large Cap Core TAGRX LT $6.85–$7.60 / 9.11%–10.11% of NAV; "
        "U.S. Global Leaders Growth USGLX LT $11.50–$12.50 / 16.38%–17.80%). "
        "Tickers are the public Class A identifiers; the PDF is fund-level ranges."
    )
    live_limitations = (
        "Family book is a PDF (press-release HTML is a viewer/shell). Fixture transcribes public A-share ranges."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_capital_gains",
                url=(
                    "https://www.jhinvestments.com/content/dam/jhi-investments/JHINV/public/"
                    "Corporate/News/CorporatePressReleases/"
                    "estimated-capital-gain-and-income-distribution-press-release-2025-jhi.pdf"
                ),
                fixture="2025_estimated_capital_gains.html",
                live=False,
            )
        ]


class PrincipalSource(HtmlTableSource):
    slug = "principal"
    display_name = "Principal"
    aum_rank = 32
    priority = 32
    notes = (
        "Tax-center hub: "
        "https://www.principal.com/help/help-individuals/tax-center/dividends-capital-gains-distributions "
        "links Principal Funds estimated-capital-gains PDFs through a GetFile viewer "
        "(https://secure02.principal.com/publicvsupply/GetFile?EXT=.VOP&fm=MM3682&ty=VOP) "
        "that does not expose a scrapeable table. Public product pages publish HTML paid "
        "distribution history, e.g. Equity Income "
        "https://www.principalam.com/us/fund/pqiax "
        "(2025-12-11 ST $0.1254 / LT $3.3687) and MidCap "
        "https://www.principalam.com/us/fund/pemgx "
        "(2025-12-11 LT $2.4892). Fixture transcribes those public rows."
    )
    live_limitations = (
        "Family estimate PDF is a GetFile/viewer shell. Product-page tables may put the date "
        "in the first column, so static parse may return 0 rows. Fixture fallback."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_paid_product_pages",
                url="https://www.principalam.com/us/fund/pqiax",
                fixture="2025_paid_distributions.html",
                live=True,
            )
        ]


class ThriventSource(HtmlTableSource):
    slug = "thrivent"
    display_name = "Thrivent"
    aum_rank = 33
    priority = 33
    notes = (
        "Public paid capital-gains HTML: "
        "https://www.thriventfunds.com/support/tax-resource-center/capital-gains.html "
        "(e.g. Mid Cap Stock Fund LT $4.02; Global Stock ST $0.35 / LT $2.42; "
        "Large Cap Growth LT $0.76). Advisor reprint: "
        "https://fp.thriventfunds.com/resources/tax-resource-center.html. "
        "Tickers are the public Class S identifiers; the HTML table is fund-level."
    )
    live_limitations = (
        "Family page is public HTML with a 'Thrivent Mutual Fund' header (no ticker column). "
        "Layout can change. Fixture fallback if 0 rows."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_paid_capital_gains",
                url="https://www.thriventfunds.com/support/tax-resource-center/capital-gains.html",
                fixture="2025_paid_capital_gains.html",
                live=True,
            )
        ]


class HartfordSource(HtmlTableSource):
    slug = "hartford"
    display_name = "Hartford Funds"
    aum_rank = 34
    priority = 34
    notes = (
        "Tax center: https://www.hartfordfunds.com/resources/taxcenter.html "
        "Public 10/31/2025 estimate PDF: "
        "https://www.hartfordfunds.com/dam/en/docs/pub/funddocuments/regulatorydocument/"
        "Tax%20Center/HMFCapitalGains_December2025EstimateMemo.pdf "
        "(e.g. MidCap Fund LT $5.36 / 19.67% of Class I NAV; Core Equity LT $6.12 / 10.09%). "
        "Final equity rates (12/11/2025): "
        "https://www.hartfordfunds.com/dam/en/docs/pub/funddocuments/regulatorydocument/"
        "Tax%20Center/capgainsdistributions/2025HartfordFundsCapitalGainsDistributions.pdf."
    )
    live_limitations = "Estimate and final books are PDF. Fixture transcribes the public 10/31 estimate."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_capital_gains",
                url=(
                    "https://www.hartfordfunds.com/dam/en/docs/pub/funddocuments/regulatorydocument/"
                    "Tax%20Center/HMFCapitalGains_December2025EstimateMemo.pdf"
                ),
                fixture="2025_estimated_capital_gains.html",
                live=False,
            )
        ]


class MacquarieSource(HtmlTableSource):
    slug = "macquarie"
    display_name = "Macquarie / Delaware Funds"
    aum_rank = 35
    priority = 35
    notes = (
        "Delaware Funds by Macquarie was renamed Macquarie Funds on 12/31/2024. "
        "Public US retail 2025 estimate PDF (as of 9/30/2025, CGE-RET 2510): "
        "https://mim.fgsfulfillment.com/download.aspx?sku=CGE-RET "
        "(e.g. Science and Technology WSTAX LT $10.051 / 15.05% of Class A NAV; "
        "Large Cap Growth WLGAX LT $3.337 / 8.47%; Value DDVAX LT $3.011 / 20.79%). "
        "Literature hub: https://www.macquarie.com/mam/literature."
    )
    live_limitations = "US estimate book is a fulfillment PDF, not an HTML grid."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_capital_gains",
                url="https://mim.fgsfulfillment.com/download.aspx?sku=CGE-RET",
                fixture="2025_estimated_capital_gains.html",
                live=False,
            )
        ]


class FirstEagleSource(HtmlTableSource):
    slug = "first_eagle"
    display_name = "First Eagle"
    aum_rank = 36
    priority = 36
    notes = (
        "Tax hub: https://www.firsteagle.com/tax-information "
        "Public 9/30/2025 ordinary-income and capital-gains estimate PDF: "
        "https://www.firsteagle.com/sites/default/files/fei-documents/FEF_Ordinary_Income_Gains_Estimates.pdf "
        "(e.g. Global Fund SGENX LT $4.12–$4.17; Overseas Fund SGOVX LT $0.72–$0.77). "
        "Paid per-share history is on product pages, e.g. U.S. Fund "
        "https://www.firsteagle.com/funds/us-fund "
        "(FEVAX 2025-12-05 ST $0.038 / LT $1.683)."
    )
    live_limitations = "Family estimate book is PDF. Fixture transcribes public Class A ranges."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_income_and_gains",
                url="https://www.firsteagle.com/sites/default/files/fei-documents/FEF_Ordinary_Income_Gains_Estimates.pdf",
                fixture="2025_estimated_income_and_gains.html",
                live=False,
            )
        ]


class GmoSource(HtmlTableSource):
    slug = "gmo"
    display_name = "GMO"
    aum_rank = 37
    priority = 37
    notes = (
        "Document library: https://www.gmo.com/americas/document-library/ "
        "Public GMO Trust July 2026 net-income and capital-gain estimate PDF "
        "(release date 6/17/2026): "
        "https://www.gmo.com/globalassets/documents---manually-loaded/documents/"
        "distribution-estimates-and-dates/gmo-trust-funds---july-2026-distribution-estimate.pdf "
        "(e.g. Quality Fund GQETX ST $0.2331 / LT $0.7242; U.S. Equity GMUEX ST $0.3501 / LT $0.7979). "
        "Share classes are institutional Trust classes; the PDF is public and fund-level."
    )
    live_limitations = "Estimate book is PDF. Fixture transcribes public Trust-class rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2026_july_distribution_estimates",
                url=(
                    "https://www.gmo.com/globalassets/documents---manually-loaded/documents/"
                    "distribution-estimates-and-dates/gmo-trust-funds---july-2026-distribution-estimate.pdf"
                ),
                fixture="2026_july_distribution_estimates.html",
                live=False,
            )
        ]


class ArtisanSource(HtmlTableSource):
    slug = "artisan"
    display_name = "Artisan Partners"
    aum_rank = 38
    priority = 38
    notes = (
        "Tax-center distributions HTML: "
        "https://www.artisanpartners.com/individual-investors/resources/tax-center/distributions.html "
        "publishes paid year-to-date income/gain tables (e.g. International Value ARTKX "
        "2026-06-29 income $0.338342; Emerging Markets Debt Opportunities APFOX "
        "2026-01-29 income $0.068306). No family-level 2025/2026 capital-gains *estimate* "
        "PDF was found on 2026-09-07; NRA / DRD PDFs are after-the-fact tax characterization."
    )
    live_limitations = (
        "Live page is public HTML but year-end equity capital-gains sit behind a year selector. "
        "Fixture transcribes current-year paid rows from the public table."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="ytd_paid_distributions",
                url="https://www.artisanpartners.com/individual-investors/resources/tax-center/distributions.html",
                fixture="ytd_paid_distributions.html",
                live=True,
            )
        ]


class CalamosSource(HtmlTableSource):
    slug = "calamos"
    display_name = "Calamos"
    aum_rank = 39
    priority = 39
    notes = (
        "Tax center: https://www.calamos.com/resources/tax-center/ "
        "Public 2025 mutual-fund estimate PDF (snapshot 10/9/2025): "
        "https://www.calamos.com/globalassets/media/documents/tax-center/2025-calamos-estimated-capital-gains.pdf "
        "(e.g. Growth Fund CVGRX LT $4.07 / 7.76% of Class A NAV; Growth and Income "
        "CVTRX ST $0.36 / LT $3.25 / 6.31% of Class A NAV). Record 12/12/2025; "
        "ex/payable 12/15/2025."
    )
    live_limitations = "Estimate book is PDF. Fixture transcribes public Class A rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_capital_gains",
                url="https://www.calamos.com/globalassets/media/documents/tax-center/2025-calamos-estimated-capital-gains.pdf",
                fixture="2025_estimated_capital_gains.html",
                live=False,
            )
        ]


class WasatchSource(HtmlTableSource):
    slug = "wasatch"
    display_name = "Wasatch"
    aum_rank = 40
    priority = 40
    notes = (
        "Public 2025 year-end distribution estimate PDF (composite NAV as of 11/20/2025): "
        "https://wasatchglobal.com/wp-content/uploads/2025/11/WGI_2025_Yr_End_Dist_Estimates.pdf "
        "(e.g. Core Growth WGROX LT $6.01 / 7.71% of NAV; International Growth WAIGX "
        "LT $7.66 / 34.93%). Record 12/17/2025; payable 12/18/2025. "
        "Registered as the Putnam replacement: Putnam.com now redirects to Franklin Templeton "
        "and has no distinct Putnam-branded family estimate book."
    )
    live_limitations = "Estimate book is PDF. Fixture transcribes public Investor-class rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_year_end_distribution_estimates",
                url="https://wasatchglobal.com/wp-content/uploads/2025/11/WGI_2025_Yr_End_Dist_Estimates.pdf",
                fixture="2025_year_end_distribution_estimates.html",
                live=False,
            )
        ]
