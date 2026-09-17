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
        "only; SMAs and Variable Series skipped. Live 2021–2025 pages are per-fund share-class tables "
        "(no ticker column) — fixtures flatten November–December YE Investor A rows. "
        "Investor A tickers are backfilled from ``app/aliases_blackrock.py`` without "
        "changing name-slug upsert keys (Equity Dividend Investor A MDDVX). "
        "Equity Dividend Investor A LT $1.089256 (2021) / $0.740291 (2022) / "
        "$0.481929 (2023) / $0.728360 (2024) / $0.999925 (2025). "
        "iShares official December YE income books are the stamped distribution-summary "
        "PDFs on the tax library (2025–2021), transcribed as ICI Primary CSVs "
        "(December / early-January YE payable only; first printed $/share = ordinary "
        "income; ST/LT left blank unless a later wave parses those columns). "
        "IVV Dec 2025 $2.413592; IWM $0.842454; AGG $0.326375 + $0.334012; "
        "ITOT $0.486672. Official 5y wave-2 gap-fill re-reads the same stamped "
        "PDFs for in-book tickers still missing a lookback year: December YE "
        "rows the 2025 ICI CSV omitted (SOXX $0.436272; IDU $0.678689; IYJ "
        "$0.269780; EXI $0.974748; JXI $0.919865; LQDB $0.345201; XJH "
        "$0.209442) and issuer-printed non-December ordinary income when "
        "December is an official dash (MBB 2021-10-01 $0.018858; TFLO "
        "2021-02-01 $0.001023; EIRL 2022-06-09 $0.518078). Cash-liquidation "
        "columns omitted. Never invent missing years or $0. "
        "Official 5y leftover densify maps 2025 stamped-PDF income onto in-book "
        "pre-rename tickers (same product IDs): HYXU/EUHY $1.895899; HYMU/SHYM "
        "$0.098944; FILL/POWR $0.288052 (income column, not POWR total $1.354307); "
        "FIBR/SYSB $0.347286. Product-page $0.000000 rows whose stamped PDFs are "
        "official dashes (SHV 2021 / IGOV 2023 / ISHG 2022 / INDA 2022 / LEMB 2024) "
        "stay unmatched. Leftover LifePath Dynamic Investor A 2022 midyear "
        "(no December table) from the live 2022-distributions page: LPRAX / LPRDX / "
        "LPREX printed $0.000000; LPJAX $0.018889; LPHAX $0.052130; LPRFX $0.033425; "
        "LPVAX $0.070209; LPDAX $0.041208; LPWAX $0.021987 (ex 2022-07-14). "
        "Parallel 5y sweep B leftover years still unpublished after that densify: "
        "CCRV/FM 2025 cash-liquidation omitted; HEWG/ISZE/USBF/WPS 2025 and 2021 "
        "inception leftovers absent; product-page /ticker slugs 404. "
        "Parallel 5y sweep G leftover (same official stamped PDFs + live open-end "
        "tax pages; in-book only): IBHF Dec YE 2021 $0.090837 / 2022 $0.132611 / "
        "2023 $0.143575 / 2024 $0.129749 completes 5y; BIRAX 2021-12-07 OI "
        "$0.242429 / ST $0.197472 / LT $0.076154; MDLOX 2021-07-15 OI $0.958356 / "
        "ST $0.904410 / LT $0.223544 and 2022-07-14 OI $0.483998 / ST $0.483998 / "
        "LT $0.499590. Year-depth: IBIG 2023–2024; IWFH / BECO 2024 June income "
        "(Aug cash-liquidation omitted); ICOL 2022 June $0.415012; LDRC / LDRI / "
        "LDRT Dec 2024; BAMBX 2022; LILAX / LELAX 2024. Official dashes still "
        "unmatched (SHV 2021 / IGOV 2023 / ISHG 2022 / INDA 2022 / LEMB 2024). "
        "BACAX / CMLAX / MDGCX / MDDCX 2025, BHYAX 2023, BCBAX / BAICX 2024, "
        "BAMBX 2021, LILAX / LELAX 2025 unpublished on those live year pages. "
        "All-events leftover (2026-09-16, in-book only): official stamped "
        "distribution-summary PDFs 2022–2025 re-read for non-December ordinary "
        "income / LT / ROC the December-only ICI CSVs omitted. Qualified % "
        "columns are 1099 character — not stored as extra OI. IVV 2025-06-16 "
        "income $1.866967 / 2024-06-11 $1.611133; IYR 2025-06-16 $0.494542. "
        "2021 stamped PDF 404 — unmatched. "
        "Parallel 5y sweep Y leftover (in-book Investor A only; not iShares ETF "
        "income already dense / not #188 quarterly ICI): live 2021–2024 open-end "
        "tax HTML plus the official stamped 2025 book "
        "https://www.blackrock.com/us/individual/literature/market-commentary/2025distributionsstamped.pdf "
        "fill leftover years. Completes 5y: BABDX / BACAX / BALPX / BARDX / BAREX / "
        "BDSAX / BICSX / BROAX / MALRX / MALVX / MCFOX / MDDCX / MDGCX / MDLVX / "
        "MDSPX / SHSAX. Heroes: BACAX 2025-07-17 OI $0.141259 / 2025-12-11 OI "
        "$0.203450; MDDCX 2025-12-09 OI $1.114790; MDGCX 2025-12-09 OI $0.362241 / "
        "ST $1.055639 / LT $1.047497; BARDX 2024-10-10 OI $0.115751 / ST $0.193089 / "
        "LT $1.386730. Walls: CMLAX / LILAX / LELAX 2025 unpublished on the stamped "
        "book (ticker rename / target-date maturity); BAICX 2024 / BAMBX 2021 / "
        "BHYAX 2023 / BCBAX 2024 still unpublished on those live year pages."
    )
    live_limitations = (
        "Live HTML on ishares.com/us/capital-gains-distributions is supported. "
        "Open-end 2021–2025 tax-information HTML is public but not column-safe "
        "(h3 + share-class tables); fixtures are flattened November–December YE books."
    )

    def pages(self) -> list[PageSpec]:
        tax = "https://www.blackrock.com/us/individual/resources/tax-information"
        ishares_tax = "https://www.ishares.com/us/literature/tax-information"
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
                name="ici_primary_2025",
                url=f"{ishares_tax}/2025-ishares-distribution-summary-stamped.pdf",
                fixture="ici_primary_2025.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
            ),
            PageSpec(
                name="ici_primary_2024",
                url=f"{ishares_tax}/2024-ishares-etf-distribution-summary-stamped-extended.pdf",
                fixture="ici_primary_2024.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
            ),
            PageSpec(
                name="ici_primary_2023",
                url=f"{ishares_tax}/2023-ishares-distribution-summary-stamped.pdf",
                fixture="ici_primary_2023.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
            ),
            PageSpec(
                name="ici_primary_2022",
                url=f"{ishares_tax}/2022-ishares-distribution-summary-stamped.pdf",
                fixture="ici_primary_2022.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
            ),
            PageSpec(
                name="ici_primary_2021",
                url=f"{ishares_tax}/2021-ishares-distribution-summary.pdf",
                fixture="ici_primary_2021.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
            ),
            PageSpec(
                name="ici_history_gapfill",
                url=f"{ishares_tax}/2025-ishares-distribution-summary-stamped.pdf",
                fixture="ici_history_gapfill.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
                role="history",
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
                name="leftover_lifepath_dynamic_2022",
                url=f"{tax}/2022-distributions",
                fixture="leftover_lifepath_dynamic_2022.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="ici_leftover_parallel_g",
                url=f"{ishares_tax}/2025-ishares-distribution-summary-stamped.pdf",
                fixture="ici_leftover_parallel_g.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
                role="history",
            ),
            PageSpec(
                name="leftover_open_end_parallel_g",
                url=f"{tax}/2021-distributions",
                fixture="leftover_open_end_parallel_g.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="leftover_open_end_parallel_y",
                url="https://www.blackrock.com/us/individual/literature/market-commentary/2025distributionsstamped.pdf",
                fixture="leftover_open_end_parallel_y.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2021_open_end_distributions",
                url=f"{tax}/2021-distributions",
                fixture="2021_open_end_distributions.html",
                live=False,
            ),
            PageSpec(
                name="ici_leftover_all_events_quarterly",
                url=f"{ishares_tax}/2025-ishares-distribution-summary-stamped.pdf",
                fixture="ici_leftover_all_events_quarterly.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
                role="history",
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
        "Wave mega-ETF densify appends official December YE ETF rows that were "
        "thin in the earlier Admiral-heavy extract: VNQ Dec 2025 income $0.800500; "
        "BNDX Dec 2025 monthly $0.104400 + YE $0.968600 (CUSIPs 922908553 / 92203J407). "
        "Wave 17 leftover ICI December YE (same official PDFs; not in the earlier "
        "extract): VONE 2025 income $0.873200; VTWO $0.402800; VTHR $0.893000; "
        "VCLT Dec 1 $0.340200 + Dec 18 $0.349200; VEVFX OI $0.494900 / ST "
        "$0.218968 / LT $3.582907. Existing ICI tickers are not re-emitted. "
        "Official 5y wave-2 adds in-book VTIPX Dec 2025 income $0.350500 from the "
        "same ICIprimary_012026.pdf (sibling VTAPX / VTSPX / VTIP were already "
        "on the 2025 ICI CSV). Parallel D leftover ICI (same official PDFs; "
        "re-extracted 2026-09-13): VTSPX Dec 2021 income $0.481000 / Dec 2023 "
        "$0.320200; VSEMX 2025 has no December row — March $0.764300 / June "
        "$0.668200 stored; VCTXX / VMRXX / VMSXX 2024–2025 have no dated YE "
        "special — one December daily income snapshot each (VCTXX 12/2/2024 "
        "$0.001951 / 12/1/2025 $0.001825; VMRXX $0.003813 / $0.003214; VMSXX "
        "$0.002457 / $0.002213). VEDIX leftover 2024 latest printed Q3 "
        "$0.586100 (no December; 2025 official dashes — unmatched). Quarterly "
        "lines still omitted except those leftover-year fills. VBPIX / VSVNX "
        "2021 absent (inception). VAIGX / VEOAX / VEOIX 2021–22 official dashes. "
        "VIDGX 2022 absent. Tax center hub: https://advisors.vanguard.com/tax-center. "
        "All-events leftover (2026-09-16, in-book only): official ICI Primary "
        "PDFs re-read for March / June / September income and any non-December "
        "ST/LT the December-only CSVs omitted. Daily / money-market lines still "
        "skipped. VBINX 2025-03-27 OI $0.276100 / ST $0.006602 / LT $0.638521; "
        "VIGAX 2025-06-30 income $0.254400. Row as_of is the event ex-date — "
        "never collapsed onto Dec 31. Official 5y parallel AA leftover (same "
        "official ICI PDFs; re-extracted 2026-09-16): leftover in-book bond / "
        "tax-exempt / money-market years still short of 2021–2025. December "
        "dated rows first (BND 2022-12-29 income $0.172311 / 2025-12-22 "
        "$0.246638; VBIIX 2022-12-01 $0.021170; VWALX 2022-12-01 $0.030387). "
        "Tax-exempt income uses the printed total/exempt dollar when ICI col "
        "14 is a dash — not invented. When December is unpublished in that "
        "year's extract, the latest leftover-year dated row is stored (BIV "
        "2025-08-05 $0.265057; VBTIX 2023-04-03 $0.024227; VFIRX 2023-09-01 "
        "$0.035085; VTBSX 2022-05-02 $0.018866; VCLAX 2023-03-01 $0.029218). "
        "Daily NII keeps one December snapshot (VUSXX). VBTLX 2023 / BSV "
        "2022+2025 / VWEHX 2025 wrap-absent. Recent launches (BNDP / VBIL / "
        "VDIG / VEXC / VGHY / VGMS / VGUS / VGVT / VSDB / VTG / VTP / VUSG / "
        "VUSV / VCPSX) and VEDIX 2025 official dashes stay unmatched. VFLQ "
        "2022-11-28 $99.896787 is official ROC/liquidation (col 14 income "
        "dash) — not stored as ordinary income."
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
            PageSpec(
                name="remaining_ici_primary_2025",
                url=f"{ici}/ICIprimary_012026.pdf",
                fixture="remaining_ici_primary_2025.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
                role="history",
            ),
            PageSpec(
                name="remaining_ici_primary_2024",
                url=f"{ici}/ICI_revised_2024_Primary_layout_spreadsheet.pdf",
                fixture="remaining_ici_primary_2024.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
                role="history",
            ),
            PageSpec(
                name="remaining_ici_primary_2023",
                url=f"{ici}/2023_ICI_Primary_Layout.pdf",
                fixture="remaining_ici_primary_2023.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
                role="history",
            ),
            PageSpec(
                name="remaining_ici_primary_2022",
                url=f"{ici}/2022_ICI_Primary_Layout.pdf",
                fixture="remaining_ici_primary_2022.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
                role="history",
            ),
            PageSpec(
                name="remaining_ici_primary_2021",
                url=f"{ici}/2021_ICI_Primary_Layout.pdf",
                fixture="remaining_ici_primary_2021.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
                role="history",
            ),
            PageSpec(
                name="ici_leftover_quarterly_midyear",
                url=f"{ici}/ICIprimary_012026.pdf",
                fixture="ici_leftover_quarterly_midyear.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
                role="history",
            ),
            PageSpec(
                name="leftover_ici_primary_2025",
                url=f"{ici}/ICIprimary_012026.pdf",
                fixture="leftover_ici_primary_2025.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
                role="history",
            ),
            PageSpec(
                name="leftover_ici_primary_2024",
                url=f"{ici}/ICI_revised_2024_Primary_layout_spreadsheet.pdf",
                fixture="leftover_ici_primary_2024.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
                role="history",
            ),
            PageSpec(
                name="leftover_ici_primary_2023",
                url=f"{ici}/2023_ICI_Primary_Layout.pdf",
                fixture="leftover_ici_primary_2023.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
                role="history",
            ),
            PageSpec(
                name="leftover_ici_primary_2022",
                url=f"{ici}/2022_ICI_Primary_Layout.pdf",
                fixture="leftover_ici_primary_2022.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
                role="history",
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
        "2021 DPL6 is the Wayback 20221209193656id_ capture: verified 2021 rows "
        "through FIMIX (204 tickers; FCNTX Dec LT $1.62700 / Feb LT $0.40000; "
        "FBGRX Dec LT $2.51300 / Sep ST $1.33300 LT $12.18700). Later range "
        "fetches of that timestamp replay a 2024 digest — N–Z not invented. "
        "2022–2023 DPL6 HTML is still not in CDX (HPDY SPA; Wave 3 + parallel-B "
        "+ parallel-D re-probe 2026-09-13; FIIS_SP10_DPL19 is 2025 Class K only, "
        "not a 2022–23 archive). No non-SPA HTML/PDF 2022–23 family book found — "
        "skip the DPL SPA wall. SEC 485BPOS 0000754510-24-000178 has fiscal "
        "July-31 highlights without a safe retail-class calendar-year map "
        "(FBGRX / FBCVX stay 3y). FCNTX 2022–2023 "
        "uses the official retail prospectus financial highlights (income "
        "$0.08 / $0.08 and net realized gain $1.36 / $0.61) stored as "
        "ordinary_income + total_capital_gains — ST/LT not published, not "
        "invented. No QDI % columns. "
        "Official 5y leftover WAVE X (existing Advisor Class I leftovers only): "
        "unfiltered DPL2 Wayback paid books 2022–2024 keep every printed "
        "midyear + YE event with official OI/ST/LT (including printed "
        "$0.00000). ShareClassId-filtered Wayback URLs 404; the 2021 DPL2 "
        "snapshot is Class A name-only (0 tickers) — Class I 2021 is unpublished "
        "except Fidelity Advisor Mega Cap Stock I (FTRIX) Hastings Street Trust "
        "N-CSR Financial Highlights (year ended June 30 2021: income $0.29 / "
        "net realized gain $1.00 unsplit). Retail DPL6 2022–2023 remains "
        "unpublished in CDX (HPDY SPA). No sibling copy onto A/C/M/Z or retail. "
        "Official 5y WAVE AG leftover does not redo Advisor DPL2 / FTRIX N-CSR "
        "from WAVE X. Remaining retail leftovers still miss 2022–2023 DPL6 "
        "(HPDY SPA); July-31 / March-31 highlights stay not calendar-safe. "
        "Hub: https://www.fidelity.com/mutual-funds/information/overview. "
        "Wave 10 share-class densify: Fidelity Advisor Funds are a separate "
        "official DPL (not on retail FIIS_SP52/SP10_DPL6). Full A/C/M/I/Z "
        "filter ``shareClassId=1SC3SC10SC9SC50805SC50405SC50855SC`` on "
        "https://institutional.fidelity.com/app/tabbed/products/FIIS_SP52_DPL2_DSC1.html "
        "and FIIS_SP10_DPL2_DSC1.html. Default DPL2 without the filter is "
        "Class I-heavy. 2025 paid book is **799** Advisor tickers (0 overlap "
        "with retail DPL6): FAGAX / FAGCX Growth Opp Dec LT $8.58500; "
        "FTRIX Mega Cap Stock Dec LT $0.27700 / Aug LT $0.65700; "
        "FCIGX Small Cap Growth Dec LT $0.77100 / Sep LT $1.46100. "
        "2026 Advisor estimate sleeve (seasonal upcoming only) includes "
        "FCIGX ST $0.355 / LT $6.922 / 17.30% of NAV (as of 2026-07-31). "
        "Record date: the midyear estimate table (FIIS_SP52_DPL6) and prior-year "
        "paid DPL6 print Fund / Ex Date / Pay Date / NAV / % of NAV / ST / LT / "
        "Total / As of — no Record / Record Date / Date of Record column. "
        "Advisor DPL2 uses the same columns. "
        "Fidelity's Cap-Gains Q&A (literature 779188) defines Record Date as "
        "usually the business day prior to ex and states that only Ex-Date and "
        "Pay Date are disclosed in the table. No filled ICI Primary Layout for "
        "these FBGRX-class fiscal estimates. record_date stays null — never "
        "invented from ex-1. Parser will store Record when a future book prints it."
    )
    live_limitations = (
        "Live HTML tables on institutional.fidelity.com are supported "
        "(current estimates + prior-year paid, including Advisor DPL2). "
        "The live DPL6 / DPL2 prior-year URLs rotate to "
        "the latest prior year — 2021 and 2024 retail DPL6 are fixture-only. 2022–2023 "
        "DPL6 is unpublished in CDX (parallel-D re-probe); FCNTX highlights are prospectus-only. "
        "Combined 485BPOS fiscal-year tables are not a class-safe 2022–23 retail archive. "
        "Advisor A/C/M/I/Z requires the shareClassId query; without it the "
        "live table is Class I-heavy. "
        "Advisor DPL2 2022–2024 leftover history is fixture-only (Wayback "
        "unfiltered Class I); 2021 Class I DPL2 unpublished; FTRIX 2021 is "
        "N-CSR fixture-only. "
        "Estimate + paid DPL omit Record Date; ETF Annual-Distribution-Calendar "
        "PDF prints Record but is not this mutual-fund estimate book."
    )

    def pages(self) -> list[PageSpec]:
        dpl6 = "https://institutional.fidelity.com/app/tabbed/products/FIIS_SP10_DPL6.html?navId=324"
        advisor_classes = "shareClassId=1SC3SC10SC9SC50805SC50405SC50855SC"
        advisor_est = (
            "https://institutional.fidelity.com/app/tabbed/products/"
            f"FIIS_SP52_DPL2_DSC1.html?navId=320&{advisor_classes}"
        )
        advisor_prior = (
            "https://institutional.fidelity.com/app/tabbed/products/"
            f"FIIS_SP10_DPL2_DSC1.html?navId=320&{advisor_classes}"
        )
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
                name="advisor_estimated_capital_gains",
                url=advisor_est,
                fixture="advisor_estimated_capital_gains.html",
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
                name="advisor_prior_year_distributions",
                url=advisor_prior,
                fixture="advisor_prior_year_distributions.html",
                live=True,
            ),
            PageSpec(
                name="prior_year_distributions_2024",
                url=dpl6,
                fixture="prior_year_distributions_2024.html",
                live=False,
            ),
            PageSpec(
                name="prior_year_distributions_2021",
                url=dpl6,
                fixture="prior_year_distributions_2021.html",
                live=False,
            ),
            PageSpec(
                name="financial_highlights_2022_2023",
                url="https://institutional.fidelity.com/app/funds-and-products/22/fidelity-contrafund-fcntx.html",
                fixture="financial_highlights_2022_2023.html",
                live=False,
            ),
            PageSpec(
                name="leftover_dpl2_class_i_2022_2024",
                url=(
                    "https://institutional.fidelity.com/app/tabbed/products/"
                    "FIIS_SP10_DPL2_DSC1.html?navId=320"
                ),
                fixture="leftover_dpl2_class_i_2022_2024.html",
                live=False,
                role="history",
                large_aum_only=True,
            ),
            PageSpec(
                name="leftover_ftrix_ncsr_2021",
                url="https://www.sec.gov/Archives/edgar/data/35348/000003534823000091/filing6692.htm",
                fixture="leftover_ftrix_ncsr_2021.html",
                live=False,
                role="history",
                large_aum_only=True,
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
        "cell, including official $0.000000). SPLG was renamed SPYM on 10/31/2025. "
        "GLD is absent from the XLSX (grantor trust). Official FAQ "
        "https://www.ssga.com/library-content/products/fund-docs/etfs/us/tax-documents/gld-faq.pdf "
        "states the trust makes no distributions — 2025 published $0.000000 stored, "
        "not invented. Parallel 5y sweep G leftover (same official XLSX; in-book "
        "only): NZAC 2022-12-01 income $0.214724 and 2023-12-01 $0.229707 plus the "
        "June semi-annual companions (empty ST/LT cells omitted, not invented $0). "
        "HYBL 2021 / SPDG 2021–2022 unpublished (inception). Later 1y / 2y launches "
        "stay unmatched. Parallel AA leftover re-probe (2026-09-16): same official "
        "XLSX. SPLG was renamed SPYM (10/31/2025) — leftover years stay under "
        "SPYM, not copied onto SPLG. ALLW / PRIV / premium-income and MyMap "
        "2024–2025 launches stay unmatched (inception). GLD grantor trust "
        "still publishes no distributions. "
        "WAVE AE leftover re-probe (2026-09-17): same official ETF XLSX has no "
        "missing-year fills for leftover in-book tickers. HYBL 2021 / SPDG "
        "2021–2022 remain unpublished (inception). Later 1y / 2y launches "
        "(ALLW / PRIV / MyMap / premium-income) stay unmatched. Official MF "
        "historical-distribution XLSX sibling still 404. Unmatched / not invented."
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
            PageSpec(
                name="leftover_nzac_2022_2023",
                url=xlsx,
                fixture="leftover_nzac_2022_2023.html",
                live=False,
                role="history",
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
        "(SEEGX / JLGMX 2024 LT mapping $0.79868). 2023/2022/2021 sibling 19a "
        "URLs re-probed 2026-09-10 and 2026-09-13 still 404 — not invented. "
        "Wayback CDX of the 19a directory has one 200 snapshot "
        "(20230123204513id_ section-19-notice-multiple-fund.pdf) — December 15 "
        "2022 ETF estimate CG for Income / Inflation Managed Bond / Market "
        "Expansion Enhanced Equity / Realty Income / Ultra-Short Income ETFs "
        "(no tickers; those names are not in-book leftovers). JEPQ 2021 is a "
        "commencement-year gap (N-CSR stub starts 2022 $0.38). "
        "JEPI / JEPQ are absent from those 19a Appendix A CG tables (income-only). "
        "Official US fiscal-year ordinary-income per share is in the J.P. Morgan "
        "Exchange-Traded Fund Trust N-CSR Financial Highlights (years ended June 30): "
        "https://www.sec.gov/Archives/edgar/data/1485894/000119312525193891/d66956dncsr.htm "
        "(JEPI 2025 $4.67 / 2024 $4.16 / 2023 $6.04 / 2022 $4.96 / 2021 $4.85; "
        "JEPQ 2025 $6.11 / 2024 $4.86 / 2023 $5.64 / 2022 commencement stub $0.38). "
        "Those are full-year paid totals, not a single December payable. "
        "AU/CA JEPI unit amounts are a different share class — not used. "
        "Official 5y leftover WAVE X (existing Trust II Class A leftovers + "
        "Large Cap Growth R6 JLGMX): fiscal-year per-share paid totals from "
        "the J.P. Morgan Trust II N-CSR Financial Highlights (years ended "
        "June 30). 2021–2023 for the 2y leftover Class A book; 2024 N-CSR "
        "only for JICAX / OGEAX / VSCOX that still lacked 2024 paid/final. "
        "Income is ordinary income; net realized gain is unsplit total "
        "capital gains (ST/LT not published, not invented). Printed dashes "
        "omitted, not stored as $0. Existing 2024 Section 19a leftovers keep "
        "that book. UBVAX is a different trust — unmatched. PGSGX 2024 both "
        "columns dashed — 2024 unmatched. JEPQ 2021 remains a commencement "
        "wall. No sibling copy."
    )
    live_limitations = (
        "No scrapeable HTML grid; 19a books are PDF. Fixture / partner ingest only. "
        "Trust II leftover Class A / JLGMX 2021–2024 paid history is N-CSR fixture-only."
    )

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
            PageSpec(
                name="jepi_ncsr_financial_highlights",
                url="https://www.sec.gov/Archives/edgar/data/1485894/000119312525193891/d66956dncsr.htm",
                fixture="jepi_ncsr_financial_highlights.html",
                live=False,
            ),
            PageSpec(
                name="leftover_ncsr_class_a_2021_2024",
                url="https://www.sec.gov/Archives/edgar/data/763852/000119312524214952/d880089dncsr.htm",
                fixture="leftover_ncsr_class_a_2021_2024.html",
                live=False,
                role="history",
                large_aum_only=True,
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
        "(GLCGX). Parallel E leftover re-probe (2026-09-13): advisor tax center still "
        "403. Official 5y leftover WAVE X: Large Cap Growth Insights Class A "
        "(GLCGX) and Institutional (GCGIX) fiscal-year per-share paid totals "
        "from Goldman Sachs Trust N-CSR Financial Highlights (years ended "
        "October 31) 2021–2024 — "
        "https://www.sec.gov/Archives/edgar/data/822977/000119312525001448/d907373dncsr.htm "
        "(verified against 0001193125-24-002318 / d536551dncsr.htm and "
        "0001193125-22-000509 / d173829dncsr.htm). Income is ordinary income; "
        "net realized gain is unsplit total capital gains. Printed dashes "
        "omitted. 2025 calendar YE stays on the existing year-end sample "
        "(GLCGX / GCGIX LT $2.74 ex 2025-12-11). Class-level only — no sibling "
        "copy. Third-party history unused."
    )
    live_limitations = (
        "Advisor tax center is login/403-walled (including historical packs). "
        "Insights leftover 2021–2024 paid history is N-CSR fixture-only. "
        "Use fixtures or POST /ingest/distributions."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="year_end_sample",
                url="https://www.gsam.com/content/gsam/us/en/advisors/literature-and-forms/forms-and-tax-center.html",
                fixture="year_end_distributions_sample.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="leftover_ncsr_insights_2021_2024",
                url="https://www.sec.gov/Archives/edgar/data/822977/000119312525001448/d907373dncsr.htm",
                fixture="leftover_ncsr_insights_2021_2024.html",
                live=False,
                role="history",
                large_aum_only=True,
            ),
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
        "samples (not official). Parallel E leftover re-probe (2026-09-13): tax-center "
        "PDFs remain 1099 character (muni % / AMT / US-gov %), not ST/LT $/share; "
        "BOND ETF product page GET 403; no in-book leftover tickers. Parallel Y "
        "leftover re-probe (2026-09-16): tax-center / 2021–2025 year-end-forms pages "
        "are still 1099 character (muni % / AMT / US-gov %), not ST/LT $/share. "
        "Fixture book has parser-layout samples only (ZZPIMI / ZZPIMB) — no existing "
        "in-book PIMCO MF tickers to densify. Partner ingest is the escape hatch "
        "for official notices."
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
        "Official ICI Primary broker XLSX files are public on "
        "https://www.invesco.com/us/en/accounts/tax-center/open-end-tax-guide.html "
        "(2025 most-funds + Real Estate; 2024 / 2023 oe-*-primary-broker-file.xlsx "
        "+ Real Estate companions). December YE income / ST / LT $/share only "
        "(Daily and $0 omitted; bare QDI / 199A / AMT % columns omitted). "
        "VAFAX Dec 2025 LT $4.0375 / 2024 LT $1.0971. SteelPath companions had "
        "no December YE $/share rows — not invented. 2021–2022 sibling XLSX "
        "URLs still 406 (GET, including oe-2021/2022-primary-broker-file.xlsx "
        "and 2021/2022-Primary-Broker-File-without-Real-Estate…); open-end tax "
        "guide lists Primary files for 2023–2025 only. Wayback CDX has no "
        "200 snapshot of those XLSX paths. Unmatched / Undisclosed. "
        "QQQ (UIT through 12/19/2025) is absent from the open-end ICI broker files. "
        "Official Invesco QQQ Trust financial highlights (N-30B-2 / HK annual report) "
        "publish fiscal-year ordinary-income per share for years ended September 30: "
        "2025 $2.84 / 2024 $3.04 / 2023 $2.17 / 2022 $1.97 / 2021 $1.77. "
        "Those are full-year paid totals, not a single December payable. "
        "Individual quarterly YE $/share US notices were not column-safe this wave. "
        "Parallel F leftover re-probe (2026-09-13): oe-2021/2022-primary-broker-file.xlsx "
        "and 2021/2022-Primary-Broker-File-without-Real-Estate siblings still GET 406; "
        "open-end tax-guide HTML also 406 this fetch. Existing 2023–2025 ICI CSVs have "
        "no leftover-missing-year rows (VAFAX etc. absent from 2023). In-book leftovers "
        "are almost all 3y (2023–2025) and cannot reach 5y without both 2021 and 2022. "
        "Fiscal Aug-31 N-CSR highlights are not calendar-safe next to ICI December YE. "
        "No new ETF identities (RSP / SPHD / QQQM stay out of book). "
        "Parallel Y leftover re-probe (2026-09-16): open-end tax guide still lists "
        "ICI Primary broker files for 2023–2025 only; oe-2021/2022-primary-broker-file.xlsx "
        "and 2021/2022-Primary-Broker-File-without-Real-Estate siblings GET 404. "
        "In-book leftovers remain almost all 3y (2023–2025) and cannot reach 5y "
        "without both official 2021 and 2022 December YE books. Unmatched / not invented. "
        "Official 5y leftover WAVE AE (existing in-book ETF estimate identities only): "
        "ETF Tax Center ICI Primary/Secondary/NRA XLSX 2021–2025 "
        "(ICI-Primary-and-Secondary-and-NRA-File-IVZ-ETF-2025.xlsx and "
        "ce-ici-primary-and-secondary-distribution-file-and-nra-file-ivz-etf-2021..2024) "
        "unlock PIN / PSCI / IDMO / IVRA / PBP to 5y from official December YE "
        "$/share (PIN 2021 LT $1.31763 / 2022 LT $2.99469; IDMO 2021 income $0.218; "
        "IVRA 2021 ST $0.36875 / LT $0.02875; PBP 2021 ST $1.24053; PSCI 2021 "
        "income $0.18503). QQQ already 5y — not redone. Year-depth only: HIYS "
        "2023–2025, BSJW 2024–2025, BSJX / GTOC / IQSZ / MTRA 2025. Open-end MF "
        "Investor A leftovers belong to Y #194 — 2021–2022 ICI still 404, not "
        "redone. No new ETF identities. "
        "WAVE AJ leftover re-probe (2026-09-17): Invesco MF 2021–2022 open-end "
        "ICI still GET 406 / 404 — leftovers stay 3y (2023–2025). ETF leftovers "
        "belong to AE and are not redone."
    )
    live_limitations = (
        "Estimates are PDF/PR/contentdetail, not an HTML grid. ICI Primary XLSX "
        "is public but not HTML — fixture mode transcribes December YE rows."
    )

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
            PageSpec(
                name="ici_primary_2025",
                url=(
                    "https://www.invesco.com/content/dam/invesco/us/en/documents/"
                    "tax-documents/2025-Primary-Broker-File-without-Real-Estate-or-SteelPath-MLP-Funds.xlsx"
                ),
                fixture="ici_primary_2025.csv",
                live=False,
                parser="ici",
            ),
            PageSpec(
                name="ici_primary_2024",
                url=(
                    "https://www.invesco.com/content/dam/invesco/us/en/documents/"
                    "tax-document/oe-2024-primary-broker-file.xlsx"
                ),
                fixture="ici_primary_2024.csv",
                live=False,
                parser="ici",
            ),
            PageSpec(
                name="ici_primary_2023",
                url=(
                    "https://www.invesco.com/content/dam/invesco/us/en/documents/"
                    "tax-document/oe-2023-primary-broker-file.xlsx"
                ),
                fixture="ici_primary_2023.csv",
                live=False,
                parser="ici",
            ),
            PageSpec(
                name="qqq_annual_report_distributions",
                url="https://www.invesco.com/content/dam/invesco/hk/en/pdf/annual-report/Invesco_QQQ_AnnualReport.pdf",
                fixture="qqq_annual_report_distributions.html",
                live=False,
            ),
            PageSpec(
                name="leftover_etf_ici_2025",
                url=(
                    "https://www.invesco.com/content/dam/invesco/us/en/documents/"
                    "tax-documents/ICI-Primary-and-Secondary-and-NRA-File-IVZ-ETF-2025.xlsx"
                ),
                fixture="leftover_etf_ici_2025.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
                role="history",
            ),
            PageSpec(
                name="leftover_etf_ici_2024",
                url=(
                    "https://www.invesco.com/content/dam/invesco/us/en/documents/"
                    "tax-document/ce-ici-primary-and-secondary-distribution-file-file-ivz-etf-2024-02-10-2025.xlsx"
                ),
                fixture="leftover_etf_ici_2024.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
                role="history",
            ),
            PageSpec(
                name="leftover_etf_ici_2023",
                url=(
                    "https://www.invesco.com/content/dam/invesco/us/en/documents/"
                    "tax-document/ce-ici-primary-and-secondary-distribution-file-and-nra-file-ivz-etf-2023.xlsx"
                ),
                fixture="leftover_etf_ici_2023.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
                role="history",
            ),
            PageSpec(
                name="leftover_etf_ici_2022",
                url=(
                    "https://www.invesco.com/content/dam/invesco/us/en/documents/"
                    "tax-document/ce-ici-primary-and-secondary-distribution-file-and-nra-file-ivz-etf-2022.xlsx"
                ),
                fixture="leftover_etf_ici_2022.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
                role="history",
            ),
            PageSpec(
                name="leftover_etf_ici_2021",
                url=(
                    "https://www.invesco.com/content/dam/invesco/us/en/documents/"
                    "tax-document/ce-ici-primary-and-secondary-distribution-file-and-nra-file-ivz-etf-2021.xlsx"
                ),
                fixture="leftover_etf_ici_2021.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
                role="history",
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
        "Wave 13 adds the official ETF YE HTML books "
        "https://www.troweprice.com/personal-investing/resources/planning/tax/"
        "dividend-distributions/etfs/2025-year-end-distributions.html "
        "(and 2024 / 2023 siblings): TCAF 2025 income $0.1916; THEQ income "
        "$0.1437 / ST $0.0548 / LT $0.0237; TVAL $0.4061. All-dash rows "
        "omitted. Variable QA* share classes are not on the public ticker "
        "YE HTML — unmatched. "
        "Verified 2026-09-07; e.g. TRBCX LT $10.9575 (2025), $16.1515 (2024), $5.2095 (2023), "
        "$6.0394 final / $5.75 prelim (2022), $16.03 (2021). Em-dash / Paid monthly omitted. "
        "Official 5y wave 4 adds the leftover 2023 ETF YE bond table from the same "
        "public HTML (TAGG income $0.1504; TOTR $0.1713; TBUX $0.2257 / ST $0.0369 / "
        "LT $0.0321). TCHP 2023 all em-dash omitted. PREFX / TEEFX / PRNHX / PRSCX "
        "official YE rows that are all em-dash stay unmatched. "
        "Parallel 5y sweep B: 2024 all-class PDF still 404; ETF 2021/2022 "
        "HTML siblings still 404; live 2024/2025 ETF HTML prints TGRW / TCHP "
        "as all em-dash (not stored); TFLR/THYF have no 2021 row on the "
        "official 2021 YE PDF (inception 2022). Advisor/R 2024 HTML still "
        "Investor/I only. "
        "Parallel F leftover (2026-09-13): 2021 YE PDF Retirement Blend 2035 "
        "Investor TBLYX (ticker printed TBLY X) income $0.071 / ST $0.072 ex "
        "2021-12-21; 2022 YE PDF TBLYX income $0.1296 / ST $0.0369 / LT $0.0145 "
        "ex 2022-12-21 — class-level, not copied from I-Class TBLHX. "
        "2023 iinvestor all-class PDF TRLAX LT $0.1199 ex 2023-12-28 (Paid monthly "
        "income omitted; 2021 still unpublished on the 2021 YE PDF). "
        "iinvestor 2022–2024 all-class PDFs GET 200; 2025 sibling 404; fai "
        "2024-Year-End-Tax-Distributions.pdf still 404. Retirement I leftovers "
        "(TRPTX / TRPNX …) still unpublished on the 2024 all-class PDF and live "
        "2024/2025 HTML. Retirement Fund I Class (TRAJX …) 2021–2022 absent from "
        "YE PDFs. Advisor/R 2023–2025 not on the all-class investor PDFs. "
        "PRGSX / TRGLX / TGBLX 2022 official all-dash; PRSCX / PRNHX / TSNIX / "
        "PRJIX 2023 official all-dash; PREFX / TEEFX 2025 official all-dash; "
        "PGLOX 2025 absent; TGPEX 2022/2024 official all-dash; RPSIX / TSPNX "
        "2023/2025 Paid monthly + dash ST/LT. "
        "All-events leftover (2026-09-16, in-book only): official quarterly "
        "income HTML 2023–2025 plus Wayback captures of the 2021 (Q1+Q2) and "
        "2022 pages. PRFDX 2025-06-26 income $0.1922 / RPBAX $0.1849. TRBCX / "
        "PRGFX are YE-only on those quarterly books — unmatched, not invented. "
        "Mass Z leftover (2026-09-16): official FAI 2023 Year-End Tax "
        "Distributions PDF plus 2025 Year-End XLSX fill leftover Advisor / R / "
        "Institutional years (PABGX 2023 LT $5.2095 / 2025 ST $0.0748 / LT "
        "$10.9575; RRBGX same LT). Class-level — never copied from Investor "
        "TRBCX. Advisor/R 2024 all-class PDF/XLSX still unpublished — those "
        "leftovers stay 4y (2021–2023+2025), not 5y."
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
            PageSpec(
                name="etf_year_end_2025",
                url=f"{base.replace('mutual-funds', 'etfs')}/2025-year-end-distributions.html",
                fixture="2025_etf_year_end_distributions.html",
                live=True,
            ),
            PageSpec(
                name="etf_year_end_2024",
                url=f"{base.replace('mutual-funds', 'etfs')}/2024-year-end-distributions.html",
                fixture="2024_etf_year_end_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="etf_year_end_2023",
                url=f"{base.replace('mutual-funds', 'etfs')}/2023-year-end-distributions.html",
                fixture="2023_etf_year_end_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="leftover_retirement_blend_2021_2022",
                url=f"{tax_pdf}/2021-Year-End-Tax-Distributions.pdf",
                fixture="leftover_retirement_blend_2021_2022.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="leftover_quarterly_2021_2025",
                url=f"{base}/2025-quarterly-distributions.html",
                fixture="leftover_quarterly_2021_2025.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="leftover_advisor_r_institutional_paid_year_end",
                url=f"{tax_pdf}/T. Rowe Price 2023 Year-End Tax Distributions.pdf",
                fixture="leftover_advisor_r_institutional_paid_year_end.html",
                live=False,
                role="history",
                large_aum_only=False,
            ),
        ]
