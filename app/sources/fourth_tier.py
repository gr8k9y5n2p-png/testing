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
        "is the full paying-fund CG table plus income-only MF/ETF rows from the "
        "same notice (TAGRX LT $6.85–$7.60; mutual funds + "
        "ETFs only — closed-end rows skipped; all-dash omitted). Plus 2024 / 2023 / 2022 "
        "sibling filenames (TAGRX LT $7.80–$8.80 / $3.60–$4.10 / $3.00–$3.60). USGLX listed "
        "em-dashes in 2022–2023 (no CG — omitted, not stored as $0). "
        "HTML press-release shells are viewers; the PDFs are the books. "
        "Official 5y parallel M leftover: no public filled ICI; jhinvestments.com "
        "product pages 404; tax-center is a login shell. Shareholder-report PDFs "
        "are fund-level tax-character totals, not per-share Class A YE. "
        "Estimate press-release PDFs stay estimates — never promoted to final."
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
                live=True,
                role="estimate",
                empty_ok=True,
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
        "distribution history at https://www.principalam.com/us/fund/<ticker>. "
        "Wave 12 transcribes the December YE capital-gain book from those pages "
        "(2025 79 tickers / 2024 79 / 2023 48; ~86 unique). Heroes unchanged: "
        "Equity Income PQIAX (2025-12-11 ST $0.1254 / LT $3.3687; 2024-12-12 "
        "ST $0.0425 / LT $3.6805; 2023-12-13 LT $0.2649), MidCap PEMGX "
        "(2025-12-11 LT $2.4892; 2024-12-12 LT $1.3963; 2023-12-13 LT $0.9475), "
        "LargeCap S&amp;P 500 Index Inst PLFPX (2025-12-18 ST $0.0190 / LT $0.6384), "
        "Blue Chip A PBLCX (2025-12-11 LT $8.3248; 2024-12-12 ST $0.0055 / LT $2.0527; "
        "no 2023 row), plus LargeCap Growth I PLGIX (2025-12-18 ST $0.3345 / LT $1.9823) "
        "and LifeTime 2025 Inst LTSTX (2025-12-18 ST $0.0449 / LT $0.9348). "
        "Annual/monthly income omitted. Missing ST omitted, not invented as $0. "
        "Official 5y leftover densify: Wayback 20230101000000id_ product-page "
        "tables restore 2021–2022 December YE for leftover 3y classes after live "
        "pages truncate (PQIAX 2022-12-13 ST $0.0498 / LT $1.3028 and 2021-12-13 "
        "ST $0.3043 / LT $1.3095; PEMGX 2022 LT $0.9922 / 2021 ST $0.1221 / LT "
        "$3.2088; PLGIX 2022 LT $1.5188 / 2021 ST $0.2032 / LT $2.3156; PCBIX "
        "same MidCap Inst amounts; LTSTX 2022-12-20 ST $0.0265 / LT $0.5279). "
        "PINIX live 2023 December income $0.3959 fills the leftover 2y year "
        "(no 2023 CG). PBLCX / PBCKX still have no 2023 YE row — unmatched. "
        "Official 5y leftover 2y/1y densify uses live product pages plus Wayback "
        "2022 / 20240101 (not 20230101000000id_): PALTX 2023 income $0.2506 / "
        "2021 ST $0.0442 / LT $0.5565; PLSIX 2023 income $0.2822; PMSAX 2023 "
        "income $0.3149; PTPPX 2023 income $0.3745; PGBHX 2023 income $0.0121 "
        "(not copied onto PGBGX / PGBEX). Real Estate leftover 2021–2023 "
        "(PRRAX 2023 income $0.1457). GEM leftover 2021–2023 income (no 2024 YE). "
        "SmallCap Growth leftovers + PGBGX / PGBEX / PGRTX / PBLAX / PBCJX still "
        "have no 2023 YE — unmatched. PINJX product page 404. "
        "Class-level — never copied across A/I/C/R/J."
    )
    live_limitations = (
        "Family estimate PDF is a GetFile/viewer shell. Product-page tables may put the date "
        "in the first column, so static parse may return 0 rows. Fixture fallback."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="tax_center_hub",
                url="https://www.principal.com/help/help-individuals/tax-center/dividends-capital-gains-distributions",
                fixture="tax_center_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_paid_product_pages",
                url="https://www.principalam.com/us/fund/pqiax",
                fixture="2025_paid_distributions.html",
                live=True,
            ),
            PageSpec(
                name="2024_paid_product_pages",
                url="https://www.principalam.com/us/fund/pqiax",
                fixture="2024_paid_distributions.html",
                live=False,
            ),
            PageSpec(
                name="2023_paid_product_pages",
                url="https://www.principalam.com/us/fund/pqiax",
                fixture="2023_paid_distributions.html",
                live=False,
            ),
            PageSpec(
                name="leftover_product_page_history_2021_2022",
                url=(
                    "https://web.archive.org/web/20230101000000id_/"
                    "https://www.principalam.com/us/fund/pqiax"
                ),
                fixture="leftover_product_page_history_2021_2022.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="leftover_product_page_history_2y_2021_2023",
                url="https://web.archive.org/web/2022/https://www.principalam.com/us/fund/paltx",
                fixture="leftover_product_page_history_2y_2021_2023.html",
                live=False,
                role="history",
            ),
        ]


class ThriventSource(HtmlTableSource):
    slug = "thrivent"
    display_name = "Thrivent"
    aum_rank = 33
    priority = 33
    notes = (
        "Public paid capital-gains HTML: "
        "https://www.thriventfunds.com/support/tax-resource-center/capital-gains.html "
        "is the full paying-fund 2025 table (Mid Cap Stock Fund LT $4.02; Global Stock "
        "ST $0.35 / LT $2.42; Large Cap Growth LT $0.76). Advisor reprint: "
        "https://fp.thriventfunds.com/resources/tax-resource-center.html. "
        "Tickers are the public Class S identifiers; the HTML table is fund-level. "
        "Official 2024 paying-fund table from Wayback "
        "https://web.archive.org/web/20250218073256/https://www.thriventfunds.com/"
        "support/tax-resource-center/capital-gains.html "
        "(TMSIX 2024 LT $1.33794; THLCX ST $0.27399 / LT $1.03670; "
        "IILGX ST $0.67534 / LT $2.17064). "
        "Official 5y wave 5 in-book leftover: Wayback paid (not estimate) "
        "2023 / 2022 / 2021 capital-gains HTML for Class S names already on "
        "the 2024/2025 book (TAAIX 2023 LT $0.41584 / 2022 LT $0.25595 / "
        "2021 ST $0.44923 / LT $1.31661; IILGX 2023 LT $0.98044; TMSIX 2023 "
        "LT $0.35311). Funds not listed that year stay unmatched — never "
        "invented $0. Low Volatility / International Allocation / other "
        "off-book names omitted. Class A (TAAAX, …) is not mapped. "
        "Official 5y parallel M leftover: TMAIX 2022 / TMCVX 2023 / TSCSX 2023 / "
        "TCAIX 2022–2023 / TSCGX 2022–2024 / IBBFX / TWAIX remain unpublished on "
        "the official CG book (if a fund is not listed, no CG). Product pages "
        "publish trailing-12-month CG already ingested as 2025 — not a multi-year "
        "per-share YE API. Never invent $0 for unlisted leftover years."
    )
    live_limitations = (
        "Family page is public HTML with a 'Thrivent Mutual Fund' header (no ticker column). "
        "Layout can change. Fixture fallback if 0 rows. Live page is the current-year book."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_paid_capital_gains",
                url="https://www.thriventfunds.com/support/tax-resource-center/capital-gains.html",
                fixture="2025_paid_capital_gains.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2024_paid_capital_gains",
                url=(
                    "https://web.archive.org/web/20250218073256/"
                    "https://www.thriventfunds.com/support/tax-resource-center/capital-gains.html"
                ),
                fixture="2024_paid_capital_gains.html",
                live=False,
            ),
            PageSpec(
                name="2023_paid_capital_gains",
                url=(
                    "https://web.archive.org/web/20240221192409id_/"
                    "https://www.thriventfunds.com/support/tax-resource-center/capital-gains.html"
                ),
                fixture="2023_paid_capital_gains.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2022_paid_capital_gains",
                url=(
                    "https://web.archive.org/web/20230327045351id_/"
                    "https://www.thriventfunds.com/support/tax-resource-center/capital-gains.html"
                ),
                fixture="2022_paid_capital_gains.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2021_paid_capital_gains",
                url=(
                    "https://web.archive.org/web/20220521194610id_/"
                    "https://www.thriventfunds.com/support/tax-resource-center/capital-gains.html"
                ),
                fixture="2021_paid_capital_gains.html",
                live=False,
                role="history",
            ),
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
        "and 2024 2024HartfordFundsCapitalGainsDistributions.pdf is the full equity "
        "paying-fund book (HFMCX LT $1.67 / 5.55% of Class I NAV; no-pay list omitted). "
        "Amounts on those PDFs are fund-level; tickers there are public Class A "
        "identifiers only where previously identified (HFMCX / HAIAX / IHGIX). "
        "Wave 12 adds ticker-keyed share-class product pages "
        "https://www.hartfordfunds.com/funds/{slug}.class{N}.html "
        "(2025 YE CG; HDGIX LT $3.9283; HFMIX LT $5.4448; HGIIX LT $6.1237; "
        "~186 new I/C/F/R/Y tickers). Official printed $0.0000 ST stored when "
        "paired with a printed LT. Class A stays on the PDF / alias map "
        "(IHGIX / HAIAX / HFMCX and name-keyed ITHAX / HQIAX) so keys are not forked. "
        "Official 5y gap-fill adds the Tax Center Historical Capital Gains PDF "
        "(2014–2024) for 2021–2024 fund-level Class A / name-keyed amounts "
        "(IHGIX 2021 LT $1.50586 / 2022 LT $1.29738; HAIAX 2021 LT $1.08029 / "
        "2022 LT $1.11577). Share-class I/C/F/R/Y amounts are not copied. "
        "Official printed $0.00000 stored. Sibling 2021–2023 equity PDFs remain HTML."
    )
    live_limitations = (
        "Estimate and final books are PDF. Share-class product pages are HTML; "
        "fixture transcribes the public 10/31 estimate plus finals plus 2025 "
        "product-page classes."
    )

    def pages(self) -> list[PageSpec]:
        dam = (
            "https://www.hartfordfunds.com/dam/en/docs/pub/funddocuments/regulatorydocument/"
        )
        return [
            PageSpec(
                name="2025_estimated_capital_gains",
                url=dam + "Tax%20Center/HMFCapitalGains_December2025EstimateMemo.pdf",
                fixture="2025_estimated_capital_gains.html",
                live=True,
                role="estimate",
                empty_ok=True,
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
            ),
            PageSpec(
                name="2025_share_class_product_pages",
                url="https://www.hartfordfunds.com/funds/divgr.classI.html",
                fixture="2025_share_class_product_page_distributions.html",
                live=False,
            ),
            PageSpec(
                name="2021_2024_historical_capital_gains",
                url=(
                    dam
                    + "Tax%20Center/capgainsdistributions/HistoricalCapitalGainsReport.pdf"
                ),
                fixture="2021_2024_historical_capital_gains.html",
                live=False,
                role="history",
                large_aum_only=False,
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
        "is the September estimate book (WSTAX LT $10.051 / 15.05% of Class A NAV; "
        "Class A tickers; no-pay list omitted). 2025 paid book is the unversioned "
        "SKU CGE-RET-ACT (CGE-RET-ACT-2025 404; Nomura-branded 2025 paid YE; "
        "WSTAX LT $10.603; distinct from CGE-RET estimate). 2024 paid book "
        "https://mim.fgsfulfillment.com/download.aspx?sku=CGE-RET-ACT-2024 "
        "is the full paying-fund table (WSTAX ST $1.108 / LT $8.135; 16 Class A "
        "tickers; no-pay list omitted). 2023 paid book "
        "https://mim.fgsfulfillment.com/download.aspx?sku=CGE-RET-ACT-2023 "
        "is the full paying-fund table (WSTAX LT $5.331; 20 Class A tickers; "
        "no-pay list omitted). 2022 paid book "
        "https://mim.fgsfulfillment.com/download.aspx?sku=CGE-RET-ACT-2022 "
        "(WSTAX LT $12.373; December YE Class A; November munis omitted). "
        "CGE-RET-ACT-2021 404 — overlapping Class A can reach 4y (2022–2025), "
        "not 5y. Official 5y parallel N leftover re-probe (2026-09-13): "
        "CGE-RET-ACT-2021 / CGE-RET-2021 / CGE-RET-ACT-21 still 404. Nomura "
        "product-page Distribution history is Institutional Class JavaScript "
        "(WSTAX Class A not printed — never copy ISTIX $30.863 onto WSTAX). "
        "Literature hub: https://www.macquarie.com/mam/literature."
    )
    live_limitations = "US estimate/paid books are fulfillment PDFs, not an HTML grid."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_capital_gains",
                url="https://mim.fgsfulfillment.com/download.aspx?sku=CGE-RET",
                fixture="2025_estimated_capital_gains.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_paid_capital_gains",
                url="https://mim.fgsfulfillment.com/download.aspx?sku=CGE-RET-ACT",
                fixture="2025_paid_capital_gains.html",
                live=False,
            ),
            PageSpec(
                name="2024_paid_capital_gains",
                url="https://mim.fgsfulfillment.com/download.aspx?sku=CGE-RET-ACT-2024",
                fixture="2024_paid_capital_gains.html",
                live=False,
            ),
            PageSpec(
                name="2023_paid_capital_gains",
                url="https://mim.fgsfulfillment.com/download.aspx?sku=CGE-RET-ACT-2023",
                fixture="2023_paid_capital_gains.html",
                live=False,
            ),
            PageSpec(
                name="2022_paid_capital_gains",
                url="https://mim.fgsfulfillment.com/download.aspx?sku=CGE-RET-ACT-2022",
                fixture="2022_paid_capital_gains.html",
                live=False,
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
        "is the full open-end book (SGENX LT $4.12–$4.17; FEVAX LT $1.77–$1.82). "
        "Class A tickers on the 2025 estimate come from the official 2024 paid PDF "
        "share-class map. Footnote-b monthly/quarterly income estimates omitted "
        "(not $0). Interval / CEF Tactical Municipal Opportunities and Credit "
        "Opportunities omitted. 2024 official paid PDF "
        "https://www.firsteagle.com/sites/default/files/2024-12/2024_Capital_Gains_%20Income_Distributions.pdf "
        "is the full share-class book (SGENX ST $0.027 / LT $2.038; 40 tickers). "
        "Product-page history "
        "https://www.firsteagle.com/funds/global-fund (SGENX 2025 LT $4.654 / "
        "2023 LT $1.407), overseas-fund (SGOVX), and us-fund (FEVAX). "
        "2025 family paid PDF sibling URLs still 404 (2025-12 and fei-documents "
        "open-end paths). Official 2025 paid rows now come from product-page "
        "grids: Global / Overseas / U.S. / Rising Dividend / Gold / Global Income "
        "Builder / Small Cap Opportunity / Global Real Assets / U.S. Smid Cap "
        "(SGENX LT $4.654 / income $2.883; FEGRX income $3.129 / LT $4.654; "
        "FEFAX ST $0.339 / LT $2.015). In-universe share classes on that "
        "product-page book keep official ordinary income + CG (not only the "
        "SGENX / SGOVX / FEVAX large-AUM heroes). Interval / CEF omitted. "
        "9/30/2025 estimate PDF income ranges stay preliminary (SGENX "
        "$2.80–$2.85) — never invented. Footnote-b monthly/quarterly income "
        "estimates still omitted (no printed $). "
        "Official 2025 ETF paid PDF "
        "https://www.firsteagle.com/sites/default/files/fei-documents/"
        "2025-Capital-Gains-and-Income%20Distributions-First%20Eagle-ETFs.pdf "
        "(FEGE income $0.589 / ST $0.000 / LT $0.000; FEOE income $0.738 / ST $0.000 / LT $0.000). "
        "2021–2022 paid PDFs were not a stable public file. Growth of $X added "
        "for FEFAX. "
        "Official 5y wave 5 in-book leftover: Class A product-page history "
        "via Wayback id_ snapshots after live firsteagle.com pages 403 "
        "(SGENX 2022 LT $2.358 / 2021 LT $2.749; SGOVX 2022 income $0.018 / "
        "LT $0.794; FEFAX 2023 ST $0.008 / LT $1.661; SGGDX 2021 income "
        "$0.221). Official 5y leftover-class densify: live product pages "
        "returned 200 and publish class-level C / I / R6 history "
        "(SGIIX 2022 income $0.213 / LT $2.358; FEGRX 2021 income $1.458 / "
        "LT $2.749; FESGX 2021 income $0.588 / LT $2.749; SGOIX 2025 income "
        "$1.717 / LT $0.923). Class A 5y heroes are not re-emitted. GRA / "
        "Smid issuer tables start 2022 (no 2021). Official printed $0.000 "
        "stored. High Yield Municipal leftover YE rows are the issuer-printed "
        "zeros. Short Duration High Yield Municipal has no 2021–2023 on the "
        "issuer table — unmatched."
    )
    live_limitations = "Family estimate book is PDF. Paid history is on public product pages."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="tax_information_hub",
                url="https://www.firsteagle.com/tax-information",
                fixture="tax_information_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_estimated_income_and_gains",
                url="https://www.firsteagle.com/sites/default/files/fei-documents/FEF_Ordinary_Income_Gains_Estimates.pdf",
                fixture="2025_estimated_income_and_gains.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_etf_paid_year_end",
                url=(
                    "https://www.firsteagle.com/sites/default/files/fei-documents/"
                    "2025-Capital-Gains-and-Income%20Distributions-First%20Eagle-ETFs.pdf"
                ),
                fixture="2025_etf_paid_year_end.html",
                live=False,
                role="history",
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
            ),
            PageSpec(
                name="2023_paid_year_end",
                url="https://www.firsteagle.com/funds/global-fund",
                fixture="2023_paid_year_end.html",
                live=False,
                large_aum_only=True,
            ),
            PageSpec(
                name="product_page_history_gapfill",
                url=(
                    "https://web.archive.org/web/20231005012234id_/"
                    "https://www.firsteagle.com/funds/global-fund"
                ),
                fixture="product_page_history_gapfill.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="product_page_history_leftover_classes",
                url="https://www.firsteagle.com/funds/global-fund",
                fixture="product_page_history_leftover_classes.html",
                live=False,
                role="history",
                large_aum_only=False,
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
        "is the full GMO Trust book (Quality Fund GQETX ST $0.2331 / LT $0.7242; "
        "published $0.000 stored; notes C/D omitted). July/December 2025 "
        "Trust sibling filenames 404. Official GMO ETF Trust 2025 prior-year "
        "1099-DIV summary "
        "https://www.gmo.com/globalassets/documents---manually-loaded/documents/"
        "distribution-estimates-and-dates/GMO-Trust-Summary-Distribution_Prior-Year/ "
        "is December income plus any-month ST (BCHI Sep/Dec ST; INVG Dec ST). "
        "Box 2a LT $0 omitted, not stored as $0. Official 5y parallel Q "
        "leftover: US Trust NAVs-and-Distributions workbooks from the GMO "
        "document library add paid Class III history for in-book leftovers "
        "GQETX (Quality), GMUEX (U.S. Equity), and GTMIX (International "
        "Opportunistic Value). Heroes: GQETX 2025-12-12 OI $0.2832 / ST "
        "$0.1466 / LT $2.6256; GMUEX 2025-12-05 OI $0.1346 / LT $0.9849 "
        "(ST N/A omitted); GTMIX 2025-12-12 OI $0.5335 / ST $0.8593 / LT "
        "$1.5312. Each workbook prints one date stored as record / ex / "
        "payable. Printed N/A omitted, not invented as $0. 2026 July paid "
        "rows skipped so they do not collide with the live July 2026 "
        "estimate book. GMO Australia skipped. Other Trust share classes "
        "and Small Cap Quality are not in-book leftovers and are not "
        "attached. ETF leftover years stay on the existing prior-year tax "
        "fixture (URL contains distribution-estimates — "
        "preliminary_estimate). Class-level Class III only — never copy "
        "I / IV / R6 / VI. Additive upserts; no schema change."
    )
    live_limitations = "Estimate book is PDF. Fixture transcribes public Trust-class and ETF YE rows."

    def pages(self) -> list[PageSpec]:
        docs = (
            "https://www.gmo.com/globalassets/documents---manually-loaded/documents/"
            "distribution-estimates-and-dates"
        )
        return [
            PageSpec(
                name="2026_july_distribution_estimates",
                url=f"{docs}/gmo-trust-funds---july-2026-distribution-estimate.pdf",
                fixture="2026_july_distribution_estimates.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_etf_year_end_tax",
                url=f"{docs}/GMO-Trust-Summary-Distribution_Prior-Year/",
                fixture="2025_etf_year_end_tax.html",
                live=False,
            ),
            PageSpec(
                name="leftover_trust_paid_navs_parallel_q",
                url=(
                    "https://www.gmo.com/globalassets/"
                    "documents-from-parcels-json/"
                    "quality-fund_mutual-fund_navs-and-distributions/"
                ),
                fixture="leftover_trust_paid_navs_parallel_q.html",
                live=False,
                role="history",
                large_aum_only=False,
            ),
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
        "2026-06-29 income $0.338342). 2025 ICI-style Year-End Tax Reporting PDF "
        "https://www.artisanpartners.com/content/dam/documents/distributions/"
        "Year-End-Tax-Reporting-Information-2025.pdf is column-safe (30-token "
        "layout; income / ST / LT at tokens 4 / 5 / 12). December income plus "
        "any-month ST/LT rows; monthly non-December income omitted so illustration "
        "does not sum. 2024 sibling Year-End-Tax-Reporting-Information-2024.pdf "
        "is column-safe with LT at token 11 (one Box 1b column omitted vs 31-token; "
        "ARTIX ST $0.456695 / LT $2.067175). Official 5y max-reach transcribes the "
        "2021–2023 ICI Primary Layout PDFs (Investor / Advisor / Institutional "
        "sections; token order varies by year) to named-column CSVs — ARTIX 2021 "
        "LT $5.498 / 2022 LT $0.306132 / 2023 LT $0.20663. In-book tickers only. "
        "December / November YE income plus any-month ST/LT; monthly non-December "
        "income-only omitted so illustration does not sum. "
        "Official 5y parallel I leftover: same ICI Primary PDFs, leftover "
        "November YE income / Advisor+Inst 2024–2025 rows the December extract "
        "omitted, plus official printed $0 HTML (ICI parser skips $0). Heroes: "
        "APDIX 2025 OI $0.643107 / ST $1.111827 / LT $5.017255; APHIX 2025 OI "
        "$0.673190 / ST $1.111827 / LT $5.017255; ARTHX 2022 OI $0.143480; "
        "ARTJX 2022+2023 printed $0.000000000; ARTZX 2021 OI $0.200000 / 2022 "
        "OI $0.114735. APDRX / ARTRX / APHRX 2022 absent from the ICI PDF. "
        "2021 International Explorer / Value Income / debt inception walls. "
        "2023 Mid / Small / Discovery / Focus unpublished on the ICI PDF. "
        "Year selector for older HTML YE tables is JavaScript — skip SPA. "
        "NRA / DRD PDFs are tax-character layouts, not ingested as CG."
    )
    live_limitations = (
        "Live YTD page is public HTML; year-end equity capital-gains sit behind a year selector. "
        "2021–2025 ICI-style Year-End Tax Reporting PDFs are the full-book fixtures. "
        "Leftover years are the same official ICI PDFs plus printed-$0 HTML."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="ytd_paid_distributions",
                url="https://www.artisanpartners.com/individual-investors/resources/tax-center/distributions.html",
                fixture="ytd_paid_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="ici_primary_2025",
                url=(
                    "https://www.artisanpartners.com/content/dam/documents/distributions/"
                    "Year-End-Tax-Reporting-Information-2025.pdf"
                ),
                fixture="ici_primary_2025.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
            ),
            PageSpec(
                name="ici_primary_2024",
                url=(
                    "https://www.artisanpartners.com/content/dam/documents/distributions/"
                    "Year-End-Tax-Reporting-Information-2024.pdf"
                ),
                fixture="ici_primary_2024.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
            ),
            PageSpec(
                name="ici_primary_2023",
                url=(
                    "https://www.artisanpartners.com/content/dam/documents/distributions/"
                    "Year-End-Tax-Reporting-Information-2023.pdf"
                ),
                fixture="ici_primary_2023.csv",
                live=False,
                parser="ici",
                role="history",
                large_aum_only=False,
            ),
            PageSpec(
                name="ici_primary_2022",
                url=(
                    "https://www.artisanpartners.com/content/dam/documents/distributions/"
                    "Year-End-Tax-Reporting-Information-2022.pdf"
                ),
                fixture="ici_primary_2022.csv",
                live=False,
                parser="ici",
                role="history",
                large_aum_only=False,
            ),
            PageSpec(
                name="ici_primary_2021",
                url=(
                    "https://www.artisanpartners.com/content/dam/documents/distributions/"
                    "Year-End-Tax-Reporting-Information-2021.pdf"
                ),
                fixture="ici_primary_2021.csv",
                live=False,
                parser="ici",
                role="history",
                large_aum_only=False,
            ),
            PageSpec(
                name="ici_leftover_parallel_i",
                url=(
                    "https://www.artisanpartners.com/content/dam/documents/distributions/"
                    "Year-End-Tax-Reporting-Information-2025.pdf"
                ),
                fixture="ici_leftover_parallel_i.csv",
                live=False,
                parser="ici",
                role="history",
                large_aum_only=False,
            ),
            PageSpec(
                name="ici_leftover_printed_zero",
                url=(
                    "https://www.artisanpartners.com/content/dam/documents/distributions/"
                    "Year-End-Tax-Reporting-Information-2022.pdf"
                ),
                fixture="ici_leftover_printed_zero.html",
                live=False,
                role="history",
                large_aum_only=False,
            ),
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
        "is the full paying-fund table (Growth Fund CVGRX LT $4.07 / 7.76% of Class A NAV; "
        "all-dash omitted). 2024 sibling "
        "2024-calamos-estimated-capital-gains.pdf (CVGRX ST $1.24 / LT $1.84). "
        "2023 sibling filename 404. Wave 15 official 2025 ETF paid PDF "
        "2025-calamos-exchange-traded-funds-capital-gains.pdf (CANQ ST $0.08; "
        "CCEF LT $0.19; ex/record 12/23/2025). Published dashes / 0.00% of NAV "
        "omitted. Structured Protection and SROI all-dash PDFs noted, not invented. "
        "Official 5y parallel I leftover: paid (not estimate) Class A capital-gains "
        "PDFs 2025 live / 2024 live / 2023–2022 Wayback plus Class A product-page "
        "Total Capital Gains for 2021 (2021 paid PDF 404). Heroes: CVGRX 2025 LT "
        "$4.17 / 2021 $4.9490; CPLSX 2025 ST $0.62 / LT $0.03 / 2021 printed "
        "$0.0000; CCVIX 2025 ST $0.65 / LT $1.60 / 2021 $3.1893. Official printed "
        "$0.00 on 2022–2023 stored. 2024/2025 PDF dashes omitted. CAGCX 2024 "
        "product-page printed $0.0000. CAISX 2021 / 2024 and CMRAX 2021 / 2022 "
        "unpublished. ETF leftover: CCEF 2024 ST $0.09; CANQ 2024 dashes omitted."
    )
    live_limitations = (
        "Estimate book is PDF. Paid leftover books are official capital-gains PDFs "
        "plus Class A product-page Total Capital Gains. Fixture transcribes public "
        "Class A / in-book ETF rows."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_capital_gains",
                url="https://www.calamos.com/globalassets/media/documents/tax-center/2025-calamos-estimated-capital-gains.pdf",
                fixture="2025_estimated_capital_gains.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2024_estimated_capital_gains",
                url="https://www.calamos.com/globalassets/media/documents/tax-center/2024-calamos-estimated-capital-gains.pdf",
                fixture="2024_estimated_capital_gains.html",
                live=False,
                large_aum_only=True,
            ),
            PageSpec(
                name="2025_etf_paid_capital_gains",
                url="https://www.calamos.com/globalassets/media/documents/tax-center/2025-calamos-exchange-traded-funds-capital-gains.pdf",
                fixture="2025_etf_paid_capital_gains.html",
                live=False,
                role="history",
                large_aum_only=False,
            ),
            PageSpec(
                name="leftover_2025_paid_capital_gains",
                url="https://www.calamos.com/globalassets/media/documents/tax-center/2025-calamos-capital-gains.pdf",
                fixture="leftover_2025_paid_capital_gains.html",
                live=False,
                role="history",
                large_aum_only=False,
            ),
            PageSpec(
                name="leftover_2024_paid_capital_gains",
                url="https://www.calamos.com/globalassets/media/documents/tax-center/2024-calamos-capital-gains.pdf",
                fixture="leftover_2024_paid_capital_gains.html",
                live=False,
                role="history",
                large_aum_only=False,
            ),
            PageSpec(
                name="leftover_2023_paid_capital_gains",
                url=(
                    "https://web.archive.org/web/20240416083227id_/"
                    "https://www.calamos.com/globalassets/media/documents/tax-center/"
                    "2023-calamos-capital-gains.pdf"
                ),
                fixture="leftover_2023_paid_capital_gains.html",
                live=False,
                role="history",
                large_aum_only=False,
            ),
            PageSpec(
                name="leftover_2022_paid_capital_gains",
                url=(
                    "https://web.archive.org/web/20230206122312id_/"
                    "https://www.calamos.com/globalassets/media/documents/tax-center/"
                    "2022-calamos-capital-gains.pdf"
                ),
                fixture="leftover_2022_paid_capital_gains.html",
                live=False,
                role="history",
                large_aum_only=False,
            ),
            PageSpec(
                name="leftover_2021_product_page_capital_gains",
                url="https://www.calamos.com/funds/us/en/cvgrx",
                fixture="leftover_2021_product_page_capital_gains.html",
                live=False,
                role="history",
                large_aum_only=False,
            ),
            PageSpec(
                name="leftover_2024_etf_paid_capital_gains",
                url="https://www.calamos.com/globalassets/media/documents/tax-center/2024-calamos-exchange-traded-funds-capital-gains.pdf",
                fixture="leftover_2024_etf_paid_capital_gains.html",
                live=False,
                role="history",
                large_aum_only=False,
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
        "is the full listed-fund estimate table (Core Growth WGROX LT $6.01 / 7.71% of NAV). "
        "2024 estimate sibling "
        "WGI_2024_Yr_End_Dist_Estimates.pdf 404. Paid YE from "
        "https://wasatchglobal.com/wasatch-core-growth-fund-investor/ "
        "(WGROX 2025 LT $6.345749; 2024 LT $8.282696; 2022 LT $0.457965). "
        "Product page has no 2023 YE row — gap, not invented. "
        "Parallel-P leftover paid year-end from official product-page Distributions History "
        "(https://wasatchglobal.com/wasatch-*-fund-investor/ + Hoisington US Treasury): "
        "WHOSX 2021–2025 OI $0.067651 / $0.078728 / $0.092987 / $0.100350 / $0.113996; "
        "WMCVX 2021–2025 (2025 OI $0.000350 + LT $0.554075); "
        "WGROX 2021 ST/LT $1.378726 / $14.455281 (2023 unpublished — official 2023 tax letter: remaining funds no distribution); "
        "WAAEX 2021+2025; WAIGX 2021+2024+2025; WAIVX 2024–2025 (inception 11/29/24); "
        "FMIEX 2023+2025. Institutional siblings are not in the NAV book (product freeze). "
        "WAEMX/WAGOX/WAINX/WAIOX/WAMVX/WAUSX unpaid years stay unmatched. "
        "Registered as the Putnam replacement: Putnam.com now redirects to Franklin Templeton."
    )
    live_limitations = (
        "Estimate book is PDF. Paid history is on the public product page. "
        "Live GET is sometimes Cloudflare 202; fixture is the book."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_year_end_distribution_estimates",
                url="https://wasatchglobal.com/wp-content/uploads/2025/11/WGI_2025_Yr_End_Dist_Estimates.pdf",
                fixture="2025_year_end_distribution_estimates.html",
                live=True,
                role="estimate",
                empty_ok=True,
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
            PageSpec(
                name="leftover_paid_year_end_parallel_p",
                url="https://wasatchglobal.com/wasatch-small-cap-growth-fund-investor/",
                fixture="leftover_paid_year_end_parallel_p.html",
                live=True,
                role="history",
                large_aum_only=False,
            ),
        ]
