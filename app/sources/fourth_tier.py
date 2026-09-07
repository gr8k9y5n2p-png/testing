from __future__ import annotations

from app.sources.html_source import HtmlTableSource, PageSpec


class JohnHancockSource(HtmlTableSource):
    slug = "john_hancock"
    display_name = "John Hancock / Manulife"
    aum_rank = 31
    priority = 31
    notes = (
        "US John Hancock Investments book (Manulife parent). No public filled ICI. "
        "Press-release estimate PDFs still posted: 2025 "
        "https://www.jhinvestments.com/content/dam/jhi-investments/JHINV/public/Corporate/News/"
        "CorporatePressReleases/estimated-capital-gain-and-income-distribution-press-release-2025-jhi.pdf "
        "is the full paying-fund CG table (TAGRX LT $6.85–$7.60; mutual funds + "
        "ETFs only — closed-end rows skipped; all-dash omitted). Plus 2024 / 2023 / 2022 "
        "sibling filenames (TAGRX LT $7.80–$8.80 / $3.60–$4.10 / $3.00–$3.60). USGLX listed "
        "em-dashes in 2022–2023 (no CG — omitted, not stored as $0). "
        "HTML press-release shells are viewers; the PDFs are the books."
    )
    live_limitations = (
        "Family book is a PDF (press-release HTML is a viewer/shell). Fixture transcribes public A-share ranges."
    )

    def pages(self) -> list[PageSpec]:
        press = (
            "https://www.jhinvestments.com/content/dam/jhi-investments/JHINV/public/"
            "Corporate/News/CorporatePressReleases/"
        )
        return [
            PageSpec(
                name="2025_estimated_capital_gains",
                url=press + "estimated-capital-gain-and-income-distribution-press-release-2025-jhi.pdf",
                fixture="2025_estimated_capital_gains.html",
                live=False,
            ),
            PageSpec(
                name="2024_estimated_capital_gains",
                url=press + "estimated-capital-gain-and-income-distribution-press-release-2024-jhi.pdf",
                fixture="2024_estimated_capital_gains.html",
                live=False,
                large_aum_only=True,
            ),
            PageSpec(
                name="2023_estimated_capital_gains",
                url=press + "estimated-capital-gain-and-income-distribution-press-release-2023-jhi.pdf",
                fixture="2023_estimated_capital_gains.html",
                live=False,
                large_aum_only=True,
            ),
            PageSpec(
                name="2022_estimated_capital_gains",
                url=press + "estimated-capital-gain-and-income-distribution-press-release-2022-jhi.pdf",
                fixture="2022_estimated_capital_gains.html",
                live=False,
                large_aum_only=True,
            ),
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
        "No public filled ICI. Public 10/31/2025 estimate PDF: "
        "https://www.hartfordfunds.com/dam/en/docs/pub/funddocuments/regulatorydocument/"
        "Tax%20Center/HMFCapitalGains_December2025EstimateMemo.pdf "
        "is the full paying-fund book (MidCap HFMCX LT $5.36 / 19.67% of Class I NAV; "
        "no-pay list omitted). Final books under .../capgainsdistributions/: 2025 equity "
        "2025HartfordFundsCapitalGainsDistributions.pdf (HFMCX LT $5.44), 2025 "
        "fixed-income / multi-strategy HartfordFundsCapitalGainsDistributions-12.17.2025.pdf, "
        "and 2024 2024HartfordFundsCapitalGainsDistributions.pdf (HFMCX LT $1.67). "
        "Amounts are fund-level; tickers are public Class A identifiers only where "
        "previously identified."
    )
    live_limitations = "Estimate and final books are PDF. Fixture transcribes the public 10/31 estimate plus finals."

    def pages(self) -> list[PageSpec]:
        dam = (
            "https://www.hartfordfunds.com/dam/en/docs/pub/funddocuments/regulatorydocument/"
        )
        return [
            PageSpec(
                name="2025_estimated_capital_gains",
                url=dam + "Tax%20Center/HMFCapitalGains_December2025EstimateMemo.pdf",
                fixture="2025_estimated_capital_gains.html",
                live=False,
            ),
            PageSpec(
                name="2025_final_capital_gains",
                url=dam + "Tax%20Center/capgainsdistributions/2025HartfordFundsCapitalGainsDistributions.pdf",
                fixture="2025_final_capital_gains.html",
                live=False,
            ),
            PageSpec(
                name="2025_final_fixed_income",
                url=dam + "Tax%20Center/capgainsdistributions/HartfordFundsCapitalGainsDistributions-12.17.2025.pdf",
                fixture="2025_final_fixed_income.html",
                live=False,
            ),
            PageSpec(
                name="2024_final_capital_gains",
                url=dam + "Tax%20Center/capgainsdistributions/2024HartfordFundsCapitalGainsDistributions.pdf",
                fixture="2024_final_capital_gains.html",
                live=False,
                large_aum_only=True,
            ),
        ]


class MacquarieSource(HtmlTableSource):
    slug = "macquarie"
    display_name = "Macquarie / Delaware Funds"
    aum_rank = 35
    priority = 35
    notes = (
        "US Delaware / Macquarie Funds book only (Australian parent; do not ingest "
        "non-US Macquarie trusts). Renamed Macquarie Funds on 12/31/2024. "
        "No public filled ICI. Public US retail 2025 estimate PDF "
        "https://mim.fgsfulfillment.com/download.aspx?sku=CGE-RET "
        "is the full paying-fund book (WSTAX LT $10.051 / 15.05% of Class A NAV; "
        "Class A tickers; no-pay list omitted). 2024 paid book "
        "https://mim.fgsfulfillment.com/download.aspx?sku=CGE-RET-ACT-2024 "
        "(WSTAX ST $1.108 / LT $8.135). Literature hub: "
        "https://www.macquarie.com/mam/literature."
    )
    live_limitations = "US estimate/paid books are fulfillment PDFs, not an HTML grid."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_capital_gains",
                url="https://mim.fgsfulfillment.com/download.aspx?sku=CGE-RET",
                fixture="2025_estimated_capital_gains.html",
                live=False,
            ),
            PageSpec(
                name="2024_paid_capital_gains",
                url="https://mim.fgsfulfillment.com/download.aspx?sku=CGE-RET-ACT-2024",
                fixture="2024_paid_capital_gains.html",
                live=False,
                large_aum_only=True,
            ),
        ]


class FirstEagleSource(HtmlTableSource):
    slug = "first_eagle"
    display_name = "First Eagle"
    aum_rank = 36
    priority = 36
    notes = (
        "Tax hub: https://www.firsteagle.com/tax-information "
        "No public filled ICI. Public 9/30/2025 estimate PDF: "
        "https://www.firsteagle.com/sites/default/files/fei-documents/FEF_Ordinary_Income_Gains_Estimates.pdf "
        "(SGENX LT $4.12–$4.17). Paid YE from the 2024 official PDF "
        "https://www.firsteagle.com/sites/default/files/2024-12/2024_Capital_Gains_%20Income_Distributions.pdf "
        "(SGENX ST $0.027 / LT $2.038) and product-page history "
        "https://www.firsteagle.com/funds/global-fund (SGENX 2025 LT $4.654 / "
        "2023 LT $1.407), overseas-fund (SGOVX), and us-fund (FEVAX). "
        "2025 family paid PDF URL was not a stable public file in this environment."
    )
    live_limitations = "Family estimate book is PDF. Paid history is on public product pages."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_income_and_gains",
                url="https://www.firsteagle.com/sites/default/files/fei-documents/FEF_Ordinary_Income_Gains_Estimates.pdf",
                fixture="2025_estimated_income_and_gains.html",
                live=False,
            ),
            PageSpec(
                name="2025_paid_year_end",
                url="https://www.firsteagle.com/funds/global-fund",
                fixture="2025_paid_year_end.html",
                live=False,
                large_aum_only=True,
            ),
            PageSpec(
                name="2024_paid_year_end",
                url="https://www.firsteagle.com/sites/default/files/2024-12/2024_Capital_Gains_%20Income_Distributions.pdf",
                fixture="2024_paid_year_end.html",
                live=False,
                large_aum_only=True,
            ),
            PageSpec(
                name="2023_paid_year_end",
                url="https://www.firsteagle.com/funds/global-fund",
                fixture="2023_paid_year_end.html",
                live=False,
                large_aum_only=True,
            ),
        ]


class GmoSource(HtmlTableSource):
    slug = "gmo"
    display_name = "GMO"
    aum_rank = 37
    priority = 37
    notes = (
        "US GMO Trust book only — skip GMO Australia unit-trust estimates. "
        "No public filled ICI. Document library: "
        "https://www.gmo.com/americas/document-library/ "
        "Public GMO Trust July 2026 net-income and capital-gain estimate PDF "
        "(release date 6/17/2026): "
        "https://www.gmo.com/globalassets/documents---manually-loaded/documents/"
        "distribution-estimates-and-dates/gmo-trust-funds---july-2026-distribution-estimate.pdf "
        "(Quality Fund GQETX ST $0.2331 / LT $0.7242). July/December 2025 "
        "sibling filenames 404 — single-vintage, not invented."
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
        "2026-06-29 income $0.338342). No family-level 2025/2026 capital-gains *estimate* "
        "PDF was found. Year selector for 2024/2025 YE is JavaScript — skip SPA. "
        "NRA PDFs (Nonresident-Alien-Reporting-2024/2025.pdf) are FIRPTA / ICI "
        "tax-character layouts, not full ST/LT $/share — not ingested as CG."
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
        "No public filled ICI. Public 2025 mutual-fund estimate PDF "
        "(snapshot 10/9/2025): "
        "https://www.calamos.com/globalassets/media/documents/tax-center/2025-calamos-estimated-capital-gains.pdf "
        "(Growth Fund CVGRX LT $4.07 / 7.76% of Class A NAV). 2024 sibling "
        "2024-calamos-estimated-capital-gains.pdf (CVGRX ST $1.24 / LT $1.84). "
        "2023 sibling filename 404."
    )
    live_limitations = "Estimate book is PDF. Fixture transcribes public Class A rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_capital_gains",
                url="https://www.calamos.com/globalassets/media/documents/tax-center/2025-calamos-estimated-capital-gains.pdf",
                fixture="2025_estimated_capital_gains.html",
                live=False,
            ),
            PageSpec(
                name="2024_estimated_capital_gains",
                url="https://www.calamos.com/globalassets/media/documents/tax-center/2024-calamos-estimated-capital-gains.pdf",
                fixture="2024_estimated_capital_gains.html",
                live=False,
                large_aum_only=True,
            ),
        ]


class WasatchSource(HtmlTableSource):
    slug = "wasatch"
    display_name = "Wasatch"
    aum_rank = 40
    priority = 40
    notes = (
        "No public filled ICI. Public 2025 year-end distribution estimate PDF "
        "(composite NAV as of 11/20/2025): "
        "https://wasatchglobal.com/wp-content/uploads/2025/11/WGI_2025_Yr_End_Dist_Estimates.pdf "
        "(Core Growth WGROX LT $6.01 / 7.71% of NAV). 2024 estimate sibling "
        "WGI_2024_Yr_End_Dist_Estimates.pdf 404. Paid YE from "
        "https://wasatchglobal.com/wasatch-core-growth-fund-investor/ "
        "(WGROX 2025 LT $6.345749; 2024 LT $8.282696; 2022 LT $0.457965). "
        "Product page has no 2023 YE row — gap, not invented. "
        "Registered as the Putnam replacement: Putnam.com now redirects to Franklin Templeton."
    )
    live_limitations = "Estimate book is PDF. Paid history is on the public product page."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_year_end_distribution_estimates",
                url="https://wasatchglobal.com/wp-content/uploads/2025/11/WGI_2025_Yr_End_Dist_Estimates.pdf",
                fixture="2025_year_end_distribution_estimates.html",
                live=False,
            ),
            PageSpec(
                name="2025_paid_year_end",
                url="https://wasatchglobal.com/wasatch-core-growth-fund-investor/",
                fixture="2025_paid_year_end.html",
                live=False,
                large_aum_only=True,
            ),
            PageSpec(
                name="2024_paid_year_end",
                url="https://wasatchglobal.com/wasatch-core-growth-fund-investor/",
                fixture="2024_paid_year_end.html",
                live=False,
                large_aum_only=True,
            ),
            PageSpec(
                name="2022_paid_year_end",
                url="https://wasatchglobal.com/wasatch-core-growth-fund-investor/",
                fixture="2022_paid_year_end.html",
                live=False,
                large_aum_only=True,
            ),
        ]
