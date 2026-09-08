"""Ranks 101–110 boutique US-advisor families with scrapeable public CG books."""

from __future__ import annotations

from app.sources.html_source import HtmlTableSource, PageSpec


class AmgSource(HtmlTableSource):
    slug = "amg"
    display_name = "AMG"
    aum_rank = 101
    priority = 101
    notes = (
        "Tax hub: https://wealth.amg.com/resources/tax-information/capital-gain-distributions/ "
        "Public 2025 year-end distributions PDF is the full printed I/N/Z book: "
        "https://wealth.amg.com/pdf-library/amg-funds-2025-year-end-distributions/ "
        "(Yacktman Class I YACKX income $1.1267 / ST $0.0843 / LT $2.8135; "
        "GW&K Small Cap Growth Class I MCGIX ST $0.4791 / LT $3.8429; "
        "River Road Dividend All Cap Value Class I ARIDX income $0.1044 / LT $1.1294). "
        "Record 12/15/2025; ex/reinvest/pay 12/16/2025. "
        "SMA shares omitted. Monthly income-only / no-CG rows omitted. "
        "Harding Loevner and Tweedy stay on their own adapters."
    )
    live_limitations = (
        "Year-end book is PDF. Weekly walk uses the tax hub + PDF URL; "
        "empty/PDF-bytes pages are no-op success."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="tax_information_hub",
                url="https://wealth.amg.com/resources/tax-information/capital-gain-distributions/",
                fixture="tax_information_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_year_end_distributions",
                url="https://wealth.amg.com/pdf-library/amg-funds-2025-year-end-distributions/",
                fixture="2025_year_end_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            )
        ]


class GuidestoneSource(HtmlTableSource):
    slug = "guidestone"
    display_name = "GuideStone"
    aum_rank = 102
    priority = 102
    notes = (
        "Public capital-gains HTML: "
        "https://www.guidestonefunds.com/Tax-Information/Capital-Gains "
        "(Growth Equity Investor GGEZX ST $0.024841 / LT $3.279591; "
        "Value Equity Investor GVEZX ST $0.056041 / LT $1.602626; "
        "Small Cap Equity Investor GSCZX ST $0.284974 / LT $1.191699). "
        "Estimates as of 9/30/2025; record 12/4/2025; pay 12/5/2025. "
        "Live table is fund-level; tickers are public Investor-class identifiers."
    )
    live_limitations = (
        "Public HTML has fund-name ST/LT columns and no ticker column. "
        "Fixture attaches public Investor tickers."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_capital_gains",
                url="https://www.guidestonefunds.com/Tax-Information/Capital-Gains",
                fixture="2025_estimated_capital_gains.html",
                live=True,
                role="estimate",
                empty_ok=True,
            )
        ]


class ValueLineSource(HtmlTableSource):
    slug = "value_line"
    display_name = "Value Line"
    aum_rank = 103
    priority = 103
    notes = (
        "Public finalized HTML: https://vlfunds.com/gains "
        "(Small Cap Opportunities Investor VLEOX LT $3.79637; "
        "Asset Allocation Investor VLAAX income $0.70009 / LT $3.59915; "
        "Capital Appreciation Investor VALIX income $0.09563 / ST $0.10621 / LT $0.66499). "
        "Record 12/16/2025; ex/pay/reinvest 12/17/2025."
    )
    live_limitations = (
        "Public HTML is scrapeable; mashed header labels may still return 0 live rows "
        "→ fixture fallback."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_year_end_distributions",
                url="https://vlfunds.com/gains",
                fixture="2025_year_end_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            )
        ]


class PermanentPortfolioSource(HtmlTableSource):
    slug = "permanent_portfolio"
    display_name = "Permanent Portfolio"
    aum_rank = 104
    priority = 104
    notes = (
        "Product page paid table: https://permanentportfoliofunds.com/permanent-portfolio.html "
        "Family supplemental tax PDF: "
        "https://www.permanentportfoliofunds.com/pdf/2025%20Supplemental%20Tax%20Information_FINAL.pdf "
        "(Permanent Portfolio Class I PRPFX income $0.872450 / ST $0.011790 / LT $1.561510; "
        "Versatile Bond Class I PRVBX income $2.708090 / ST $0.002690; "
        "Aggressive Growth Class I PAGRX income $0.000930 / ST $0.003150 / LT $0.039230). "
        "Record 12/3/2025; ex/pay/reinvest 12/4/2025."
    )
    live_limitations = (
        "Paid amounts sit in a class-column product table, not a Fund/Ticker/ST/LT grid. "
        "Fixture transcribes public Class I rows from the family tax PDF."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_supplemental_tax_information",
                url=(
                    "https://www.permanentportfoliofunds.com/pdf/"
                    "2025%20Supplemental%20Tax%20Information_FINAL.pdf"
                ),
                fixture="2025_supplemental_tax_information.html",
                live=True,
                role="estimate",
                empty_ok=True,
            )
        ]


class ConestogaSource(HtmlTableSource):
    slug = "conestoga"
    display_name = "Conestoga"
    aum_rank = 105
    priority = 105
    notes = (
        "Public capital-gains HTML: "
        "https://conestogacapital.com/capital-gains-information/ "
        "(Small Cap Institutional CCALX LT $19.71; "
        "Discovery Institutional CMIRX LT $0.31). "
        "Estimates as of July 31, 2026; not final. "
        "Live table is fund-level (all share classes); tickers are public Institutional identifiers."
    )
    live_limitations = (
        "Public HTML has fund-name ST/LT columns and no ticker column. "
        "Fixture attaches public Institutional tickers."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2026_estimated_capital_gains",
                url="https://conestogacapital.com/capital-gains-information/",
                fixture="2026_estimated_capital_gains.html",
                live=True,
                role="estimate",
                empty_ok=True,
            )
        ]


class KopernikSource(HtmlTableSource):
    slug = "kopernik"
    display_name = "Kopernik"
    aum_rank = 106
    priority = 106
    notes = (
        "Public December 2025 final PDF: "
        "https://www.kopernikglobal.com/wp-content/uploads/2025/12/"
        "KGI-CG-MEMO-December-2025-FINAL-1.pdf "
        "(Global All-Cap Class I KGGIX income $0.9635 / ST $0.3420 / LT $1.2488; "
        "International Class I KGIIX income $0.7608 / ST $0.3811 / LT $1.3127). "
        "Capital-gain record 12/19/2025; ex 12/22/2025; pay 12/23/2025."
    )
    live_limitations = "Year-end book is PDF. Fixture transcribes public Class I / Class A rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_final_distributions",
                url=(
                    "https://www.kopernikglobal.com/wp-content/uploads/2025/12/"
                    "KGI-CG-MEMO-December-2025-FINAL-1.pdf"
                ),
                fixture="2025_final_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            )
        ]


class LocorrSource(HtmlTableSource):
    slug = "locorr"
    display_name = "LoCorr"
    aum_rank = 107
    priority = 107
    notes = (
        "Public 2025 annual distributions PDF: "
        "https://locorrfunds.com/wp-content/uploads/2021/04/"
        "LoCorr-Funds-Annual-CapitalGains-Dividends.pdf "
        "(Dynamic Opportunity Class I LEQIX ST $2.0297 / income $0.2202; "
        "Macro Strategies Class I LFMIX income $0.2444; "
        "Market Trend Class I LOTIX income $0.2908). "
        "Most funds record 12/8/2025 / ex 12/9/2025; "
        "Dynamic Opportunity record 12/30/2025 / ex 12/31/2025."
    )
    live_limitations = "Year-end book is PDF. Fixture transcribes public Class I rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_annual_distributions",
                url=(
                    "https://locorrfunds.com/wp-content/uploads/2021/04/"
                    "LoCorr-Funds-Annual-CapitalGains-Dividends.pdf"
                ),
                fixture="2025_annual_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            )
        ]


class TimothyPlanSource(HtmlTableSource):
    slug = "timothy_plan"
    display_name = "Timothy Plan"
    aum_rank = 108
    priority = 108
    notes = (
        "Public year-end 2025 PDF: "
        "https://timothyplan.com/download/Capital_Gains_Distribution.pdf "
        "(Large/Mid Cap Value Class I TMVIX ST $1.6936 / LT $0.1303; "
        "Large/Mid Cap Growth Class A TLGAX ST $1.5574 / LT $0.0408; "
        "Small Cap Value Class A TPLNX ST $0.2780 / LT $0.6058). "
        "Record 12/10/2025; ex 12/11/2025. "
        "PDF is fund-level; tickers are public Class I / Class A identifiers."
    )
    live_limitations = "Year-end book is PDF. Fixture attaches public Class I / Class A tickers."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_year_end_distributions",
                url="https://timothyplan.com/download/Capital_Gains_Distribution.pdf",
                fixture="2025_year_end_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            )
        ]


class HodgesSource(HtmlTableSource):
    slug = "hodges"
    display_name = "Hodges"
    aum_rank = 109
    priority = 109
    notes = (
        "Public 10/31/2025 estimate PDF: "
        "https://www.hodgescapital.com/hubfs/Mutual_Funds/Documents/"
        "Year_End_Distribution_Estimates.pdf "
        "(Hodges Fund Retail HDPMX ST $1.57 / LT $5.82; "
        "Small Cap Retail HDPSX ST $0.56 / LT $0.97; "
        "Blue Chip Equity Income Retail HDPBX ST $0.27 / LT $1.05). "
        "Anticipated ex 12/11/2025 (Blue Chip 12/30/2025). "
        "PDF is fund-level; tickers are public Retail identifiers."
    )
    live_limitations = "Year-end book is PDF. Fixture attaches public Retail tickers."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_capital_gains",
                url=(
                    "https://www.hodgescapital.com/hubfs/Mutual_Funds/Documents/"
                    "Year_End_Distribution_Estimates.pdf"
                ),
                fixture="2025_estimated_capital_gains.html",
                live=True,
                role="estimate",
                empty_ok=True,
            )
        ]


class TocquevilleSource(HtmlTableSource):
    slug = "tocqueville"
    display_name = "Tocqueville"
    aum_rank = 110
    priority = 110
    notes = (
        "Document library: https://www.tocquevillefunds.com/document-library/ "
        "Public 12/9/2025 final PDF: "
        "https://www.tocquevillefunds.com/wp-content/uploads/2025/12/"
        "2025-FINAL-Distributions-December-9-2025.pdf "
        "(Tocqueville Fund TOCQX income $0.063 / LT $3.578). "
        "Record 12/8/2025; ex/pay 12/9/2025. "
        "Remaining open-end book is a single fund with a family distribution notice."
    )
    live_limitations = "Year-end book is PDF. Fixture transcribes the public TOCQX row."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_final_distributions",
                url=(
                    "https://www.tocquevillefunds.com/wp-content/uploads/2025/12/"
                    "2025-FINAL-Distributions-December-9-2025.pdf"
                ),
                fixture="2025_final_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            )
        ]
