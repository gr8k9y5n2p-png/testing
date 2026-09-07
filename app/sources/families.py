from __future__ import annotations

from app.sources.html_source import HtmlTableSource, PageSpec


class BlackRockSource(HtmlTableSource):
    slug = "blackrock"
    display_name = "BlackRock / iShares"
    aum_rank = 1
    priority = 1
    notes = (
        "Parses the public iShares US capital-gains HTML tables (mid-year and year-end "
        "$/share, % of NAV, ex/pay dates). Verified 2026-09-07. Do not use BlackRock "
        "Canada PDFs as the US source."
    )
    live_limitations = "Live HTML on ishares.com/us/capital-gains-distributions is supported."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="ishares_us_capital_gains",
                url="https://www.ishares.com/us/capital-gains-distributions",
                fixture="capital_gains_distributions.html",
                live=True,
            )
        ]


class VanguardSource(HtmlTableSource):
    slug = "vanguard"
    display_name = "Vanguard"
    aum_rank = 2
    priority = 2
    notes = (
        "Fixture parser for the advisor year-end distribution table "
        "(fund / symbol / distribution type / per share / dates). "
        "https://advisors.vanguard.com/tax-center/year-end-distributions is a JS SPA "
        "with no rows in static HTML (verified 2026-09-07). Live fetch falls back to fixtures. "
        "Tax center hub: https://advisors.vanguard.com/tax-center. "
        "Workplace supplemental PDF: "
        "https://workplace.vanguard.com/content/dam/inst/iig-transformation/insights/pdf/2026/ESDF_032026.pdf"
    )
    live_limitations = (
        "Advisor year-end page is JavaScript-rendered; static GET yields 0 rows. "
        "Use fixture mode or POST /ingest/distributions."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="year_end_distributions",
                url="https://advisors.vanguard.com/tax-center/year-end-distributions",
                fixture="year_end_distributions.html",
                live=True,
            )
        ]


class FidelitySource(HtmlTableSource):
    slug = "fidelity"
    display_name = "Fidelity"
    aum_rank = 3
    priority = 3
    notes = (
        "Parses Fidelity Institutional estimated capital-gains HTML "
        "(Symbol/Cusip, ex/pay, % of NAV, ST/LT, total per share, as-of). "
        "Verified 2026-09-07. Hub: https://www.fidelity.com/mutual-funds/information/overview"
    )
    live_limitations = "Live HTML table on institutional.fidelity.com is supported."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="estimated_capital_gains",
                url="https://institutional.fidelity.com/app/tabbed/products/FIIS_SP52_DPL6.html?navId=324",
                fixture="estimated_capital_gains.html",
                live=True,
            )
        ]


class StateStreetSource(HtmlTableSource):
    slug = "state_street"
    display_name = "State Street / SPDR"
    aum_rank = 4
    priority = 4
    notes = (
        "Public estimate page "
        "https://www.ssga.com/us/en/individual/resources/documents/etf-capital-gain-distributions "
        "(as of Oct 31, 2025) is an Angular app — static HTML has {{th.name}} placeholders. "
        "MF companion: .../mf-capital-gain-distributions. Fixture parser covers the published "
        "column layout; live fetch falls back to fixtures."
    )
    live_limitations = (
        "SSGA estimate tables are client-rendered. Fixture mode is the supported path; "
        "replace figures via POST /ingest/distributions when the Angular table is exported."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="etf_capital_gains",
                url="https://www.ssga.com/us/en/individual/resources/documents/etf-capital-gain-distributions",
                fixture="etf_capital_gain_distributions.html",
                live=True,
            )
        ]


class JPMorganSource(HtmlTableSource):
    slug = "jpmorgan"
    display_name = "J.P. Morgan Asset Management"
    aum_rank = 5
    priority = 5
    notes = (
        "Public tax-center HTML 404’d (2026-09-07). Estimates appear in Section 19a PDFs, e.g. "
        "https://am.jpmorgan.com/content/dam/jpm-am-aem/americas/us/en/supplemental/section-19-notices/2025-19a-notice-etfs.pdf "
        "and section-19a-notice-aa-funds-12-2025.pdf. Fixture parser covers that table layout "
        "plus the published Large Cap Growth $9.32525 year-end capital gain."
    )
    live_limitations = "No scrapeable HTML grid; fixture / partner ingest only."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="section_19a_sample",
                url="https://am.jpmorgan.com/content/dam/jpm-am-aem/americas/us/en/supplemental/section-19-notices/section-19a-notice-aa-funds-12-2025.pdf",
                fixture="section_19a_sample.html",
                live=False,
            )
        ]


class GoldmanSachsSource(HtmlTableSource):
    slug = "goldman_sachs"
    display_name = "Goldman Sachs Asset Management"
    aum_rank = 6
    priority = 6
    notes = (
        "Document library: "
        "https://www.gsam.com/content/gsam/us/en/advisors/literature-and-forms/forms-and-tax-center.html "
        "Advisor tax-center HTML returned 403 (2026-09-07); estimates are typically Q4 PDFs. "
        "Fixture parser uses the GSAM table layout plus the public 2025 year-end distribution "
        "for Large Cap Growth Insights (GLCGX)."
    )
    live_limitations = "Advisor tax center is login/403-walled. Use fixtures or POST /ingest/distributions."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="year_end_sample",
                url="https://www.gsam.com/content/gsam/us/en/advisors/literature-and-forms/forms-and-tax-center.html",
                fixture="year_end_distributions_sample.html",
                live=False,
            )
        ]


class PimcoSource(HtmlTableSource):
    slug = "pimco"
    display_name = "PIMCO"
    aum_rank = 8
    priority = 8
    notes = (
        "Public hub https://www.pimco.com/us/en/resources/tax-center (verified 2026-09-07). "
        "Year-end forms: https://www.pimco.com/us/en/resources/tax-center/2025-tax-information-and-year-end-forms. "
        "Preliminary estimate grids are PDF / Section 19 notices, not a scrapeable HTML table. "
        "Fixture is a layout sample (synthetic tickers ZZPIMI/ZZPIMB). Partner ingest is the "
        "escape hatch for official notices."
    )
    live_limitations = "No public HTML estimate table; fixture parser + POST /ingest/distributions."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="tax_center_sample",
                url="https://www.pimco.com/us/en/resources/tax-center",
                fixture="tax_center_sample.html",
                live=False,
            )
        ]


class InvescoSource(HtmlTableSource):
    slug = "invesco"
    display_name = "Invesco"
    aum_rank = 9
    priority = 9
    notes = (
        "Mutual-fund estimates are a public PDF: "
        "https://www.invesco.com/content/dam/invesco/us/en/documents/tax-centre/2025%20Invesco%20Estimated%20Capital%20Gains%20pdf.pdf "
        "(American Franchise LT $2.89 / 8.55% of NAV, etc.). ETF estimates via the 20 Nov 2025 "
        "press release. Fixture HTML transcribes those tables; live PDF is not HTML-parsed."
    )
    live_limitations = "Estimates are PDF/PR, not an HTML grid. Fixture mode transcribes the public PDF."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="estimated_capital_gains_pdf",
                url="https://www.invesco.com/content/dam/invesco/us/en/documents/tax-centre/2025%20Invesco%20Estimated%20Capital%20Gains%20pdf.pdf",
                fixture="2025_estimated_capital_gains.html",
                live=False,
            )
        ]


class TRowePriceSource(HtmlTableSource):
    slug = "t_rowe_price"
    display_name = "T. Rowe Price"
    aum_rank = 10
    priority = 10
    notes = (
        "Parses public year-end HTML tables "
        "(ticker, income dividends, ST/LT) at "
        "https://www.troweprice.com/personal-investing/resources/planning/tax/dividend-distributions/mutual-funds/2025-year-end-distributions.html "
        "plus public archives for 2024 and 2023 (same path, year in the filename). "
        "Verified 2026-09-07; e.g. TRBCX LT $10.9575 (2025), $16.1515 (2024), $5.2095 (2023)."
    )
    live_limitations = "Live year-end HTML is supported for 2023–2025. Preliminary estimate pages may be intermediary-only."

    def pages(self) -> list[PageSpec]:
        base = (
            "https://www.troweprice.com/personal-investing/resources/planning/tax/"
            "dividend-distributions/mutual-funds"
        )
        return [
            PageSpec(
                name="year_end_2025",
                url=f"{base}/2025-year-end-distributions.html",
                fixture="2025_year_end_distributions.html",
                live=True,
            ),
            PageSpec(
                name="year_end_2024",
                url=f"{base}/2024-year-end-distributions.html",
                fixture="2024_year_end_distributions.html",
                live=True,
            ),
            PageSpec(
                name="year_end_2023",
                url=f"{base}/2023-year-end-distributions.html",
                fixture="2023_year_end_distributions.html",
                live=True,
            ),
        ]
