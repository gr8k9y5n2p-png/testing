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
        "BlackRock open-end mutual-fund distribution books "
        "https://www.blackrock.com/us/individual/resources/tax-information/2025-distributions "
        "(and the 2024 / 2023 / 2022 / 2021 HTML siblings). Investor A when listed. Mutual funds + ETFs "
        "only; SMAs and Variable Series skipped. Live 2021–2024 pages are per-fund share-class tables "
        "(no ticker column) — fixtures flatten November–December YE Investor A rows. "
        "Investor A tickers are backfilled from ``app/aliases_blackrock.py`` without "
        "changing name-slug upsert keys (Equity Dividend Investor A MDDVX). "
        "Equity Dividend Investor A LT $1.089256 (2021) / $0.740291 (2022) / "
        "$0.481929 (2023) / $0.728360 (2024) / $0.999925 (2025). "
        "iShares 2023–2024 tax kits remain 1099-style PDFs, not an ETF HTML CG grid. "
        "No public ICI Primary Layout download was found on the iShares tax library."
    )
    live_limitations = (
        "Live HTML on ishares.com/us/capital-gains-distributions is supported. "
        "Open-end 2021–2025 tax-information HTML is public but not column-safe "
        "(h3 + share-class tables); fixtures are flattened November–December YE books."
    )

    def pages(self) -> list[PageSpec]:
        tax = "https://www.blackrock.com/us/individual/resources/tax-information"
        return [
            PageSpec(
                name="ishares_us_capital_gains",
                url="https://www.ishares.com/us/capital-gains-distributions",
                fixture="capital_gains_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_open_end_distributions",
                url=f"{tax}/2025-distributions",
                fixture="2025_open_end_distributions.html",
                live=False,
            ),
            PageSpec(
                name="2024_open_end_distributions",
                url=f"{tax}/2024-distributions",
                fixture="2024_open_end_distributions.html",
                live=False,
            ),
            PageSpec(
                name="2023_open_end_distributions",
                url=f"{tax}/2023-distributions",
                fixture="2023_open_end_distributions.html",
                live=False,
            ),
            PageSpec(
                name="2022_open_end_distributions",
                url=f"{tax}/2022-distributions",
                fixture="2022_open_end_distributions.html",
                live=False,
            ),
            PageSpec(
                name="2021_open_end_distributions",
                url=f"{tax}/2021-distributions",
                fixture="2021_open_end_distributions.html",
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
        "2021–2025 ICI files are column-safe full December books (31-token "
        "layout: income / ST / LT at tokens 4 / 5 / 12). 2025 omits "
        "VFIAX / VBIAX / VIGAX so the YE HTML fixture is not double-counted. "
        "2024 includes those three. Quarterly ICI lines are not stored. "
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
                name="tax_center_hub",
                url="https://advisors.vanguard.com/tax-center",
                fixture="tax_center_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="year_end_distributions",
                url="https://advisors.vanguard.com/tax-center/year-end-distributions",
                fixture="year_end_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
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
                large_aum_only=False,
            ),
            PageSpec(
                name="ici_primary_2022",
                url=f"{ici}/2022_ICI_Primary_Layout.pdf",
                fixture="ici_primary_2022.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
            ),
            PageSpec(
                name="ici_primary_2021",
                url=f"{ici}/2021_ICI_Primary_Layout.pdf",
                fixture="ici_primary_2021.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
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
        "coexists with 2025 paid LT $5.07300 (ex 2025-09-12) and the full 2024 "
        "paid DPL6 book from the Wayback id_ snapshot captured 2025-03-21 "
        "(FBGRX Dec LT $1.66900 / Sep LT $11.08100; FCNTX Dec LT $0.85500; "
        "FDGRX Dec LT $3.57500; 350 tickers). "
        "2021–2023 prior-year HTML is not in the CDX set (HPDY tool is SPA). "
        "Hub: https://www.fidelity.com/mutual-funds/information/overview"
    )
    live_limitations = "Live HTML tables on institutional.fidelity.com are supported (current estimates + prior-year paid). The live DPL6 URL rotates to the latest prior year — 2024 is fixture-only."

    def pages(self) -> list[PageSpec]:
        dpl6 = "https://institutional.fidelity.com/app/tabbed/products/FIIS_SP10_DPL6.html?navId=324"
        return [
            PageSpec(
                name="estimated_capital_gains",
                url="https://institutional.fidelity.com/app/tabbed/products/FIIS_SP52_DPL6.html?navId=324",
                fixture="estimated_capital_gains.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="prior_year_distributions",
                url=dpl6,
                fixture="prior_year_distributions.html",
                live=True,
            ),
            PageSpec(
                name="prior_year_distributions_2024",
                url=dpl6,
                fixture="prior_year_distributions_2024.html",
                live=False,
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
        "MF companion: .../mf-capital-gain-distributions. Live estimate fetch falls back "
        "to fixtures (SPY/SPLG 0% NAV placeholders + ZZSSGA parser sample). "
        "Official paid history is the public XLSX "
        "https://www.ssga.com/library-content/products/fund-data/etfs/us/spdr-etf-historical-distributions.xlsx "
        "(verified 2026-09-08; 2021–2025 December / annual rows that publish a ST or LT "
        "cell, including official $0.000000). SPLG was renamed SPYM on 10/31/2025."
    )
    live_limitations = (
        "SSGA estimate tables are client-rendered Angular. Historical XLSX is public but "
        "not HTML — fixtures transcribe the paid YE book. Replace live estimates via "
        "POST /ingest/distributions."
    )

    def pages(self) -> list[PageSpec]:
        xlsx = (
            "https://www.ssga.com/library-content/products/fund-data/etfs/us/"
            "spdr-etf-historical-distributions.xlsx"
        )
        return [
            PageSpec(
                name="etf_capital_gains",
                url="https://www.ssga.com/us/en/individual/resources/documents/etf-capital-gain-distributions",
                fixture="etf_capital_gain_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="mf_capital_gains",
                url="https://www.ssga.com/us/en/individual/resources/documents/mf-capital-gain-distributions",
                fixture="mf_capital_gain_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_historical_distributions",
                url=xlsx,
                fixture="2025_historical_distributions.html",
                live=False,
            ),
            PageSpec(
                name="2024_historical_distributions",
                url=xlsx,
                fixture="2024_historical_distributions.html",
                live=False,
            ),
            PageSpec(
                name="2023_historical_distributions",
                url=xlsx,
                fixture="2023_historical_distributions.html",
                live=False,
            ),
            PageSpec(
                name="2022_historical_distributions",
                url=xlsx,
                fixture="2022_historical_distributions.html",
                live=False,
            ),
            PageSpec(
                name="2021_historical_distributions",
                url=xlsx,
                fixture="2021_historical_distributions.html",
                live=False,
            ),
        ]


class JPMorganSource(HtmlTableSource):
    slug = "jpmorgan"
    display_name = "J.P. Morgan Asset Management"
    aum_rank = 5
    priority = 5
    notes = (
        "Public tax-center HTML 404’d (2026-09-07). Estimates appear in Section 19a PDFs, e.g. "
        "https://am.jpmorgan.com/content/dam/jpm-am-aem/americas/us/en/supplemental/section-19-notices/2025-19a-notice-etfs.pdf "
        "and section-19a-notice-aa-funds-12-2025.pdf plus the money-market notice "
        "mutual-funds-annual-section-19a-notice-mmkt.pdf (four municipal MMKT LT "
        "amounts). The 2025 fixture is the full Appendix A from those notices "
        "(unsplit estimated CG $/share on open-end + ETF; LT $/share on MMKT). "
        "SEEGX / JLGMX keep the previously identified Large Cap Growth long-term "
        "mapping ($9.32525). Other Appendix A names stay slug-keyed; Class A / ETF / "
        "Morgan money-market tickers are backfilled from ``app/aliases_jpmorgan.py`` "
        "(Equity Income Class A OIEIX; BetaBuilders EM BBEM). Mutual funds + ETFs only. "
        "Official 2024 Section 19a Appendix A PDFs "
        "section-19a-notice-mutual-funds-dec-13-2024.pdf and "
        "section-19a-etf-notice-12-2024.pdf publish unsplit estimated CG $/share "
        "(SEEGX / JLGMX 2024 LT mapping $0.79868). 2023 sibling 19a URLs 404."
    )
    live_limitations = "No scrapeable HTML grid; 19a books are PDF. Fixture / partner ingest only."

    def pages(self) -> list[PageSpec]:
        notices = (
            "https://am.jpmorgan.com/content/dam/jpm-am-aem/americas/us/en/"
            "supplemental/section-19-notices"
        )
        return [
            PageSpec(
                name="section_19a_sample",
                url=f"{notices}/section-19a-notice-aa-funds-12-2025.pdf",
                fixture="section_19a_sample.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2024_section_19a",
                url=f"{notices}/section-19a-notice-mutual-funds-dec-13-2024.pdf",
                fixture="2024_section_19a.html",
                live=False,
            ),
        ]


class GoldmanSachsSource(HtmlTableSource):
    slug = "goldman_sachs"
    display_name = "Goldman Sachs Asset Management"
    aum_rank = 6
    priority = 6
    notes = (
        "Document library: "
        "https://www.gsam.com/content/gsam/us/en/advisors/literature-and-forms/forms-and-tax-center.html "
        "Advisor tax-center HTML returned 403 (2026-09-07 and 2026-09-08) and 200 with no "
        "ST/LT table on 2026-09-08 (literature library / no estimate grid). Weekly refresh "
        "walks the hub anyway. Estimates are typically Q4 PDFs. Fixture parser uses the GSAM "
        "table layout plus the public 2025 year-end distribution for Large Cap Growth Insights "
        "(GLCGX). Prior-year advisor archives remain walled — deferred, not invented."
    )
    live_limitations = "Advisor tax center is login/403-walled (including historical packs). Use fixtures or POST /ingest/distributions."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="year_end_sample",
                url="https://www.gsam.com/content/gsam/us/en/advisors/literature-and-forms/forms-and-tax-center.html",
                fixture="year_end_distributions_sample.html",
                live=True,
                role="estimate",
                empty_ok=True,
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
        "Re-checked 2026-09-08: tax-center document hash served an SAI/prospectus "
        "supplement (not ST/LT $/share). The 2025 tax-information PDF remains 1099 "
        "character (muni taxable % / AMT), not a per-share CG book. Open-end Section 19 "
        "/ year-end estimate PDFs were not fetchable — ZZPIMI/ZZPIMB stay parser-layout "
        "samples (not official). Partner ingest is the escape hatch for official notices."
    )
    live_limitations = (
        "No public HTML estimate table or open-end ST/LT PDF on this pass; fixture "
        "parser + POST /ingest/distributions."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="tax_center_sample",
                url="https://www.pimco.com/us/en/resources/tax-center",
                fixture="tax_center_sample.html",
                live=True,
                role="estimate",
                empty_ok=True,
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
                name="open_end_tax_guide",
                url="https://www.invesco.com/us/en/accounts/tax-center/open-end-tax-guide.html",
                fixture="open_end_tax_guide_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="estimated_capital_gains_pdf",
                url="https://www.invesco.com/content/dam/invesco/us/en/documents/tax-centre/2025%20Invesco%20Estimated%20Capital%20Gains%20pdf.pdf",
                fixture="2025_estimated_capital_gains.html",
                live=True,
                role="estimate",
                empty_ok=True,
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
        "2021–2022 YE PDFs are the full mutual-fund/ETF books "
        "(no public HTML siblings): "
        "https://www.troweprice.com/content/dam/fai/Funds/Tax_Center/2021-Year-End-Tax-Distributions.pdf "
        "and .../2022-Year-End-Tax-Distributions.pdf. "
        "Verified 2026-09-07; e.g. TRBCX LT $10.9575 (2025), $16.1515 (2024), $5.2095 (2023), "
        "$6.0394 final / $5.75 prelim (2022), $16.03 (2021). Em-dash / Paid monthly omitted."
    )
    live_limitations = (
        "Live year-end HTML is supported for 2023–2025. "
        "2021–2022 YE and 2022 prelim are PDF transcriptions (live=False)."
    )

    def pages(self) -> list[PageSpec]:
        base = (
            "https://www.troweprice.com/personal-investing/resources/planning/tax/"
            "dividend-distributions/mutual-funds"
        )
        tax_pdf = "https://www.troweprice.com/content/dam/fai/Funds/Tax_Center"
        return [
            PageSpec(
                name="dividend_distributions_hub",
                url="https://www.troweprice.com/personal-investing/resources/planning/tax/dividend-distributions.html",
                fixture="dividend_distributions_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
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
                url=f"{tax_pdf}/2022-Year-End-Tax-Distributions.pdf",
                fixture="2022_year_end_distributions.html",
                live=False,
            ),
            PageSpec(
                name="year_end_2021",
                url=f"{tax_pdf}/2021-Year-End-Tax-Distributions.pdf",
                fixture="2021_year_end_distributions.html",
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
