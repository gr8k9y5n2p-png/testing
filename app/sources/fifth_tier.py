from __future__ import annotations

from app.sources.html_source import HtmlTableSource, PageSpec


class HarborSource(HtmlTableSource):
    slug = "harbor"
    display_name = "Harbor"
    aum_rank = 41
    priority = 41
    notes = (
        "Tax center: https://www.harborcapital.com/tax-center/ "
        "Public 10/23/2025 year-end estimate PDF: "
        "https://assets.harborcapital.com/docs/Distribution_Estimates_Mutual_Funds_2025.pdf "
        "(e.g. Capital Appreciation Institutional HACAX LT $11.89 / 9% of NAV; "
        "Small Cap Value Institutional HASCX LT $0.86 / 2% of NAV). "
        "Ordinary-income + capital-gains record/ex/pay 12/18–12/19/2025; "
        "a second date set is 12/10–12/11/2025."
    )
    live_limitations = "Estimate book is PDF. Fixture transcribes public Institutional-class rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_year_end_distributions",
                url="https://assets.harborcapital.com/docs/Distribution_Estimates_Mutual_Funds_2025.pdf",
                fixture="2025_estimated_year_end_distributions.html",
                live=False,
            )
        ]


class NationwideSource(HtmlTableSource):
    slug = "nationwide"
    display_name = "Nationwide"
    aum_rank = 42
    priority = 42
    notes = (
        "Year-end hub: "
        "https://www.nationwide.com/personal/investing/mutual-funds/year-end-information/ "
        "Public 2025 capital-gains distribution PDF (MFN-0435AO): "
        "https://nationwidefinancial.com/media/pdf/MFN-0435AO.pdf "
        "(e.g. Bailard Technology & Science Class A NWHOX LT $3.7231 / 12.48% of NAV; "
        "Bailard International Equities Class A NWHJX LT $0.6148 / 5.19%). "
        "Most funds record 12/17/2025, ex 12/18/2025, pay 12/19/2025; "
        "Investor/Target Destination funds record 12/22/2025."
    )
    live_limitations = (
        "Family book is PDF. Automated GET is sometimes Akamai-denied without a "
        "browser/query token; fixture transcribes public Class A rows."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_capital_gains_distributions",
                url="https://nationwidefinancial.com/media/pdf/MFN-0435AO.pdf",
                fixture="2025_capital_gains_distributions.html",
                live=False,
            )
        ]


class VoyaSource(HtmlTableSource):
    slug = "voya"
    display_name = "Voya"
    aum_rank = 43
    priority = 43
    notes = (
        "Tax center: https://individuals.voya.com/product/tax-center/about-capital-gain-distributions "
        "Public 10/30/2025 estimate PDF: "
        "https://individuals.voya.com/document/tax-center/2025-estimated-capital-gains.pdf "
        "(advisor copy: https://advisors.voya.com/document/tax-center/2025-estimated-capital-gains.pdf) "
        "(e.g. Large-Cap Growth NLCAX/PLCIX ST $0.396 / LT $7.259 / 11.63% of NAV; "
        "Corporate Leaders 100 ST $0.654 / LT $1.205 / 6.83%). "
        "Record 12/11/2025; ex/pay 12/12/2025. Tickers are public Class A/I identifiers; "
        "the PDF is fund-level. AllianzGI US retail books transferred to Voya in 2022 — "
        "use this adapter, not a distinct allianzgi source."
    )
    live_limitations = "Estimate book is PDF. Fixture transcribes public open-end rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_capital_gains",
                url="https://individuals.voya.com/document/tax-center/2025-estimated-capital-gains.pdf",
                fixture="2025_estimated_capital_gains.html",
                live=False,
            )
        ]


class OakmarkSource(HtmlTableSource):
    slug = "oakmark"
    display_name = "Oakmark / Harris Associates"
    aum_rank = 44
    priority = 44
    notes = (
        "Public 2025 year-end distribution HTML: "
        "https://oakmark.com/news-insights/2025-oakmark-year-end-fund-distributions/ "
        "(e.g. International Small Cap Investor OAKEX LT $0.7640 / 5.13% of NAV; "
        "Oakmark Fund Investor OAKMX income $1.5797 / 0.91% of NAV — no 2025 CG). "
        "Record 12/10/2025; ex 12/11/2025; pay 12/12/2025. "
        "Tax guide: https://oakmark.com/wp-content/uploads/sites/3/documents/HarrisOakmark-Tax-Information-Guide.pdf"
    )
    live_limitations = (
        "Live page is public HTML with class-section tables and no ticker column. "
        "Static parse may return 0 rows. Fixture fallback with Investor-class tickers."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_year_end_distributions",
                url="https://oakmark.com/news-insights/2025-oakmark-year-end-fund-distributions/",
                fixture="2025_year_end_distributions.html",
                live=True,
            )
        ]


class TweedySource(HtmlTableSource):
    slug = "tweedy"
    display_name = "Tweedy, Browne"
    aum_rank = 45
    priority = 45
    notes = (
        "Public 9/30/2025 estimate PDF: "
        "https://www.tweedyfunds.com/wp-content/uploads/sites/10/2025/10/2025-Estimated-Distributions-9-30-25-2.pdf "
        "(e.g. International Value TBGVX LT $2.516; Value Fund TWEBX ST $0.017 / LT $0.408). "
        "Record 12/10/2025; ex/pay/reinvest 12/11/2025. Paid history is on product pages, "
        "e.g. https://www.tweedyfunds.com/mutual-funds/value-fund-distributions/"
    )
    live_limitations = "Family estimate book is PDF. Fixture transcribes public Investor-class rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_year_end_distributions",
                url=(
                    "https://www.tweedyfunds.com/wp-content/uploads/sites/10/2025/10/"
                    "2025-Estimated-Distributions-9-30-25-2.pdf"
                ),
                fixture="2025_estimated_year_end_distributions.html",
                live=False,
            )
        ]


class GabelliSource(HtmlTableSource):
    slug = "gabelli"
    display_name = "Gabelli"
    aum_rank = 46
    priority = 46
    notes = (
        "Open-end distributions hub: https://gabelli.com/funds/open-ends/distributions/ "
        "Public 12/29/2025 paid year-end memo: "
        "https://gabelli.com/wp-content/uploads/2025/12/Distribution-memo-12.29.2025.pdf "
        "(e.g. Growth Fund Class AAA GABGX LT $6.8575; Asset Fund Class AAA GABAX LT $5.6168). "
        "Record 12/26/2025; ex/pay/reinvest 12/29/2025."
    )
    live_limitations = "Year-end book is PDF. Fixture transcribes public Class AAA rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_year_end_distributions",
                url="https://gabelli.com/wp-content/uploads/2025/12/Distribution-memo-12.29.2025.pdf",
                fixture="2025_year_end_distributions.html",
                live=False,
            )
        ]


class RoyceSource(HtmlTableSource):
    slug = "royce"
    display_name = "Royce"
    aum_rank = 47
    priority = 47
    notes = (
        "Public 2025 open-end year-end distribution HTML: "
        "https://www.royceinvest.com/news/2025/4Q25/open-end-funds-2025-year-end-distributions "
        "PDF reprint: "
        "https://www.royceinvest.com/news/2025/4Q25/PDF/royce-open-end-funds-distributions-2025.pdf "
        "(e.g. Small-Cap Total Return Investment RYTRX ST $0.0257 / LT $0.7656; "
        "Micro-Cap Investment RYOTX LT $1.6509). "
        "Record 12/10/2025; ex/pay 12/11/2025. CEF 19(a) notices are a separate closed-end book."
    )
    live_limitations = (
        "Live HTML is public but table layout/headers may not parse. Fixture fallback."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_year_end_distributions",
                url="https://www.royceinvest.com/news/2025/4Q25/open-end-funds-2025-year-end-distributions",
                fixture="2025_year_end_distributions.html",
                live=True,
            )
        ]


class NylifeSource(HtmlTableSource):
    slug = "nylife"
    display_name = "New York Life Investments / MainStay"
    aum_rank = 48
    priority = 48
    notes = (
        "Public 10/31/2025 year-end estimate PDF (MainStay/NYLI flyer MSSR06-11/25): "
        "https://www.nylim.com/assets/documents/tax/cap-gains-estimate.pdf "
        "(e.g. Winslow Large Cap Growth MLAIX ST $0.26–$0.50 / LT $1.01–$3.00 / over 10% of NAV; "
        "Epoch U.S. Equity Yield EPLCX LT $1.01–$3.00 / 5.01–10.00% of NAV). "
        "Equity record/ex dates vary (Winslow 12/3–12/4/2025). "
        "MainStay funds were rebranded NYLI; this adapter covers both names."
    )
    live_limitations = "Estimate book is PDF with per-share ranges. Fixture transcribes public Class I identifiers."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_capital_gains",
                url="https://www.nylim.com/assets/documents/tax/cap-gains-estimate.pdf",
                fixture="2025_estimated_capital_gains.html",
                live=False,
            )
        ]


class TouchstoneSource(HtmlTableSource):
    slug = "touchstone"
    display_name = "Touchstone"
    aum_rank = 49
    priority = 49
    notes = (
        "Public 2025 paid capital-gains PDF: "
        "https://www.westernsouthern.com/-/media/files/touchstone/tax-planning/capital-gains.pdf "
        "(e.g. Value Fund TVLAX ST $0.16201 / LT $1.28631 / 10.99–11.12% of NAV; "
        "Mid Cap Fund TMAPX LT $1.10236 / 1.86–2.14% of NAV). "
        "Record 12/10/2025; ex/pay 12/11/2025. Tickers are public Class A identifiers; "
        "% of NAV is a share-class range."
    )
    live_limitations = "Year-end book is PDF. Fixture transcribes public Class A rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_capital_gains",
                url="https://www.westernsouthern.com/-/media/files/touchstone/tax-planning/capital-gains.pdf",
                fixture="2025_capital_gains.html",
                live=False,
            )
        ]


class VictorySource(HtmlTableSource):
    slug = "victory"
    display_name = "Victory Capital"
    aum_rank = 50
    priority = 50
    notes = (
        "Distinct from Pioneer / Amundi US: Pioneer open-end estimates stay on `amundi` "
        "(alias `pioneer` / `victory_pioneer`). This adapter is Victory Portfolios I/II "
        "(Integrity / Sycamore / Multi-Cap) — public 10/31/2025 estimate PDF: "
        "https://investor.vcm.com/assets/resources-mutualfunddoc/Victory-Funds-2025-Estimated-Capital-Gains.pdf "
        "(e.g. Integrity Discovery Class A MMEAX ST $0.607411 / LT $3.876127 / 10.07% of NAV; "
        "S&P 500 Index Class A MUXAX ST $0.040958 / LT $1.957923 / 6.72%). "
        "Capital-gains record 12/11/2025; ex 12/12/2025; pay 12/15/2025. "
        "USAA (Portfolios III) and RS books have separate public estimate PDFs on vcm.com."
    )
    live_limitations = "Integrity/Sycamore estimate book is PDF. Fixture transcribes public Class A rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_capital_gains",
                url="https://investor.vcm.com/assets/resources-mutualfunddoc/Victory-Funds-2025-Estimated-Capital-Gains.pdf",
                fixture="2025_estimated_capital_gains.html",
                live=False,
            )
        ]
