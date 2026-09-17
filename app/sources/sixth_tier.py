from __future__ import annotations

from app.sources.html_source import HtmlTableSource, PageSpec


class SeiSource(HtmlTableSource):
    slug = "sei"
    display_name = "SEI"
    aum_rank = 51
    priority = 51
    notes = (
        "Public 11/20/2025 estimate PDF: "
        "https://www.seic.com/sites/default/files/2025-11/"
        "SEI%20Capital%20gains%20distribution%20estimates_11.20.2025.pdf "
        "is the full paying-fund book "
        "(e.g. SIMT Large Cap Growth ST $1.189 / LT $8.018 / 16.16% of NAV; "
        "SIMT Mid-Cap ST $0.080 / LT $5.609 / 17.81% of NAV). "
        "Equity record 12/16/2025, ex 12/17/2025, pay 12/18/2025. "
        "The PDF is fund-level (ETF tickers kept when printed in the name). "
        "All-dash / not-expected rows are omitted. "
        "2024 estimate PDF: "
        "https://www.seic.com/sites/default/files/2024-10/SEI-2024-Capital-Gains-Distribution-Estimates.pdf "
        "(SIMT Large Cap Growth ST $1.541 / LT $7.596 / 15.46% of NAV). "
        "Official 5y parallel N leftover: 2025 paid/final PDF "
        "https://www.seic.com/sites/default/files/2025-12/"
        "2025%20SEI%20Capital%20gains%20distribution_Final.pdf "
        "(SIMT Large Cap Growth ST $1.370 / LT $8.053; QALT ST $0.248 / LT $0.372). "
        "Existing estimate-book identities only. 2021–2024 sibling final PDFs 404; "
        "Canadian tax-factor PDFs omitted (non-US)."
    )
    live_limitations = "Estimate book is PDF. Fixture transcribes the public paying-fund table."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_capital_gains",
                url=(
                    "https://www.seic.com/sites/default/files/2025-11/"
                    "SEI%20Capital%20gains%20distribution%20estimates_11.20.2025.pdf"
                ),
                fixture="2025_estimated_capital_gains.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2024_estimated_capital_gains",
                url="https://www.seic.com/sites/default/files/2024-10/SEI-2024-Capital-Gains-Distribution-Estimates.pdf",
                fixture="2024_estimated_capital_gains.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2025_paid_capital_gains",
                url=(
                    "https://www.seic.com/sites/default/files/2025-12/"
                    "2025%20SEI%20Capital%20gains%20distribution_Final.pdf"
                ),
                fixture="2025_paid_capital_gains.html",
                live=False,
                role="history",
                large_aum_only=False,
            ),
        ]


class BrownAdvisorySource(HtmlTableSource):
    slug = "brown_advisory"
    display_name = "Brown Advisory"
    aum_rank = 52
    priority = 52
    notes = (
        "Public 2025 capital-gains estimate PDF: "
        "https://www.brownadvisory.com/sites/default/files/2025-10/"
        "2025-Capital-Gain-Distribution-Update.pdf "
        "is the full listed-fund book "
        "(e.g. Flexible Equity Institutional BAFFX ST $0.23 / LT $2.17; "
        "Growth Equity Institutional BAFGX ST $0.34 / LT $7.86; "
        "Sustainable Growth Institutional BAFWX ST $0.07 / LT $10.90). "
        "Institutional / Investor / Advisor columns are ingested when printed. "
        "Tickers only for previously identified Institutional classes. "
        "Wave 16 leftover Investor / Advisor / Institutional tickers come from "
        "official brownadvisory.com/mf/funds product pages (BIAFX / BAFAX / "
        "BIAWX / BAWAX / BAFLX) paired with the same printed amounts — existing "
        "BAFFX / BAFGX / BAFWX / BVALX are not re-emitted. Mid-Cap Growth and "
        "WMC Japan Equity product pages 404 this session. "
        "Record/declaration 12/12/2025; ex/reinvest and pay 12/15/2025. "
        "2024 schedule: https://www.brownadvisory.com/sites/default/files/2024_Capital_Gain_Distribution.pdf "
        "(Flexible Equity Institutional BAFFX ST $0.15 / LT $1.72). "
        "Parallel L leftover: 2024/2025 family books stay estimate-stage "
        "(titles print Estimated / Update — not paid YE finals). 2021–2023 "
        "Capital_Gain_Distribution sibling PDFs 404; Wayback CDX of "
        "brownadvisory.com/sites/default/files/*Capital*Gain* empty this "
        "session. Product pages have no harvestable paid Distribution History. "
        "Leftover years stay unmatched — never invent $0."
    )
    live_limitations = (
        "Estimate book is PDF with Institutional / Investor / Advisor columns. "
        "Fixture transcribes public Institutional-class rows."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_capital_gains",
                url=(
                    "https://www.brownadvisory.com/sites/default/files/2025-10/"
                    "2025-Capital-Gain-Distribution-Update.pdf"
                ),
                fixture="2025_estimated_capital_gains.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2024_capital_gains",
                url="https://www.brownadvisory.com/sites/default/files/2024_Capital_Gain_Distribution.pdf",
                fixture="2024_capital_gains.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="remaining_share_class_estimates",
                url="https://www.brownadvisory.com/mf",
                fixture="remaining_share_class_estimates.html",
                live=False,
                role="history",
                large_aum_only=False,
            ),
        ]


class WilliamBlairSource(HtmlTableSource):
    slug = "william_blair"
    display_name = "William Blair"
    aum_rank = 53
    priority = 53
    notes = (
        "Resources hub: https://im.williamblair.com/investments/resources-us "
        "Public 2025 paid annual distributions PDF (Class I / N / R6): "
        "https://media.im.williamblair.com/v1/media/edge/images/"
        "williamblaib9c8-wbim74f8-wbimprod42cd-8345/media/documents/resources/us/"
        "distributions/william-blair-funds---annual-distributions-2025---class-i-n-and-r6.pdf "
        "(e.g. Growth Class I BGFIX ST $0.02557 / LT $2.91999 / 31% of NAV; "
        "Large Cap Growth Class I LCGFX LT $2.57994 / 8% of NAV; "
        "Global Leaders Class I WGFIX LT $5.52579 / 47% of NAV). "
        "Record 12/17/2025; ex 12/18/2025; pay 12/19/2025. "
        "PDF text extraction reverses amount/name columns — not column-safe "
        "for a full-book auto-extract; Class I flagship rows remain. "
        "2024 paid Class I/N/R6: "
        "https://media.im.williamblair.com/v1/media/edge/images/"
        "williamblaib9c8-wbim74f8-wbimprod42cd-8345/media/documents/resources/us/"
        "distributions/2024-yearend-distributions-and-dividends--class-i-n-and-r6.pdf "
        "(Growth Class I BGFIX LT $3.03562 / 19% of NAV). "
        "Wave 16 leftover Class I / N / R6 tickers are official "
        "im.williamblair.com product-page title identifiers paired with the "
        "same 2025 I/N/R6 paid PDF (WSMDX ST $0.24654 / LT $0.52390; WBSNX "
        "ST $0.64563 / LT $1.88947; BGFRX ST $0.02557 / LT $2.91999). Existing "
        "Class I flagships BGFIX / LCGFX / WGFIX / WBSIX are not re-emitted. "
        "Official 5y max-reach: 2021–2023 Class I/N/R6 paid PDFs plus leftover "
        "2024 share classes from the same official book (BGFIX 2021 LT $1.41651 / "
        "2022 LT $0.36515 / 2023 LT $1.23527; WBGSX 2024 LT $3.03562). Class N/I "
        "income is class-level; ST/LT on the N&I table are the official shared "
        "columns. Class R6 amounts come from the Class R6 table — never copied "
        "from Class I. 2024 Class I flagships stay on 2024_annual_distributions."
    )
    live_limitations = "Year-end book is PDF. Text extract is wrap-unsafe; fixture keeps Class I flagships."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_annual_distributions",
                url=(
                    "https://media.im.williamblair.com/v1/media/edge/images/"
                    "williamblaib9c8-wbim74f8-wbimprod42cd-8345/media/documents/"
                    "resources/us/distributions/"
                    "william-blair-funds---annual-distributions-2025---class-i-n-and-r6.pdf"
                ),
                fixture="2025_annual_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2024_annual_distributions",
                url=(
                    "https://media.im.williamblair.com/v1/media/edge/images/"
                    "williamblaib9c8-wbim74f8-wbimprod42cd-8345/media/documents/"
                    "resources/us/distributions/"
                    "2024-yearend-distributions-and-dividends--class-i-n-and-r6.pdf"
                ),
                fixture="2024_annual_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2021_2024_annual_distributions",
                url=(
                    "https://media.im.williamblair.com/v1/media/edge/images/"
                    "williamblaib9c8-wbim74f8-wbimprod42cd-8345/media/documents/"
                    "resources/us/distributions/"
                    "2021-yearend-distributions-and-dividends--class-i-n-and-r6.pdf"
                ),
                fixture="2021_2024_annual_distributions.html",
                live=False,
                role="history",
                large_aum_only=False,
            ),
            PageSpec(
                name="remaining_share_class_annual_distributions",
                url=(
                    "https://media.im.williamblair.com/v1/media/edge/images/"
                    "williamblaib9c8-wbim74f8-wbimprod42cd-8345/media/documents/"
                    "resources/us/distributions/"
                    "william-blair-funds---annual-distributions-2025---class-i-n-and-r6.pdf"
                ),
                fixture="remaining_share_class_annual_distributions.html",
                live=False,
                role="history",
                large_aum_only=False,
            ),
            PageSpec(
                name="distributions_hub",
                url="https://im.williamblair.com/investments/resources-us",
                fixture="distributions_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
        ]


class VaneckSource(HtmlTableSource):
    slug = "vaneck"
    display_name = "VanEck"
    aum_rank = 54
    priority = 54
    notes = (
        "Public 2025 mutual-fund estimate PDF: "
        "https://www.vaneck.com/us/en/vaneck-funds-estimated-yearend-distributions-2025.pdf "
        "is the full listed mutual-fund book "
        "(e.g. Morningstar Wide Moat I MWMIX forecasted ST $1.94 / LT $1.68; "
        "International Investors Gold A INIVX income $1.56 / no CG). "
        "Printed None for capital gains is omitted. CM Commodity ‡ estimates-to-come omitted. "
        "Most funds record 12/17/2025, ex/pay 12/18/2025. "
        "ETF estimate reprint: https://www.vaneck.com/us/en/vaneck-etfs-yearend-distributions-2025.pdf "
        "(CLOB ST $0.064; CLOI ST $0.007 / LT $0.029; EINC LT $1.016; printed None omitted). "
        "2024 paid ETF YE: https://www.vaneck.com/us/en/vaneck-etfs-yearend-distributions-2024.pdf "
        "(GDX income $0.4025; SMH income $1.0713; MOAT income $1.2675; "
        "IBOT ST $0.9104 / LT $0.0112; MOTG LT $1.3793; all-None AFK/DGIN/VNM omitted). "
        "Official 2024 paid mutual-fund PDF "
        "https://www.vaneck.com/us/en/vaneck-funds-yearend-distributions-2024.pdf "
        "(INIVX income $0.7750; MWMIX ST $1.4731 / LT $1.4325; printed None omitted; EMRCX all-None omitted). "
        "Official 2023 equity-ETF paid PDF "
        "https://www.vaneck.com/us/en/vaneck-equity-etfs-2023-year-end-distributions.pdf "
        "(GDX income $0.5001; SMH $1.0427; IBOT ST $0.6716; printed None / all-None CNXT/DAPP/REMX omitted). "
        "Official 2023 mutual-fund paid PDF "
        "https://www.vaneck.com/us/en/vaneck-funds-yearend-distributions-2023.pdf "
        "(INIVX income $0.0102; MWMIX ST $1.6352; printed None / IIGCX all-None omitted). "
        "Official 2025 paid YE PDF "
        "https://www.vaneck.com/us/en/vaneck-funds-yearend-distributions-2025.pdf "
        "(INIVX income $1.5675; MWMIX ST $1.9529 / LT $1.6944; GDX $0.6331; "
        "MOTG ST $1.8899 / LT $4.0549; printed None / all-None BUZZ/DAPP omitted; "
        "RAAX/LFEQ/CMCI finals-to-come omitted). "
        "Official 5y leftover densify reads the later "
        "https://www.vaneck.com/us/en/vaneck-funds-2025-yearend-dividends-distributions.pdf "
        "for leftover CM Commodity Index classes (CMCAX 12/29 OI $1.0825 and "
        "12/23 OI $5.2074; COMIX $1.0825 / $5.4279; CMCYX $1.0825 / $5.3910). "
        "MOTE / GHACX 2025 still absent — unmatched. "
        "Official 5y wave-3 tax-center PDFs (not year-alias URLs, which still "
        "serve HTML): 2022 ETF "
        "https://www.vaneck.com/us/en/vaneck-etfs-2022-yearend-dividends-distributions.pdf "
        "(GDX income $0.4762; SMH $2.4010; MOAT $0.8119; printed None / * monthly "
        "/ ** quarterly annual-omitted rows dropped) and 2021 ETF "
        "https://www.vaneck.com/us/en/vaneck-etfs-2021-yearend-distributions-fixed-income-and-equity.pdf "
        "(GDX $0.5348; SMH $1.5733; MOAT $0.8227) plus 2022 MF "
        "https://www.vaneck.com/us/en/vaneck-funds-2022-yearend-dividends-distributions.pdf "
        "(MWMIX ST $0.7455 / LT $1.9311; INIVX 2022 all-None omitted) and 2021 MF "
        "https://www.vaneck.com/us/en/vaneck-funds-2021-yearend-dividends-distributions.pdf "
        "(INIVX income $0.6603; MWMIX ST $2.3655 / LT $1.7611). "
        "Parallel 5y sweep B re-read leftover years on the same official PDFs: "
        "AFK/VNM 2024, REMX 2023, INIVX/INIIX/INIYX 2022, GLIN/GMET 2021, "
        "RSX/RSXJ 2022, and MOTE 2025 stay issuer-printed None / absent — "
        "unmatched, not $0. Parallel O leftover densify reads official ETF "
        "year-end tax guides plus the later 2025 paid PDF for leftover years "
        "those YE PDFs omitted (EINC 2021-11-19 OI $0.390850 / 2022-11-07 "
        "$0.125200 / 2023-11-07 $0.378400 / 2024-11-06 $0.664900 and 2025-12-29 "
        "LT $0.9843; LFEQ 2023-12-29 $0.625000 / 2025-12-29 $0.4900; RAAX "
        "2023-12-29 $0.935700 / 2025-12-29 $0.8163; EGPT 2024-03-27 $0.031200; "
        "YUMY 2024-03-21 $0.050000; CLOI 2025-12-29 OI $0.2332 / ST $0.0070 / "
        "LT $0.0279; CLOB 2025-12-29 OI $0.2630 / ST $0.0641; CMCI 2025-12-30 "
        "$2.3700). Tax-guide monthly CLOI/CLOB annual totals without a printed "
        "calendar day omitted. AFK/VNM 2024, REMX 2023, GLIN/GMET 2021, "
        "MOTE/GHACX 2025 stay unpublished. WAVE AH leftover re-probe "
        "(2026-09-17): VanEck ETF Trust FYE Dec 31 2024 N-CSR Financial "
        "Highlights print dashes for leftover missing years (AFK / VNM 2024; "
        "REMX 2023; GLIN / GMET 2021; RSX / RSXJ 2022). INIVX Class A 2022 "
        "N-CSR dash. 2025 paid YE PDFs still omit EGPT / MOTE / GHACX "
        "(printed None / absent). Hub: "
        "https://www.vaneck.com/us/en/resources/etf-distributions/"
    )
    live_limitations = (
        "Family estimate books are PDF. Weekly walk uses the MF estimate PDF, "
        "ETF estimate PDF, and ETF distributions hub."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_year_end_distributions",
                url="https://www.vaneck.com/us/en/vaneck-funds-estimated-yearend-distributions-2025.pdf",
                fixture="2025_estimated_year_end_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_etf_year_end_estimates",
                url="https://www.vaneck.com/us/en/vaneck-etfs-yearend-distributions-2025.pdf",
                fixture="2025_etf_year_end_estimates.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="etf_distributions_hub",
                url="https://www.vaneck.com/us/en/resources/etf-distributions/",
                fixture="etf_distributions_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2024_etf_year_end_distributions",
                url="https://www.vaneck.com/us/en/vaneck-etfs-yearend-distributions-2024.pdf",
                fixture="2024_etf_year_end_distributions.html",
                live=False,
            ),
            PageSpec(
                name="2024_funds_year_end_distributions",
                url="https://www.vaneck.com/us/en/vaneck-funds-yearend-distributions-2024.pdf",
                fixture="2024_funds_year_end_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2023_etf_year_end_distributions",
                url="https://www.vaneck.com/us/en/vaneck-equity-etfs-2023-year-end-distributions.pdf",
                fixture="2023_etf_year_end_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2023_funds_year_end_distributions",
                url="https://www.vaneck.com/us/en/vaneck-funds-yearend-distributions-2023.pdf",
                fixture="2023_funds_year_end_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2025_funds_year_end_distributions",
                url="https://www.vaneck.com/us/en/vaneck-funds-yearend-distributions-2025.pdf",
                fixture="2025_funds_year_end_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="leftover_2025_cm_commodity",
                url="https://www.vaneck.com/us/en/vaneck-funds-2025-yearend-dividends-distributions.pdf",
                fixture="leftover_2025_cm_commodity.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="leftover_parallel_o_tax_guide_paid",
                url="https://www.vaneck.com/us/en/resources/tax-center/2024-vaneck-etfs-year-end-tax-guide.pdf",
                fixture="leftover_parallel_o_tax_guide_paid.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="leftover_parallel_o_2025_later_paid",
                url="https://www.vaneck.com/us/en/vaneck-funds-2025-yearend-dividends-distributions.pdf",
                fixture="leftover_parallel_o_2025_later_paid.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2025_etf_year_end_distributions",
                url="https://www.vaneck.com/us/en/vaneck-funds-yearend-distributions-2025.pdf",
                fixture="2025_etf_year_end_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2022_etf_year_end_distributions",
                url="https://www.vaneck.com/us/en/vaneck-etfs-2022-yearend-dividends-distributions.pdf",
                fixture="2022_etf_year_end_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2021_etf_year_end_distributions",
                url="https://www.vaneck.com/us/en/vaneck-etfs-2021-yearend-distributions-fixed-income-and-equity.pdf",
                fixture="2021_etf_year_end_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2022_funds_year_end_distributions",
                url="https://www.vaneck.com/us/en/vaneck-funds-2022-yearend-dividends-distributions.pdf",
                fixture="2022_funds_year_end_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2021_funds_year_end_distributions",
                url="https://www.vaneck.com/us/en/vaneck-funds-2021-yearend-dividends-distributions.pdf",
                fixture="2021_funds_year_end_distributions.html",
                live=False,
                role="history",
            ),
        ]


class WisdomtreeSource(HtmlTableSource):
    slug = "wisdomtree"
    display_name = "WisdomTree"
    aum_rank = 55
    priority = 55
    notes = (
        "Hub: https://www.wisdomtree.com/investments/resource-library/"
        "2025-estimated-capital-gains-distributions "
        "Public 12/10/2025 final capital-gains PDF: "
        "https://www.wisdomtree.com/investments/-/media/us-media-files/documents/about/pdf/2025/"
        "wisdomtree-etfs-declare-final-capital-gains-distributions-2025.pdf "
        "lists the family; payers are ingested "
        "(e.g. Target Range GTR ST $0.84657 / 3.23% of NAV; "
        "True Emerging Markets XC ST $0.72040 / LT $2.49286 / 9.13% of NAV; "
        "Equity Premium Income WTPI LT $0.72183 / 2.14% of NAV). "
        "Dashed (no 2025 CG) rows are omitted. Ex/record 12/10/2025; pay 12/12/2025. "
        "Official 2024 sibling "
        "https://www.wisdomtree.com/investments/-/media/us-media-files/documents/about/pdf/2024/"
        "wisdomtree-etfs-declare-final-capital-gains-distributions-2024.pdf "
        "is the full family list; payers ingested "
        "(GTR ST $0.51992; INDH LT $0.12765; QSML ST $0.00236; USIN ST $0.02859; "
        "USSH ST $0.02407; WTBN ST $0.02168). Dashed no-CG rows omitted. "
        "2023 December income sibling PDF is still 404 (do not invent). "
        "Official 5y leftover densify uses January–November 2023 monthly "
        "income PDFs for in-book leftover 4y tickers still missing 2023 "
        "(DGRW Nov $0.10000; DES Nov $0.06000; AGGY Nov $0.15000; GTR Sep "
        "$0.30000; CXSE Sep $0.10500). Leftover 3y names still missing 2023: "
        "AIVI Sep $0.35000; AIVL Sep $0.72000; GCC Oct $0.39883; GDE Oct "
        "$0.52223; GDMN Oct $1.68178; WTMF Oct $1.32291; WTRE Sep $0.11000; "
        "WTV Sep $0.26000; XC Sep $0.25000 (still miss 2021). Printed $0.00000 "
        "ST/LT omitted. CEW / USDU / WCBR / WCLD / WDNA / QGRW unpublished on "
        "those monthlies — skip. Parallel O leftover densify adds UNIY Nov "
        "2023 OI $0.17700 (ex 11/24/2023) from the same official November "
        "2023 monthly PDF — leftover 2y → 3y (2021–2022 unpublished; UNIY "
        "first appears on the February 2023 monthly). Leftover 4y names "
        "still missing 2021 stay unmatched: official December 2021 income "
        "PDF omits AIVI / AIVL / GCC / GDE / GDMN / WTAI / WTMF / WTRE / "
        "WTV / XC under current tickers; January–November 2021 monthly PDFs "
        "404. "
        "Live product pages 403. "
        "Digital-fund 2024 CG book is a separate tokenized product line — omitted. "
        "Official December 2025 income declaration "
        "https://www.wisdomtree.com/investments/-/media/us-media-files/documents/"
        "resource-library/fund-reports-schedules/distribution-history/"
        "wisdomtree-etfs-declare-distributions-december-2025.pdf "
        "is the family income book (DGRW $0.23270; DHS $0.58476; XC $0.22721; "
        "GTR $0.18160; WTPI $0.08373; published $0.00000 income stored for "
        "EPI / HEDJ / INDH / WCBR / WCLD / WQTM). Printed $0.00000 ST/LT "
        "columns omitted (the December 10 CG book remains the CG source). "
        "Official 5y wave-3 December income PDFs: 2024 "
        "(DGRW $0.15525), 2022 (DGRW $0.23017), 2021 (DGRW $0.20349). "
        "December 2023 income sibling still 404 — unmatched. Official 2023 "
        "final CG PDF adds printed payers only (AGZD ST $0.50744; WTAI ST "
        "$0.02126; dashed no-CG rows omitted). Growth of $X added for XC. "
        "WAVE AE leftover re-probe (2026-09-17): December 2023 income sibling "
        "and January–November 2021 monthly PDFs still 404. 2023 monthlies still "
        "omit CEW / USDU / WCBR / WCLD / WDNA / QGRW. Official 2021 December "
        "income PDF prints DOO / DTN / QSY — those are strategy restructures "
        "to AIVI / AIVL / WTV; leftover years are never copied from old "
        "tickers. Unmatched / not invented."
    )
    live_limitations = (
        "Family books are PDF. Weekly walk uses the 2025 estimate hub, "
        "final CG PDF, and December income declaration."
    )

    def pages(self) -> list[PageSpec]:
        media = "https://www.wisdomtree.com/investments/-/media/us-media-files/documents/about/pdf"
        return [
            PageSpec(
                name="2025_estimated_capital_gains_hub",
                url=(
                    "https://www.wisdomtree.com/investments/resource-library/"
                    "2025-estimated-capital-gains-distributions"
                ),
                fixture="2025_estimated_capital_gains_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_final_capital_gains",
                url=f"{media}/2025/wisdomtree-etfs-declare-final-capital-gains-distributions-2025.pdf",
                fixture="2025_final_capital_gains.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2024_final_capital_gains",
                url=f"{media}/2024/wisdomtree-etfs-declare-final-capital-gains-distributions-2024.pdf",
                fixture="2024_final_capital_gains.html",
                live=False,
            ),
            PageSpec(
                name="2025_december_etf_distributions",
                url=(
                    "https://www.wisdomtree.com/investments/-/media/us-media-files/documents/"
                    "resource-library/fund-reports-schedules/distribution-history/"
                    "wisdomtree-etfs-declare-distributions-december-2025.pdf"
                ),
                fixture="2025_december_etf_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2024_december_etf_distributions",
                url=(
                    "https://www.wisdomtree.com/investments/-/media/us-media-files/documents/"
                    "resource-library/fund-reports-schedules/distribution-history/"
                    "wisdomtree-etfs-declare-distributions-december-2024.pdf"
                ),
                fixture="2024_december_etf_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2022_december_etf_distributions",
                url=(
                    "https://www.wisdomtree.com/-/media/us-media-files/documents/"
                    "resource-library/fund-reports-schedules/distribution-history/"
                    "wisdomtree-etfs-declare-distributions-december-2022.pdf"
                ),
                fixture="2022_december_etf_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2021_december_etf_distributions",
                url=(
                    "https://www.wisdomtree.com/-/media/us-media-files/documents/"
                    "resource-library/fund-reports-schedules/distribution-history/"
                    "wisdomtree-etfs-declare-distributions-december-2021.pdf"
                ),
                fixture="2021_december_etf_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2023_final_capital_gains",
                url=(
                    "https://www.wisdomtree.com/investments/-/media/us-media-files/documents/"
                    "about/pdf/2023/wisdomtree-etfs-declare-final-capital-gains-distributions-2023.pdf"
                ),
                fixture="2023_final_capital_gains.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2023_monthly_etf_distributions_leftover",
                url=(
                    "https://www.wisdomtree.com/investments/-/media/us-media-files/documents/"
                    "resource-library/fund-reports-schedules/distribution-history/"
                    "wisdomtree-etfs-declare-distributions-november-2023.pdf"
                ),
                fixture="2023_monthly_etf_distributions_leftover.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="leftover_parallel_o_2023_monthly",
                url=(
                    "https://www.wisdomtree.com/investments/-/media/us-media-files/documents/"
                    "resource-library/fund-reports-schedules/distribution-history/"
                    "wisdomtree-etfs-declare-distributions-november-2023.pdf"
                ),
                fixture="leftover_parallel_o_2023_monthly.html",
                live=False,
                role="history",
            ),
        ]


class FirstTrustSource(HtmlTableSource):
    slug = "first_trust"
    display_name = "First Trust"
    aum_rank = 111
    priority = 111
    notes = (
        "Official Section 19(a) source-of-distribution notice "
        "https://www.ftportfolios.com/Common/ContentFileLoader.aspx?"
        "ContentGUID=ad59e9bb-c8bb-4696-bf2d-42b9fa64b17e "
        "(declaration 12/26/2025; ex/record 12/29/2025; pay 12/31/2025) "
        "lists current NII / STCG / LTCG / ROC for BFAP / BFJL / BGLD / IGLD "
        "(BFAP LT $3.1933 / ROC $0.2500; BGLD NII $0.5074 / ST $2.7353 / ROC $4.3407; "
        "IGLD NII $0.1042 / ST $0.1401 / ROC $0.3525). Fiscal YTD cumulative table "
        "omitted so illustration does not double-count. Printed dashes omitted. "
        "Official 24 Sep 2025 family declaration of 146 ETFs "
        "https://www.ftportfolios.com/Common/ContentFileLoader.aspx?"
        "ContentGUID=865e45a8-c914-4704-bc74-7227c3cabaf5 "
        "(ex/record 9/25/2025; pay 9/30/2025) is ordinary income "
        "(FVD $0.2519; FTHI $0.1710; FPE $0.0845; CIBR $0.0006). "
        "Printed LT column was blank — omitted, not stored as $0. "
        "Wave 11 official December family declarations: "
        "12/11/2025 156-ETF notice "
        "https://www.ftportfolios.com/Common/ContentFileLoader.aspx?"
        "ContentGUID=cf8dadde-0a3c-463c-b694-5111dbd18e39 "
        "(ex/record 12/12/2025; pay 12/31/2025; 152 paired tickers; "
        "FVD $0.3186; FTHI $0.1770; FPE $0.1220; CIBR $0.2084; "
        "FTCB income $0.0950 / ST $0.0318 / LT $0.0473) "
        "and 12/12/2024 159-ETF notice "
        "https://www.ftportfolios.com/Common/ContentFileLoader.aspx?"
        "ContentGUID=93a2ae96-a7c6-468c-b68b-8f516d1de5c4 "
        "(147 paired tickers; FVD $0.2752; FTHI $0.1720). "
        "Wrapped name rows the HTML table extractor could not pair are omitted, not invented. "
        "Interval / tender-offer First Trust Capital Management funds omitted. "
        "Coming-soon Vest rows omitted. "
        "Official 5y wave-3 product-page Distribution History "
        "https://www.ftportfolios.com/Retail/Etf/EtfDividHistory.aspx?Print=Y&Ticker=FVD&year=2023 "
        "(and the same Print=Y year page for each in-book ticker) adds December "
        "ordinary income 2021–2023 when the issuer printed a December row "
        "(FVD 2021 $0.231700 / 2022 $0.274800 / 2023 $0.292800; FPE 2021 "
        "$0.080200 / 2022 $0.092500 / 2023 $0.085700; CIBR 2021 $0.280700 / "
        "2022 $0.095400 / 2023 $0.165800; FTHI 2021 $0.080000 / 2022 $0.137000 "
        "/ 2023 $0.152000). Empty years (SKYY 2022–2023) omitted, not stored as $0. "
        "In-book hero gap-fill re-reads the same Print=Y pages for leftover "
        "lookback years the family December 2024 declaration omitted "
        "(FPEI 2024 $0.087000; RFDI $1.151300; FTA $0.453400; IGLD $2.404300; "
        "BGLD $4.595500). Empty issuer years still omitted. "
        "Official 5y wave 4 stores the latest issuer-printed ordinary-income "
        "row when December is empty on the missing lookback year "
        "(FPX 2021-09-23 $0.080500; FEP 2022-09-23 $0.170700; FSZ 2023-06-27 "
        "$1.281000; AGQI 2024-09-26 $0.071700; RNEM 2021-09-23 $0.843100). "
        "Empty issuer years (ARVR/BGLD/CRPT/EIPX/FSGS/FTC/FTGS/FXH/MISL/RDVI) "
        "still omitted. Parallel 5y sweep B re-reads leftover Print=Y years "
        "still missing from fixtures: FNY 2025-06-26 $0.029700; BNGE "
        "2022-06-24 $0.099800; EMDM 2024-12-13 $0.847300; SDVD 2024-12-13 "
        "$0.161200; FDNI 2023-03-24 $0.089700. Those fills do not complete "
        "5y. 4y leftovers (ARVR/BGLD/CRPT/EIPX/FSGS/FTC/FTGS/FXH/MISL/RDVI) "
        "and FNY 2021 / BNGE 2021+2024 / FBT empty years still unpublished. "
        "Parallel O re-read leftover Print=Y years still missing after B: "
        "ARVR/BGLD/EIPX/FNY/FTC/FTGS/FXH/MISL/RDVI 2021, CRPT 2023, FSGS 2025, "
        "BNGE 2021+2024, FBT 2021–2023+2025, remaining 3y/2y/1y leftovers "
        "(DOGG/EMDM/FCFY/FDNI/FIIG/FTCB/FTHF/FTIF/LALT/MGOV/SDVD/TDVI "
        "2021–2022; CAAA/EMOT/FDND/FTCE/SCIO 2021–2023; FAI/RND 2021–2023+2025) "
        "print “No distributions were paid during the selected year.” "
        "RFEU/EFIX/FBZ Print=Y is terminated; MARB/ECLN fund-not-found. "
        "Those leftover years stay unmatched — no new identities. "
        "WAVE AE leftover re-probe (2026-09-17): leftover Print=Y years still "
        "print “No distributions were paid during the selected year.” "
        "(ARVR/BGLD/EIPX/FNY/FTC/FTGS/FXH/MISL/RDVI 2021; CRPT 2023; "
        "FSGS 2025; BNGE 2021+2024; FBT empty years). Fiscal Jul-31 N-CSR "
        "highlights are not calendar-safe next to those empty Print=Y years. "
        "Unmatched / not invented."
    )
    live_limitations = (
        "Family 19(a) and declaration PDFs. Weekly walk uses the ContentGUID notice "
        "plus the 2025 tax-information reprint; empty/PDF-bytes pages are no-op success."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_section_19a_notice",
                url=(
                    "https://www.ftportfolios.com/Common/ContentFileLoader.aspx?"
                    "ContentGUID=ad59e9bb-c8bb-4696-bf2d-42b9fa64b17e"
                ),
                fixture="2025_section_19a_notice.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_september_etf_distributions",
                url=(
                    "https://www.ftportfolios.com/Common/ContentFileLoader.aspx?"
                    "ContentGUID=865e45a8-c914-4704-bc74-7227c3cabaf5"
                ),
                fixture="2025_september_etf_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2025_december_etf_distributions",
                url=(
                    "https://www.ftportfolios.com/Common/ContentFileLoader.aspx?"
                    "ContentGUID=cf8dadde-0a3c-463c-b694-5111dbd18e39"
                ),
                fixture="2025_december_etf_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2024_december_etf_distributions",
                url=(
                    "https://www.ftportfolios.com/Common/ContentFileLoader.aspx?"
                    "ContentGUID=93a2ae96-a7c6-468c-b68b-8f516d1de5c4"
                ),
                fixture="2024_december_etf_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="product_page_history_gapfill",
                url=(
                    "https://www.ftportfolios.com/Retail/Etf/EtfDividHistory.aspx?"
                    "Print=Y&Ticker=FPEI&year=2024"
                ),
                fixture="product_page_history_gapfill.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="product_page_history_midyear_gapfill",
                url=(
                    "https://www.ftportfolios.com/Retail/Etf/EtfDividHistory.aspx?"
                    "Print=Y&Ticker=FPX&year=2021"
                ),
                fixture="product_page_history_midyear_gapfill.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="product_page_history_leftover_parallel_b",
                url=(
                    "https://www.ftportfolios.com/Retail/Etf/EtfDividHistory.aspx?"
                    "Print=Y&Ticker=FNY&year=2025"
                ),
                fixture="product_page_history_leftover_parallel_b.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2023_december_etf_distributions",
                url=(
                    "https://www.ftportfolios.com/Retail/Etf/EtfDividHistory.aspx?"
                    "Print=Y&Ticker=FVD&year=2023"
                ),
                fixture="2023_december_etf_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2022_december_etf_distributions",
                url=(
                    "https://www.ftportfolios.com/Retail/Etf/EtfDividHistory.aspx?"
                    "Print=Y&Ticker=FVD&year=2022"
                ),
                fixture="2022_december_etf_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2021_december_etf_distributions",
                url=(
                    "https://www.ftportfolios.com/Retail/Etf/EtfDividHistory.aspx?"
                    "Print=Y&Ticker=FVD&year=2021"
                ),
                fixture="2021_december_etf_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="tax_information_hub",
                url=(
                    "https://www.ftportfolios.com/Common/ContentFileLoader.aspx?"
                    "ContentGUID=ef0fb0f7-095d-48e9-a38e-ef09507f9729"
                ),
                fixture="tax_information_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
        ]


class AqrSource(HtmlTableSource):
    slug = "aqr"
    display_name = "AQR"
    aum_rank = 56
    priority = 56
    notes = (
        "News: https://funds.aqr.com/News/2025/"
        "AQR-Funds-Announces-Estimated-Income-and-Capital-Gain-Distributions-for-2025 "
        "Public 2025 estimate PDF: "
        "https://funds.aqr.com/-/media/Funds/Tax-Documents/2025/"
        "2025-AQR-Funds-Announces-Estimated-Distributions.pdf?sc_lang=en "
        "is the full I/N/R6 share-class book "
        "(e.g. Global Equity I AQGIX ST $0.9086 / LT $0.4747 / 11.41% of NAV; "
        "Large Cap Defensive Style I AUEIX ST $0.0619 / LT $3.0673 / 15.62% of NAV). "
        "Most funds record 12/16/2025, ex 12/17/2025, pay 12/18/2025; "
        "Diversifying Strategies uses 12/19 / 12/22 / 12/23. "
        "Estimates as of 9/30/2025; NAV/shares as of 10/31/2025. "
        "Official 2024 final PDF: "
        "https://funds.aqr.com/-/media/Funds/Tax-Documents/2024/"
        "2024-AQR-Funds-Final-Distribution-Memo-Ex-Date-121724.pdf?sc_lang=en "
        "is transcribed as Class I only "
        "(AQGIX ST $0.6140 / LT $0.5462 / 11.68% of NAV; "
        "AUEIX ST $0.1898 / LT $4.3691 / 18.93% of NAV). "
        "Printed dashes omitted. N/R6 2024 clones not added as ticker vanity. "
        "Official 5y parallel R leftover: 2023 final memos (ex 12/18/2023 and "
        "Diversifying Strategies ex 12/27/2023), leftover 2024 N/R6 from the "
        "same 2024 final PDF, and 2025 final "
        "https://funds.aqr.com/-/media/Funds/Tax-Documents/2025/"
        "2025-AQR-Funds-Announces-Final-Distributions.pdf?sc_lang=en "
        "(AQGIX ST $0.9401 / LT $0.5044). 2021 / 2022 December finals 404. "
        "QDSIX 2025 unpublished on the 2025 final memo. Class-level — N/R6 "
        "are not copied from Class I."
    )
    live_limitations = (
        "Estimate book is PDF. Weekly walk uses the news hub + 2025 estimate PDF; "
        "empty/PDF-bytes pages are no-op success."
    )

    def pages(self) -> list[PageSpec]:
        tax = "https://funds.aqr.com/-/media/Funds/Tax-Documents"
        return [
            PageSpec(
                name="tax_documents_hub",
                url="https://funds.aqr.com/News",
                fixture="tax_documents_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_estimated_distributions",
                url=(
                    f"{tax}/2025/"
                    "2025-AQR-Funds-Announces-Estimated-Distributions.pdf?sc_lang=en"
                ),
                fixture="2025_estimated_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2024_final_distributions",
                url=(
                    f"{tax}/2024/"
                    "2024-AQR-Funds-Final-Distribution-Memo-Ex-Date-121724.pdf?sc_lang=en"
                ),
                fixture="2024_final_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="leftover_paid_parallel_r",
                url=(
                    f"{tax}/2025/"
                    "2025-AQR-Funds-Announces-Final-Distributions.pdf?sc_lang=en"
                ),
                fixture="leftover_paid_parallel_r.html",
                live=False,
                role="history",
            ),
        ]


class CausewaySource(HtmlTableSource):
    slug = "causeway"
    display_name = "Causeway"
    aum_rank = 57
    priority = 57
    notes = (
        "Public 2025 final distributions PDF: "
        "https://www.causewaycap.com/wp-content/uploads/2025_Causeway-Funds-Final-Distributions.pdf "
        "is the full Institutional + Investor book "
        "(e.g. International Value Institutional CIVIX ST $0.3957 / LT $1.5537; "
        "Global Value Institutional CGVIX ST $0.4236 / LT $0.9631; "
        "International Small Cap Institutional CIISX ST $0.2609 / LT $1.5623). "
        "Record 12/19/2025; ex 12/22/2025; pay 12/23/2025. "
        "Official 2024 final PDF: "
        "https://www.causewaycap.com/wp-content/uploads/2024_Causeway-Funds-Final-Distributions.pdf "
        "(CIVIX ST $0.1324 / LT $1.1868; CGVIX ST $1.0338 / LT $1.8282; "
        "CEMIX published $0.0000 ST/LT stored). "
        "Wave 5 lookback: official 2021–2023 final PDFs on the same "
        "`YYYY_Causeway-Funds-Final-Distributions.pdf` path "
        "(CIVIX 2021 income $0.3170 / published $0.0000 ST/LT stored; "
        "2022 income $0.2834; 2023 ST $0.1678 / LT $0.1748). "
        "Concentrated Equity CCENX / CCEVX is on 2021–2022 only — later years "
        "unmatched, not invented. Parallel-P leftover: official 2023–2025 Final "
        "PDFs omit Concentrated Equity; product page 404; no additive paid rows."
    )
    live_limitations = (
        "Year-end book is PDF. Weekly walk uses the resources hub + 2025 final PDF; "
        "empty/PDF-bytes pages are no-op success."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="distributions_hub",
                url="https://www.causewaycap.com/resources/",
                fixture="distributions_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_final_distributions",
                url="https://www.causewaycap.com/wp-content/uploads/2025_Causeway-Funds-Final-Distributions.pdf",
                fixture="2025_final_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2024_final_distributions",
                url="https://www.causewaycap.com/wp-content/uploads/2024_Causeway-Funds-Final-Distributions.pdf",
                fixture="2024_final_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2023_final_distributions",
                url="https://www.causewaycap.com/wp-content/uploads/2023_Causeway-Funds-Final-Distributions.pdf",
                fixture="2023_final_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2022_final_distributions",
                url="https://www.causewaycap.com/wp-content/uploads/2022_Causeway-Funds-Final-Distributions.pdf",
                fixture="2022_final_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2021_final_distributions",
                url="https://www.causewaycap.com/wp-content/uploads/2021_Causeway-Funds-Final-Distributions.pdf",
                fixture="2021_final_distributions.html",
                live=False,
                role="history",
            ),
        ]


class AlgerSource(HtmlTableSource):
    slug = "alger"
    display_name = "Alger / Fred Alger"
    aum_rank = 58
    priority = 58
    notes = (
        "Hub: https://www.alger.com/Pages/Page.aspx?pageLabel=DividendsDistributions "
        "Public 2025 mutual-fund distributions PDF: "
        "https://www.alger.com/AlgerDocuments/Distrib_FUNDS.pdf "
        "is the full share-class book "
        "(e.g. Global Equity A CHUSX ST $0.0024 / LT $2.4670 / 8.3% of NAV; "
        "International Opportunities A ALGAX LT $2.0655 / 10.4% of NAV; "
        "Small Cap Growth Institutional I ALSRX LT $0.4912 / 2.7% of NAV). "
        "Record 12/16/2025; ex/pay 12/17/2025. Published $0.00 amounts are stored. "
        "The PDF lists International Small Cap A as ALCZX (same ticker as Opportunities Z) — that row is omitted. "
        "Wave 7 lookback: official unversioned Distrib_FUNDS.pdf Wayback "
        "20230330013818 is the 2022 paid book (ACAAX LT $0.8384; ALARX LT $0.9783; "
        "SPECX LT $0.3918). Tickers attached only where the 2025 book prints the "
        "same fund name + class. Global Focus / International Focus / Weatherbie "
        "Enduring Growth 2022 name rows omitted (2025 names differ — not invented). "
        "Official Distrib_ETFS.pdf is the 2025 ETF book (ATFV ST $0.07080; FRTY "
        "income $0.04095; AWEG LT $0.45647) plus Wayback 2021 (FRTY ST $1.0687) "
        "and 2023 (ATFV income $0.0015). Distrib_FUNDS_2024.pdf 404; no official "
        "2023/2024 MF ST/LT book stored. Official 5y parallel I leftover: "
        "Distrib_FUNDS_2021 / 2023 / 2024 siblings still 404; Wayback "
        "20221103225410 of Distrib_FUNDS.pdf is 2022 estimates (as of Oct 17) "
        "— not ingested as paid. 2024 ETF Wayback is estimates. CHUSX "
        "2021/2023/2024 stay unmatched. Official 5y parallel T leftover "
        "re-probe: Distrib_FUNDS_2021 / 2023 / 2024 siblings still unpublished. "
        "ETF Wayback 20241126184535 of Distrib_ETFs.pdf is truncated; "
        "20251209195815 is Oct 2025 estimates — not ingested as paid. "
        "ATFV / FRTY 2022+2024 and leftover MF 2021/2023/2024 stay unmatched. "
        "Official 5y WAVE CF leftover (existing in-book only): Alger Funds II "
        "Responsible Investing FYE October 31 N-CSR Financial Highlights unlock "
        "leftover 2021 / 2023 / 2024 on the 2022+2025 paid Class A / C / I / Z "
        "book (SPEGX / AGFCX / AGIFX / ALGZX). Calendar-safe as_of 10/31. "
        "Class-level — never sibling-copied onto reserved Alger CHUSX / ALGAX / "
        "ALSRX / ACAAX or Spectra SPECX (2024 CG dash omitted). Income dividends "
        "from net investment income are official dashes — omitted, never invent "
        "$0. Net realized gain is unsplit total capital gains. 2022 and 2025 stay "
        "on the existing paid Distrib_FUNDS.pdf books. Alger Funds II N-CSR "
        "https://www.sec.gov/Archives/edgar/data/92751/000113322824011661/"
        "tgfii-efp13341_ncsr.htm (0001133228-24-011661) and matching 2023 N-CSR "
        "https://www.sec.gov/Archives/edgar/data/92751/000114036123059788/"
        "ef20017111_ncsr.htm (0001140361-23-059788). Sister WAVE CC Pioneer "
        "Class R PIORX / PQIRX, WAVE CD Lazard R6, WAVE CB Open, WAVE BY "
        "Institutional, WAVE CG Lazard Real Assets RALIX / RALOX, WAVE BZ / CA / "
        "BX Pioneer C/Y/K, and prior sister leftover pages stay unmatched / not "
        "re-emitted here. WAVE CF leftover N-CSR paid history is fixture-only. "
        "Official 5y WAVE CJ leftover (existing in-book only): The Alger Funds "
        "Growth & Income FYE October 31 N-CSR Financial Highlights unlock "
        "leftover 2021 / 2023 / 2024 on the 2022+2025 paid Class A / C / Z book "
        "(ALBAX / ALBCX / AGIZX). Calendar-safe as_of 10/31. Class-level — never "
        "sibling-copied onto reserved Alger CHUSX / ALGAX / ALSRX / ACAAX, WAVE "
        "CF Responsible Investing SPEGX / AGFCX / AGIFX / ALGZX, or Spectra "
        "SPECX. Income is ordinary income; net realized gain is unsplit total "
        "capital gains. Official 2023 / 2024 CG dashes omitted. 2022 and 2025 "
        "stay on the existing paid Distrib_FUNDS.pdf books. The Alger Funds "
        "N-CSR https://www.sec.gov/Archives/edgar/data/3521/000113322824011659/"
        "tgf-efp13340_ncsr.htm (0001133228-24-011659) and matching 2023 N-CSR "
        "https://www.sec.gov/Archives/edgar/data/3521/000114036123059776/"
        "ef20017112_ncsr.htm (0001140361-23-059776). Sister WAVE CH Harding "
        "Loevner HLEMX / HLGZX / HLIZX / HLFZX, WAVE CG Lazard Real Assets, "
        "WAVE CF Responsible Investing, WAVE CC Pioneer Class R, WAVE CD / CB / "
        "BY Lazard, WAVE BZ / CA / BX Pioneer C/Y/K, WAVE BW RAIIX, WAVE BV "
        "HMDCX, WAVE BT Federated SVD, sister CI Federated SVALX / NYLI Class I, "
        "and prior leftover pages stay unmatched / not re-emitted here. WAVE CJ "
        "leftover N-CSR paid history is fixture-only. "
        "Official 5y WAVE CS leftover (existing in-book only): The Alger Funds "
        "Capital Appreciation FYE October 31 N-CSR Financial Highlights unlock "
        "leftover 2021 / 2023 / 2024 on the 2022+2025 paid Class C / Z book "
        "(ALCCX / ACAZX). Calendar-safe as_of 10/31. Class-level — never "
        "sibling-copied onto reserved Alger CHUSX / ALGAX / ALSRX / ACAAX, WAVE "
        "CF Responsible Investing SPEGX / AGFCX / AGIFX / ALGZX, WAVE CJ Growth "
        "& Income ALBAX / ALBCX / AGIZX, Spectra SPECX, or Institutional ALARX "
        "/ ACARX / ACAYX / ACIZX. Income dividends from net investment income "
        "are official dashes — omitted, never invent $0. Net realized gain is "
        "unsplit total capital gains. 2022 and 2025 stay on the existing paid "
        "Distrib_FUNDS.pdf books. The Alger Funds 2025 N-CSR "
        "https://www.sec.gov/Archives/edgar/data/3521/000113322825014263/"
        "taf-efp21605_ncsr.htm (0001133228-25-014263) and matching 2024 / 2023 "
        "N-CSR https://www.sec.gov/Archives/edgar/data/3521/000113322824011659/"
        "tgf-efp13340_ncsr.htm (0001133228-24-011659) / "
        "https://www.sec.gov/Archives/edgar/data/3521/000114036123059776/"
        "ef20017112_ncsr.htm (0001140361-23-059776). Sister WAVE CR remaining "
        "JH Oct 31 leftovers, WAVE CP PZFVX, WAVE CO JHJAX, WAVE CN FIDAX / "
        "FRBAX, WAVE CL SVBAX / JDIBX / JEMQX / JDJAX, WAVE CM JEEBX, WAVE CK "
        "TAGRX / JCCAX, WAVE CJ Growth & Income, WAVE CI Federated SVALX / "
        "NYLI Class I, WAVE CH Harding Loevner, WAVE CG Lazard Real Assets, "
        "WAVE CF Responsible Investing, WAVE CC Pioneer Class R, WAVE CD / CB "
        "/ BY Lazard, WAVE BZ / CA / BX Pioneer C/Y/K, WAVE BW RAIIX, WAVE BV "
        "HMDCX, WAVE BT Federated SVD, and prior leftover pages stay unmatched "
        "/ not re-emitted here. WAVE CS leftover N-CSR paid history is "
        "fixture-only. "
        "Official 5y WAVE CT leftover (existing in-book only): The Alger "
        "Institutional Funds Capital Appreciation Institutional FYE October 31 "
        "N-CSR Financial Highlights unlock leftover 2021 / 2023 / 2024 on the "
        "2022+2025 paid Class I / R / Y / Z-2 book (ALARX / ACARX / ACAYX / "
        "ACIZX). Calendar-safe as_of 10/31. Class-level — never sibling-copied "
        "onto reserved Alger CHUSX / ALGAX / ALSRX / ACAAX, WAVE CS Capital "
        "Appreciation C/Z ALCCX / ACAZX, WAVE CF Responsible Investing SPEGX / "
        "AGFCX / AGIFX / ALGZX, WAVE CJ Growth & Income ALBAX / ALBCX / AGIZX, "
        "Spectra SPECX, or other Institutional series (Focus Equity / Mid Cap / "
        "Small Cap). Income dividends from net investment income are official "
        "dashes / absent — omitted, never invent $0. Net realized gain is "
        "unsplit total capital gains. 2022 and 2025 stay on the existing paid "
        "Distrib_FUNDS.pdf books. The Alger Institutional Funds 2025 N-CSR "
        "https://www.sec.gov/Archives/edgar/data/911415/000113322825014265/"
        "aif-efp21607_ncsr.htm (0001133228-25-014265) and matching 2024 / 2023 "
        "N-CSR https://www.sec.gov/Archives/edgar/data/911415/000113322824011663/"
        "taif-efp13342_ncsr.htm (0001133228-24-011663) / "
        "https://www.sec.gov/Archives/edgar/data/911415/000114036123059794/"
        "ef20017118_ncsr.htm (0001140361-23-059794). Sister WAVE CS Capital "
        "Appreciation C/Z, WAVE CU remaining mid-AUM leftovers, WAVE CR "
        "remaining JH Oct 31 leftovers, WAVE CP PZFVX, WAVE CO JHJAX, WAVE CN "
        "FIDAX / FRBAX, WAVE CL SVBAX / JDIBX / JEMQX / JDJAX, WAVE CM JEEBX, "
        "WAVE CK TAGRX / JCCAX, WAVE CJ Growth & Income, WAVE CI Federated "
        "SVALX / NYLI Class I, WAVE CH Harding Loevner, WAVE CG Lazard Real "
        "Assets, WAVE CF Responsible Investing, WAVE CC Pioneer Class R, WAVE "
        "CD / CB / BY Lazard, WAVE BZ / CA / BX Pioneer C/Y/K, WAVE BW RAIIX, "
        "WAVE BV HMDCX, WAVE BT Federated SVD, and prior leftover pages stay "
        "unmatched / not re-emitted here. WAVE CT leftover N-CSR paid history "
        "is fixture-only. "
        "Official 5y WAVE CU leftover (existing in-book only): Alger "
        "Institutional Funds Focus Equity FYE October 31 N-CSR Financial "
        "Highlights unlock leftover 2021 / 2023 / 2024 on the 2022+2025 paid "
        "Class A / I / Y / Z book (ALAFX / ALGRX / ALGYX / ALZFX). "
        "Calendar-safe as_of 10/31. Class-level — never sibling-copied onto "
        "Class C ALCFX (2023 official dashes), WAVE CS Capital Appreciation "
        "C/Z ALCCX / ACAZX, WAVE CT Capital Appreciation Institutional "
        "ALARX / ACARX / ACAYX / ACIZX, reserved Alger CHUSX / ALGAX / ALSRX "
        "/ ACAAX, WAVE CF Responsible Investing SPEGX / AGFCX / AGIFX / "
        "ALGZX, WAVE CJ Growth & Income ALBAX / ALBCX / AGIZX, or Spectra "
        "SPECX. Income is ordinary income; net realized gain is unsplit total "
        "capital gains. Official 2024 / 2023 / 2025 CG dashes, Class A 2021 "
        "OI dash, and Class I 2021 OI footnote (b) less than $0.005 omitted "
        "— never invent $0. 2022 and 2025 stay on the existing paid "
        "Distrib_FUNDS.pdf books (2025 ST $4.6563 / LT $3.4288; 2022 class-"
        "level OI / printed $0.00 ST/LT — not overwritten by N-CSR 2022 CG "
        "highlight $7.96). Alger Institutional Funds "
        "2025 N-CSR https://www.sec.gov/Archives/edgar/data/911415/"
        "000113322825014265/aif-efp21607_ncsr.htm (0001133228-25-014265) and "
        "matching 2024 N-CSR https://www.sec.gov/Archives/edgar/data/911415/"
        "000113322824011663/taif-efp13342_ncsr.htm (0001133228-24-011663). "
        "Sister WAVE CT Capital Appreciation Institutional, WAVE CS Capital "
        "Appreciation C/Z, WAVE CP PZFVX, WAVE CO JHJAX, WAVE CN FIDAX / "
        "FRBAX, WAVE CL SVBAX / JDIBX / JEMQX / JDJAX, WAVE CM JEEBX, WAVE "
        "CK TAGRX / JCCAX, WAVE CJ Growth & Income, WAVE CI Federated SVALX "
        "/ NYLI Class I, WAVE CH Harding Loevner, WAVE CG Lazard Real "
        "Assets, WAVE CF Responsible Investing, WAVE CC Pioneer Class R, "
        "WAVE CD / CB / BY Lazard, WAVE BZ / CA / BX Pioneer C/Y/K, WAVE BW "
        "RAIIX, WAVE BV HMDCX, WAVE BT Federated SVD, and prior leftover "
        "pages stay unmatched / not re-emitted here. Lazard RALYX / CONIX / "
        "CONOX / READX / RCMPX commencement walls stay unmatched. WAVE CU "
        "leftover N-CSR paid history is fixture-only."
    )
    live_limitations = (
        "Year-end book is PDF. Weekly walk uses the DividendsDistributions hub + 2025 "
        "MF/ETF PDFs; empty/PDF-bytes pages are no-op success. 2023/2024 MF official "
        "URLs missing. WAVE CF leftover Responsible Investing, WAVE CJ leftover "
        "Growth & Income, WAVE CS leftover Capital Appreciation C/Z Oct 31, "
        "WAVE CT leftover Capital Appreciation Institutional Oct 31, and WAVE CU "
        "leftover Focus Equity A/I/Y/Z Oct 31 N-CSR paid history are fixture-only."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="dividends_distributions_hub",
                url="https://www.alger.com/Pages/Page.aspx?pageLabel=DividendsDistributions",
                fixture="dividends_distributions_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_dividends_and_distributions",
                url="https://www.alger.com/AlgerDocuments/Distrib_FUNDS.pdf",
                fixture="2025_dividends_and_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_etf_dividends_and_distributions",
                url="https://www.alger.com/AlgerDocuments/Distrib_ETFS.pdf",
                fixture="2025_etf_dividends_and_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2022_dividends_and_distributions",
                url="https://www.alger.com/AlgerDocuments/Distrib_FUNDS.pdf",
                fixture="2022_dividends_and_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2023_etf_dividends_and_distributions",
                url="https://www.alger.com/AlgerDocuments/Distrib_ETFs.pdf",
                fixture="2023_etf_dividends_and_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2021_etf_dividends_and_distributions",
                url="https://www.alger.com/AlgerDocuments/Distrib_ETFs.pdf",
                fixture="2021_etf_dividends_and_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="leftover_ncsr_spegx_2021_2024_wave_cf",
                url=(
                    "https://www.sec.gov/Archives/edgar/data/92751/"
                    "000113322824011661/tgfii-efp13341_ncsr.htm#responsible-investing"
                ),
                fixture="leftover_ncsr_spegx_2021_2024_wave_cf.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="leftover_ncsr_albax_2021_2024_wave_cj",
                url=(
                    "https://www.sec.gov/Archives/edgar/data/3521/"
                    "000113322824011659/tgf-efp13340_ncsr.htm#growth-income"
                ),
                fixture="leftover_ncsr_albax_2021_2024_wave_cj.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="leftover_ncsr_alccx_acazx_2021_2024_wave_cs",
                url=(
                    "https://www.sec.gov/Archives/edgar/data/3521/"
                    "000113322825014263/taf-efp21605_ncsr.htm#capital-appreciation"
                ),
                fixture="leftover_ncsr_alccx_acazx_2021_2024_wave_cs.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="leftover_ncsr_alarx_acarx_acayx_acizx_2021_2024_wave_ct",
                url=(
                    "https://www.sec.gov/Archives/edgar/data/911415/"
                    "000113322825014265/aif-efp21607_ncsr.htm"
                    "#capital-appreciation-institutional"
                ),
                fixture="leftover_ncsr_alarx_acarx_acayx_acizx_2021_2024_wave_ct.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="leftover_ncsr_alafx_2021_2024_wave_cu",
                url=(
                    "https://www.sec.gov/Archives/edgar/data/911415/"
                    "000113322825014265/aif-efp21607_ncsr.htm#focus-equity"
                ),
                fixture="leftover_ncsr_alafx_2021_2024_wave_cu.html",
                live=False,
                role="history",
            ),
        ]


class HardingLoevnerSource(HtmlTableSource):
    slug = "harding_loevner"
    display_name = "Harding Loevner"
    aum_rank = 59
    priority = 59
    notes = (
        "Official 2025 annual-distributions PDF is the full printed share-class book: "
        "https://media.hardingloevner.com/fileadmin/pdf/HLF/HLF-2025-Distributions.pdf "
        "(AMG reprint https://wealth.amg.com/pdf-library/harding-loevner-2025-year-end-distributions/) "
        "(Global Equity Advisor HLMGX ST $0.240073 / LT $6.192933 / 17.15% of NAV; "
        "International Equity Investor HLMNX ST $0.097311 / LT $3.415402 / 11.43% of NAV; "
        "Emerging Markets Advisor HLEMX ST $0.589704 / LT $20.71838 / 46.85% of NAV). "
        "Record 12/12/2025; ex 12/15/2025; pay 12/16/2025. "
        "Frontier Emerging Markets printed no CG (income stored). "
        "Official 5y parallel A leftover: AMG product-page "
        "https://wealth.amg.com/wp-json/amgfundsdata/v1/fund-detail/{ticker}/performance "
        "Calendar Year Distributions 2021–2024 (HLMNX 2022 income $0.478847; "
        "HLMIX 2021 income $0.424819 / LT $0.321926; HLMSX 2021 LT $0.605796; "
        "HLMEX 2024 LT $2.094041). Class-level — never copied. Global Equity "
        "HLMGX / HLMVX have no 2022 row (unpublished). AMG JSON 404 leftover "
        "Z / HLEMX / HLIDX 2023 rows from Wayback HLF-2023-Distributions.pdf. "
        "2025 stays on the existing PDF fixture. Em-dash ST/LT omitted. "
        "Official 5y parallel T leftover: Wayback issuer PDFs "
        "HLF-Distributions-2021.pdf (20220116110203) and "
        "HLF-Distributions-2022.pdf (20230317075511) fill leftover HLEMX "
        "2021+2022 / HLGZX 2021 / HLIZX 2021+2022 / HLIDX 2022. Global Equity "
        "2022 printed dashes stay unmatched. HLFZX / HLRZX 2021–2022 unpublished "
        "under those tickers. 2024 leftover Z / HLEMX / HLIDX still 404. "
        "Official 5y WAVE AW leftover (existing in-book only): Global Equity "
        "FYE October 31 2022 N-CSR Financial Highlights unlock leftover 2022 "
        "on the 2021/2023–2025 AMG JSON + issuer PDF book (HLMGX / HLMVX CG "
        "$7.41 complete 5y; HLGZX CG $7.41 is official year-depth only — 2024 "
        "still unpublished). Calendar-safe as_of 10/31. Class-level Advisor / "
        "Institutional / Institutional Z — never sibling-copied. Income is "
        "ordinary income; net realized gain is unsplit total capital gains. "
        "Issuer 2022 OI dashes omitted. 2022 N-CSR "
        "https://www.sec.gov/Archives/edgar/data/1018170/000119312523002209/"
        "d363948dncsr.htm. WAVE AW leftover N-CSR paid history is fixture-only. "
        "Official 5y WAVE CH leftover (existing in-book only): Harding, Loevner "
        "Funds, Inc. FYE October 31 2024 N-CSR Financial Highlights unlock "
        "leftover 2024 on the 2021–2023+2025 paid Emerging Markets Advisor / "
        "Global Equity Institutional Z / International Equity Institutional Z "
        "book (HLEMX / HLGZX / HLIZX) and leftover 2021 / 2022 / 2024 on "
        "Frontier Emerging Markets Institutional Z (HLFZX). Calendar-safe "
        "as_of 10/31. Class-level — never sibling-copied onto Advisor / "
        "Institutional / Investor siblings or onto WAVE AW Global Equity "
        "HLMGX / HLMVX. Income is ordinary income; net realized gain is "
        "unsplit total capital gains. Official dashes omitted. 2025 stays on "
        "the existing paid HLF-2025-Distributions.pdf book. 2024 N-CSR "
        "https://www.sec.gov/Archives/edgar/data/1018170/000089843025000008/"
        "8dd25e24ef2e8b3.htm (0000898430-25-000008). HLIDX 2021 commencement "
        "wall and HLRZX Institutional Z commencement April 4, 2023 stay "
        "unmatched. Sister WAVE CG Lazard Real Assets RALIX / RALOX, WAVE CF "
        "Alger Responsible Investing, WAVE CC Pioneer Class R, WAVE CD / CB / "
        "BY Lazard, and prior leftover pages stay unmatched / not re-emitted "
        "here. WAVE CH leftover N-CSR paid history is fixture-only."
    )
    live_limitations = (
        "Year-end book is PDF. Weekly walk uses the official media.hardingloevner.com PDF; "
        "empty/PDF-bytes pages are no-op success. Leftover 2021–2024 is AMG JSON / Wayback PDF. "
        "Leftover Global Equity 2022 N-CSR and WAVE CH leftover Oct 31 2024 N-CSR "
        "paid history are fixture-only."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="tax_information_hub",
                url="https://media.hardingloevner.com/fileadmin/pdf/HLF/HLF-2025-Distributions.pdf",
                fixture="tax_information_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_year_end_distributions",
                url="https://media.hardingloevner.com/fileadmin/pdf/HLF/HLF-2025-Distributions.pdf",
                fixture="2025_year_end_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="leftover_product_page_history_2021_2024",
                url="https://wealth.amg.com/wp-json/amgfundsdata/v1/fund-detail/HLMNX/performance",
                fixture="leftover_product_page_history_2021_2024.html",
                live=False,
                role="history",
                large_aum_only=False,
            ),
            PageSpec(
                name="leftover_paid_year_end_parallel_t",
                url=(
                    "https://web.archive.org/web/20230317075511id_/"
                    "https://media.hardingloevner.com/fileadmin/pdf/HLF/"
                    "HLF-Distributions-2022.pdf"
                ),
                fixture="leftover_paid_year_end_parallel_t.html",
                live=False,
                role="history",
                large_aum_only=False,
            ),
            PageSpec(
                name="leftover_ncsr_global_equity_2022_wave_aw",
                url="https://www.sec.gov/Archives/edgar/data/1018170/000119312523002209/d363948dncsr.htm",
                fixture="leftover_ncsr_global_equity_2022_wave_aw.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="leftover_ncsr_hlemx_2024_wave_ch",
                url=(
                    "https://www.sec.gov/Archives/edgar/data/1018170/"
                    "000089843025000008/8dd25e24ef2e8b3.htm#hlemx-2024"
                ),
                fixture="leftover_ncsr_hlemx_2024_wave_ch.html",
                live=False,
                role="history",
            ),
        ]


class MatthewsAsiaSource(HtmlTableSource):
    slug = "matthews_asia"
    display_name = "Matthews Asia"
    aum_rank = 60
    priority = 60
    notes = (
        "Public paid mutual-fund distribution tables: "
        "https://www.matthewsasia.com/funds/mutual-funds/ "
        "(e.g. Emerging Markets Equity Investor MEGMX income $0.40034 / ST $0.08706 / 3.0% of NAV; "
        "Pacific Tiger Investor MAPTX LT $0.52224 / 2.4% of NAV; "
        "India Investor MINDX LT $1.62048 / 6.5% of NAV). "
        "Record 12/16/2025; ex/pay 12/17/2025. "
        "Schedule-only page (no amounts): "
        "https://www.matthewsasia.com/resources/distributions-tax/distribution-dates/ "
        "Official product-page paid history for Investor heroes MEGMX / MAPTX / MINDX "
        "covers 2021–2024 (e.g. MAPTX 2024 income $0.58609 / LT $0.99319 / 8.0% of NAV; "
        "MINDX 2024 ST $1.41120 / LT $2.39476 / 12.7% of NAV). "
        "Wave 5 lookback adds official Investor product-page December YE 2021–2025 "
        "for MAPIX / MSMLX / MCHFX / MASGX / MCSMX "
        "(MAPIX 2021 LT $2.31785 / 2025 income $0.26050; "
        "MSMLX 2021 ST $1.52123 / 2025 income $0.38648; "
        "MCHFX 2022 LT $1.09205 / 2025 income $0.23320). "
        "December YE only so quarterly MAPIX income is not summed. "
        "MPACX has no 2025 YE row; MJFOX has no 2023 YE row; MATFX stops at 2023 — "
        "gaps, not invented. Parallel-P leftover: in-book Investor names "
        "(MAPIX / MAPTX / MASGX / MCHFX / MCSMX / MEGMX / MINDX / MSMLX) are already 5y; "
        "MPACX / MJFOX / MATFX and Institutional siblings are not in the NAV book "
        "(product freeze) — no additive paid rows."
    )
    live_limitations = (
        "Live product HTML is public but nested class/accordion tables may not parse. "
        "Weekly walk uses the product page; empty/SPA pages are no-op success. "
        "Fixture fallback with Investor-class tickers."
    )

    def pages(self) -> list[PageSpec]:
        product = "https://www.matthewsasia.com/funds/mutual-funds/"
        return [
            PageSpec(
                name="2025_year_end_distributions",
                url=product,
                fixture="2025_year_end_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2024_year_end_distributions",
                url=product,
                fixture="2024_year_end_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2023_year_end_distributions",
                url=product,
                fixture="2023_year_end_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2022_year_end_distributions",
                url=product,
                fixture="2022_year_end_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2021_year_end_distributions",
                url=product,
                fixture="2021_year_end_distributions.html",
                live=False,
                role="history",
            ),
        ]
