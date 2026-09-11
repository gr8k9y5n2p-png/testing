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
        "Wave 16 leftover Investor / Advisor / Institutional tickers come from "
        "official brownadvisory.com/mf/funds product pages (BIAFX / BAFAX / "
        "BIAWX / BAWAX / BAFLX) paired with the same printed amounts — existing "
        "BAFFX / BAFGX / BAFWX / BVALX are not re-emitted. Mid-Cap Growth and "
        "WMC Japan Equity product pages 404 this session. "
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
        "Class I flagships BGFIX / LCGFX / WGFIX / WBSIX are not re-emitted."
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
                name="2025_etf_year_end_distributions",
                url="https://www.vaneck.com/us/en/vaneck-funds-yearend-distributions-2025.pdf",
                fixture="2025_etf_year_end_distributions.html",
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
        "2023 ETF final sibling PDF was not a stable public file (do not invent). "
        "Digital-fund 2024 CG book is a separate tokenized product line — omitted. "
        "Official December 2025 income declaration "
        "https://www.wisdomtree.com/investments/-/media/us-media-files/documents/"
        "resource-library/fund-reports-schedules/distribution-history/"
        "wisdomtree-etfs-declare-distributions-december-2025.pdf "
        "is the family income book (DGRW $0.23270; DHS $0.58476; XC $0.22721; "
        "GTR $0.18160; WTPI $0.08373; published $0.00000 income stored for "
        "EPI / HEDJ / INDH / WCBR / WCLD / WQTM). Printed $0.00000 ST/LT "
        "columns omitted (the December 10 CG book remains the CG source). "
        "Growth of $X added for XC."
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
        "Coming-soon Vest rows omitted."
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
        "Printed dashes omitted. N/R6 2024 clones not added as ticker vanity."
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
        "unmatched, not invented."
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
        "2023/2024 MF ST/LT book stored."
    )
    live_limitations = (
        "Year-end book is PDF. Weekly walk uses the DividendsDistributions hub + 2025 "
        "MF/ETF PDFs; empty/PDF-bytes pages are no-op success. 2023/2024 MF official "
        "URLs missing."
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
        "2024 sibling URLs 404; no official 2024 ST/LT book stored."
    )
    live_limitations = (
        "Year-end book is PDF. Weekly walk uses the official media.hardingloevner.com PDF; "
        "empty/PDF-bytes pages are no-op success. 2024 official URL missing."
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
        "gaps, not invented."
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
