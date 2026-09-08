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
        "(SIMT Large Cap Growth ST $1.541 / LT $7.596 / 15.46% of NAV)."
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
        "Record/declaration 12/12/2025; ex/reinvest and pay 12/15/2025. "
        "2024 schedule: https://www.brownadvisory.com/sites/default/files/2024_Capital_Gain_Distribution.pdf "
        "(Flexible Equity Institutional BAFFX ST $0.15 / LT $1.72)."
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
        "(Growth Class I BGFIX LT $3.03562 / 19% of NAV)."
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
        "Hub: https://www.vaneck.com/us/en/resources/etf-distributions/"
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
        "USSH ST $0.02407; WTBN ST $0.02168). Dashed no-CG rows omitted."
    )
    live_limitations = "Family books are PDF. Weekly walk uses the 2025 final CG PDF."

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
        "Monthly income-sleeve 19(a) notices (FTHI, FMB) are not this family book."
    )
    live_limitations = (
        "Family 19(a) is PDF. Weekly walk uses the ContentGUID notice; "
        "empty/PDF-bytes pages are no-op success."
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
            )
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
        "Estimates as of 9/30/2025; NAV/shares as of 10/31/2025."
    )
    live_limitations = "Estimate book is PDF. Fixture transcribes public Class I rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_distributions",
                url=(
                    "https://funds.aqr.com/-/media/Funds/Tax-Documents/2025/"
                    "2025-AQR-Funds-Announces-Estimated-Distributions.pdf?sc_lang=en"
                ),
                fixture="2025_estimated_distributions.html",
                live=False,
            )
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
        "Record 12/19/2025; ex 12/22/2025; pay 12/23/2025."
    )
    live_limitations = "Year-end book is PDF. Fixture transcribes public Institutional-class rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_final_distributions",
                url="https://www.causewaycap.com/wp-content/uploads/2025_Causeway-Funds-Final-Distributions.pdf",
                fixture="2025_final_distributions.html",
                live=False,
            )
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
        "The PDF lists International Small Cap A as ALCZX (same ticker as Opportunities Z) — that row is omitted."
    )
    live_limitations = "Year-end book is PDF. Fixture transcribes public Class A / Institutional I rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_dividends_and_distributions",
                url="https://www.alger.com/AlgerDocuments/Distrib_FUNDS.pdf",
                fixture="2025_dividends_and_distributions.html",
                live=False,
            )
        ]


class HardingLoevnerSource(HtmlTableSource):
    slug = "harding_loevner"
    display_name = "Harding Loevner"
    aum_rank = 59
    priority = 59
    notes = (
        "Public 2025 year-end distributions PDF (AMG reprint): "
        "https://wealth.amg.com/pdf-library/harding-loevner-2025-year-end-distributions/ "
        "(e.g. Global Equity Advisor HLMGX ST $0.240073 / LT $6.192933 / 17.15% of NAV; "
        "International Equity Investor HLMNX ST $0.097311 / LT $3.415402 / 11.43% of NAV; "
        "Emerging Markets Advisor HLEMX ST $0.589704 / LT $20.71838 / 46.85% of NAV). "
        "Record 12/12/2025; ex 12/15/2025; pay 12/16/2025. "
        "Tax-info reprint: "
        "https://media.hardingloevner.com/fileadmin/pdf/HLF/HLF-Additional-Tax-Information-2025.pdf"
    )
    live_limitations = "Year-end book is PDF. Fixture transcribes public Advisor/Investor-class rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_year_end_distributions",
                url="https://wealth.amg.com/pdf-library/harding-loevner-2025-year-end-distributions/",
                fixture="2025_year_end_distributions.html",
                live=False,
            )
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
        "https://www.matthewsasia.com/resources/distributions-tax/distribution-dates/"
    )
    live_limitations = (
        "Live product HTML is public but nested class/accordion tables may not parse. "
        "Fixture fallback with Investor-class tickers."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_year_end_distributions",
                url="https://www.matthewsasia.com/funds/mutual-funds/",
                fixture="2025_year_end_distributions.html",
                live=True,
            )
        ]
