from __future__ import annotations

from app.sources.html_source import HtmlTableSource, PageSpec


class BlackRockSource(HtmlTableSource):
    slug = "blackrock"
    display_name = "BlackRock / iShares"
    aum_rank = 1
    priority = 1
    notes = (
        "iShares US ETF capital-gains HTML "
        "https://www.ishares.com/us/capital-gains-distributions "
        "(every fund on the mid-year and year-end tables; $/share, % of NAV, ex/pay) plus the "
        "BlackRock open-end mutual-fund 2025 distribution book "
        "https://www.blackrock.com/us/individual/resources/tax-information/2025-distributions "
        "(Investor A when listed). Mutual funds + ETFs only; SMAs skipped. Table captions "
        "set publication_stage: mid-year paid vs year-end final. Verified 2026-09-07. "
        "Do not use BlackRock Canada PDFs as the US source. "
        "Prior-year archives are 1099-style PDFs in the tax kits "
        "(2024: https://www.ishares.com/us/library/2024-tax-kit ; "
        "2023: https://www.ishares.com/us/literature/tax-information/2023-ishares-distribution-summary-stamped.pdf) "
        "— not an HTML CG grid, so they are not fixture-transcribed. "
        "No public ICI Primary Layout download was found on the iShares tax library."
    )
    live_limitations = "Live HTML on ishares.com/us/capital-gains-distributions is supported. 2023–2024 YE archives are PDF tax kits, not scrapeable HTML."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="ishares_us_capital_gains",
                url="https://www.ishares.com/us/capital-gains-distributions",
                fixture="capital_gains_distributions.html",
                live=True,
            ),
            PageSpec(
                name="2025_open_end_distributions",
                url="https://www.blackrock.com/us/individual/resources/tax-information/2025-distributions",
                fixture="2025_open_end_distributions.html",
                live=False,
            ),
        ]


class VanguardSource(HtmlTableSource):
    slug = "vanguard"
    display_name = "Vanguard"
    aum_rank = 2
    priority = 2
    notes = (
        "ICI Primary Layout is the preferred source for historical + ongoing "
        "Vanguard books (not the JS year-end SPA). Official PDFs: "
        "2025 https://advisors.vanguard.com/content/dam/fas/pdfs/ICIprimary_012026.pdf "
        "2024 https://advisors.vanguard.com/content/dam/fas/pdfs/ICI_revised_2024_Primary_layout_spreadsheet.pdf "
        "2023 https://advisors.vanguard.com/content/dam/fas/pdfs/2023_ICI_Primary_Layout.pdf "
        "2022 https://advisors.vanguard.com/content/dam/fas/pdfs/2022_ICI_Primary_Layout.pdf "
        "2021 https://advisors.vanguard.com/content/dam/fas/pdfs/2021_ICI_Primary_Layout.pdf. "
        "2025 ICI is a column-safe full December book (31-token layout; "
        "VFIAX / VBIAX / VIGAX omitted so the YE HTML fixture "
        "is not double-counted). 2024 ICI is the same full-December extract "
        "(includes VFIAX / VBIAX / VIGAX). 2021–2023 ICI CSVs remain flagship-only. "
        "Tax center hub: https://advisors.vanguard.com/tax-center."
    )
    live_limitations = (
        "Advisor year-end page is JavaScript-rendered; ICI archives are PDFs "
        "(fixture transcription). Use fixture mode or POST /ingest/distributions."
    )

    def pages(self) -> list[PageSpec]:
        ici = "https://advisors.vanguard.com/content/dam/fas/pdfs"
        return [
            PageSpec(
                name="year_end_distributions",
                url="https://advisors.vanguard.com/tax-center/year-end-distributions",
                fixture="year_end_distributions.html",
                live=True,
            ),
            PageSpec(
                name="ici_primary_2025",
                url=f"{ici}/ICIprimary_012026.pdf",
                fixture="ici_primary_2025.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
            ),
            PageSpec(
                name="ici_primary_2024",
                url=f"{ici}/ICI_revised_2024_Primary_layout_spreadsheet.pdf",
                fixture="ici_primary_2024.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
            ),
            PageSpec(
                name="ici_primary_2023",
                url=f"{ici}/2023_ICI_Primary_Layout.pdf",
                fixture="ici_primary_2023.csv",
                live=False,
                parser="ici",
                large_aum_only=True,
            ),
            PageSpec(
                name="ici_primary_2022",
                url=f"{ici}/2022_ICI_Primary_Layout.pdf",
                fixture="ici_primary_2022.csv",
                live=False,
                parser="ici",
                large_aum_only=True,
            ),
            PageSpec(
                name="ici_primary_2021",
                url=f"{ici}/2021_ICI_Primary_Layout.pdf",
                fixture="ici_primary_2021.csv",
                live=False,
                parser="ici",
                large_aum_only=True,
            ),
        ]


class FidelitySource(HtmlTableSource):
    slug = "fidelity"
    display_name = "Fidelity"
    aum_rank = 3
    priority = 3
    notes = (
        "Parses Fidelity Institutional estimated capital-gains HTML "
        "(Symbol/Cusip, ex/pay, % of NAV, ST/LT, total per share, as-of) "
        "plus the public prior-year paid table "
        "https://institutional.fidelity.com/app/tabbed/products/FIIS_SP10_DPL6.html?navId=324 "
        "(full book: Dividends / ST / LT / Reinvest NAV). "
        "Verified 2026-09-07. FBGRX 2026 estimate LT $21.021 (as of 2026-07-31) "
        "coexists with 2025 paid LT $5.07300 (ex 2025-09-12). "
        "Hub: https://www.fidelity.com/mutual-funds/information/overview"
    )
    live_limitations = "Live HTML tables on institutional.fidelity.com are supported (current estimates + prior-year paid)."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="estimated_capital_gains",
                url="https://institutional.fidelity.com/app/tabbed/products/FIIS_SP52_DPL6.html?navId=324",
                fixture="estimated_capital_gains.html",
                live=True,
            ),
            PageSpec(
                name="prior_year_distributions",
                url="https://institutional.fidelity.com/app/tabbed/products/FIIS_SP10_DPL6.html?navId=324",
                fixture="prior_year_distributions.html",
                live=True,
            ),
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
        "column layout; live fetch falls back to fixtures. "
        "The dividend-distributions page links a Historical Distributions XLSX, but that "
        "file has no stable public URL (Angular). 2024 paid ST/LT for SPY/SPLG were not "
        "transcribed without a fetchable official file."
    )
    live_limitations = (
        "SSGA estimate tables are client-rendered. Historical XLSX is not a stable public "
        "file URL. Fixture mode is the supported path; replace figures via POST /ingest/distributions."
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
        "and section-19a-notice-aa-funds-12-2025.pdf. The 2025 fixture is the full Appendix A "
        "from both notices (unsplit estimated CG $/share). SEEGX / JLGMX keep the previously "
        "identified Large Cap Growth long-term mapping ($9.32525). "
        "No official 2024 (or earlier) $/share 19a HTML/PDF with SEEGX amounts was "
        "confirmed on this pass — third-party histories are not used."
    )
    live_limitations = "No scrapeable HTML grid; 2024+ archives not confirmed as public $/share PDFs. Fixture / partner ingest only."

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
        "for Large Cap Growth Insights (GLCGX). Prior-year advisor archives remain 403-walled."
    )
    live_limitations = "Advisor tax center is login/403-walled (including historical packs). Use fixtures or POST /ingest/distributions."

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
        "Fixture is a layout sample (synthetic tickers ZZPIMI/ZZPIMB) — no additional "
        "tax years are invented. Partner ingest is the escape hatch for official notices."
    )
    live_limitations = "No public HTML estimate table or scrapeable multi-year archive; fixture parser + POST /ingest/distributions."

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
        "Mutual-fund estimates are public PDFs / In Focus pages. "
        "2025: https://www.invesco.com/content/dam/invesco/us/en/documents/tax-centre/2025%20Invesco%20Estimated%20Capital%20Gains%20pdf.pdf "
        "(American Franchise LT $2.89 / 8.55% of NAV). "
        "2024: https://www.invesco.com/us-rest/contentdetail?contentId=29096ee0-8ec4-4199-930f-645be9d07e64 "
        "(as of 2024-09-30; American Franchise LT $0.93 / 3.29% of NAV). "
        "ETF estimates via the 20 Nov 2025 press-release table (full listed ETFs). "
        "2025 MF fixture is the full paying-fund PDF table (names; no MF tickers; "
        "SMA High Yield Bond skipped). "
        "Invesco lists ICI Primary distribution files on "
        "https://www.invesco.com/us/en/accounts/tax-center/open-end-tax-guide.html "
        "(2023–2025 most funds / REIT / SteelPath). No stable public file URL "
        "was fetchable from this environment (JS / 406) — PDF/HTML archives remain "
        "the supported path until an ICI download URL is confirmed."
    )
    live_limitations = "Estimates are PDF/PR/contentdetail, not an HTML grid. Fixture mode transcribes the public tables."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="estimated_capital_gains_pdf",
                url="https://www.invesco.com/content/dam/invesco/us/en/documents/tax-centre/2025%20Invesco%20Estimated%20Capital%20Gains%20pdf.pdf",
                fixture="2025_estimated_capital_gains.html",
                live=False,
            ),
            PageSpec(
                name="estimated_capital_gains_2024",
                url="https://www.invesco.com/us-rest/contentdetail?contentId=29096ee0-8ec4-4199-930f-645be9d07e64",
                fixture="2024_estimated_capital_gains.html",
                live=False,
            ),
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
        "2022 year-end and 2022 preliminary are official PDFs (no 2022 HTML sibling): "
        "https://www.troweprice.com/content/dam/fai/Funds/Tax_Center/2022-Year-End-Tax-Distributions.pdf "
        "and .../T.%20Rowe%20Price%202022%20Preliminary%20Estimated%20Distributions%20as%20of%2010.31.2022.pdf. "
        "2023–2025 fixtures are the full public YE HTML books. "
        "Verified 2026-09-07; e.g. TRBCX LT $10.9575 (2025), $16.1515 (2024), $5.2095 (2023), "
        "$6.0394 final / $5.75 prelim (2022). 2022 remains PDF flagship transcription."
    )
    live_limitations = "Live year-end HTML is supported for 2023–2025. 2022 packs are PDF transcriptions (live=False)."

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
            PageSpec(
                name="year_end_2022",
                url="https://www.troweprice.com/content/dam/fai/Funds/Tax_Center/2022-Year-End-Tax-Distributions.pdf",
                fixture="2022_year_end_distributions.html",
                live=False,
            ),
            PageSpec(
                name="prelim_2022",
                url=(
                    "https://www.troweprice.com/content/dam/fai/Funds/Tax_Center/"
                    "T.%20Rowe%20Price%202022%20Preliminary%20Estimated%20Distributions%20as%20of%2010.31.2022.pdf"
                ),
                fixture="2022_preliminary_estimated_distributions.html",
                live=False,
            ),
        ]
