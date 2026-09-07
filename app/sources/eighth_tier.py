"""Ranks 71–80 boutique US-advisor families with scrapeable public CG books."""

from __future__ import annotations

from app.sources.html_source import HtmlTableSource, PageSpec


class PrimecapSource(HtmlTableSource):
    slug = "primecap"
    display_name = "PRIMECAP Odyssey"
    aum_rank = 71
    priority = 71
    notes = (
        "Public 10/31/2025 distribution-estimate PDF: "
        "https://www.primecap.com/wp-content/uploads/2025/11/"
        "2025-Distribution-Estimates-as-of-10312025-PCF000287.pdf "
        "(Stock POSKX ST $0.15 / LT $8.25; Growth POGRX ST $0.25 / LT $9.00; "
        "Aggressive Growth POAGX ST $0.30 / LT $6.50). "
        "Record 12/12/2025; ex 12/15/2025. The PDF is fund-level; tickers are "
        "public Investor-class identifiers."
    )
    live_limitations = (
        "Estimate book is PDF. Fixture transcribes public Investor-class identifiers."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_distribution_estimates",
                url=(
                    "https://www.primecap.com/wp-content/uploads/2025/11/"
                    "2025-Distribution-Estimates-as-of-10312025-PCF000287.pdf"
                ),
                fixture="2025_distribution_estimates.html",
                live=False,
            )
        ]


class ArielSource(HtmlTableSource):
    slug = "ariel"
    display_name = "Ariel"
    aum_rank = 72
    priority = 72
    notes = (
        "Public 12/17/2025 paid-history PDF: "
        "https://www.arielinvestments.com/wp-content/uploads/2025/12/"
        "Distributions_ArielFund_as-of-12.17.2025-Final.pdf "
        "(Ariel Fund Investor ARGFX income $0.110534 / ST $0.444905 / LT $8.152412; "
        "Institutional ARAIX income $0.096387 / same ST/LT). "
        "Fixture transcribes the 2025 year-end rows only."
    )
    live_limitations = "Paid book is a multi-decade PDF. Fixture transcribes 2025 year-end rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_year_end_distributions",
                url=(
                    "https://www.arielinvestments.com/wp-content/uploads/2025/12/"
                    "Distributions_ArielFund_as-of-12.17.2025-Final.pdf"
                ),
                fixture="2025_year_end_distributions.html",
                live=False,
            )
        ]


class BairdSource(HtmlTableSource):
    slug = "baird"
    display_name = "Baird"
    aum_rank = 73
    priority = 73
    notes = (
        "Public 2025 final capital-gains PDF: "
        "https://www.bairdassetmanagement.com/siteassets/pdfs/distributions/"
        "2025-final-capital-gains.pdf "
        "(Equity Opportunity Inst BSVIX ST $0.74297 / LT $1.23087; "
        "Mid Cap Growth Inst BMDIX ST $0.14763 / LT $2.19832; "
        "Chautauqua Global Growth Inst CCGIX ST $0.11209 / LT $0.69980). "
        "Record 12/12/2025; ex 12/15/2025; pay 12/16/2025. "
        "Bond book is all None this year — fixture uses equity rows with amounts."
    )
    live_limitations = "Year-end book is PDF. Fixture transcribes public Institutional equity rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_final_capital_gains",
                url=(
                    "https://www.bairdassetmanagement.com/siteassets/pdfs/"
                    "distributions/2025-final-capital-gains.pdf"
                ),
                fixture="2025_final_capital_gains.html",
                live=False,
            )
        ]


class LongleafSource(HtmlTableSource):
    slug = "longleaf"
    display_name = "Longleaf Partners"
    aum_rank = 74
    priority = 74
    notes = (
        "Public paid history HTML: "
        "https://southeasternasset.com/investment-offerings/longleaf-partners-fund/ "
        "(Partners Fund LLPFX 2025 income $0.2149 / ST $0.8486 / LT $1.7935). "
        "Record 12/15/2025; ex 12/16/2025."
    )
    live_limitations = (
        "Live HTML is public but product-page layout may not parse. Fixture fallback."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_partners_fund_distributions",
                url="https://southeasternasset.com/investment-offerings/longleaf-partners-fund/",
                fixture="2025_partners_fund_distributions.html",
                live=True,
            )
        ]


class BuffaloSource(HtmlTableSource):
    slug = "buffalo"
    display_name = "Buffalo"
    aum_rank = 75
    priority = 75
    notes = (
        "Public 10/31/2025 estimate PDF: "
        "https://buffalofunds.com/wp-content/uploads/2025/11/Final-Cap-Gains-Estimates.pdf "
        "(Blue Chip Growth Investor BUFEX ST $0.50424 / LT $3.35047; "
        "Growth Investor BUFGX ST $0.04585 / LT $2.22250; "
        "Mid Cap Discovery Investor BUFTX LT $3.74685). "
        "CG record/pay 12/04–12/05/2025. The PDF is class-level without tickers; "
        "tickers are public Investor-class identifiers."
    )
    live_limitations = (
        "Estimate book is PDF. Fixture transcribes public Investor-class identifiers."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_capital_gains",
                url="https://buffalofunds.com/wp-content/uploads/2025/11/Final-Cap-Gains-Estimates.pdf",
                fixture="2025_estimated_capital_gains.html",
                live=False,
            )
        ]


class GqgSource(HtmlTableSource):
    slug = "gqg"
    display_name = "GQG Partners"
    aum_rank = 76
    priority = 76
    notes = (
        "Public 9/30/2025 estimate PDF: "
        "https://gqg.com/content/2025/10/"
        "2025-Estimated-Capital-Gain-Distributions-09.30.pdf "
        "(US Select Quality Equity Inst GQEIX LT $0.81 / 3.7% of NAV; "
        "Global Quality Equity Inst GQRIX LT $0.97 / 5.1% of NAV; "
        "Global Quality Value Inst GQFIX LT $0.27 / 2.2% of NAV). "
        "Record 12/17/2025; ex 12/18/2025; pay 12/19/2025."
    )
    live_limitations = "Estimate book is PDF. Fixture transcribes public Institutional rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_capital_gains",
                url=(
                    "https://gqg.com/content/2025/10/"
                    "2025-Estimated-Capital-Gain-Distributions-09.30.pdf"
                ),
                fixture="2025_estimated_capital_gains.html",
                live=False,
            )
        ]


class ThirdAvenueSource(HtmlTableSource):
    slug = "third_avenue"
    display_name = "Third Avenue"
    aum_rank = 77
    priority = 77
    notes = (
        "Public 2025 paid HTML: "
        "https://www.thirdave.com/2025-income-capital-gain-distributions "
        "(Value TAVFX income $1.72194 / LT $3.34191; "
        "Small-Cap Value TASCX ST $0.03591 / LT $0.70304; "
        "Real Estate Value TAREX ST $0.00295 / LT $1.09875). "
        "Record 12/09/2025; ex/reinvest 12/10/2025; pay 12/11/2025."
    )
    live_limitations = (
        "Live HTML is public but page layout may not parse. Fixture fallback."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_income_capital_gain_distributions",
                url="https://www.thirdave.com/2025-income-capital-gain-distributions",
                fixture="2025_income_capital_gain_distributions.html",
                live=True,
            )
        ]


class HeartlandSource(HtmlTableSource):
    slug = "heartland"
    display_name = "Heartland"
    aum_rank = 78
    priority = 78
    notes = (
        "Public 2025 paid HTML: "
        "https://www.heartlandadvisors.com/Resources/Tax-Information "
        "(Mid Cap Value Investor HRMDX LT $0.12387; "
        "Value Investor HRTVX ST $0.05228 / LT $4.34950; "
        "Value Plus Investor HRVIX no CG in 2025). "
        "Record 12/18/2025; pay 12/19/2025."
    )
    live_limitations = (
        "Live HTML is public but tax-center layout may not parse. Fixture fallback."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_year_end_distributions",
                url="https://www.heartlandadvisors.com/Resources/Tax-Information",
                fixture="2025_year_end_distributions.html",
                live=True,
            )
        ]


class FmiSource(HtmlTableSource):
    slug = "fmi"
    display_name = "FMI"
    aum_rank = 79
    priority = 79
    notes = (
        "Public 2025 distribution-summary PDF: "
        "https://www.fmimgt.com/fmi/funds/cs/CS_distribution_summary_2025.pdf "
        "(Common Stock Institutional FMIUX income $0.11660616 / ST $0.47986 / LT $3.8237; "
        "Investor FMIMX income $0.1803821 / same ST/LT). "
        "Ex 12/19/2025. Fixture transcribes the 2025 year-end rows only."
    )
    live_limitations = "Paid book is a multi-decade PDF. Fixture transcribes 2025 year-end rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_distribution_summary",
                url="https://www.fmimgt.com/fmi/funds/cs/CS_distribution_summary_2025.pdf",
                fixture="2025_distribution_summary.html",
                live=False,
            )
        ]


class ImpaxSource(HtmlTableSource):
    slug = "impax"
    display_name = "Impax / Pax"
    aum_rank = 80
    priority = 80
    notes = (
        "Hub: https://impaxam.com/customer-service/distributions/ "
        "Public December 2025 paid table (crawled from that URL): "
        "Large Cap Investor PAXLX / Institutional PXLIX LT $3.19835; "
        "Small Cap Investor PXSCX ST $0.18529 / LT $0.99442; "
        "Global Sustainable Infrastructure Investor PGINX ST $0.00116 / LT $4.82181. "
        "Record 12/19/2025; ex/reinvest 12/22/2025; pay 12/23/2025."
    )
    live_limitations = (
        "Live hub is geo/investor-type gated. Fixture transcribes the public December 2025 table."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_year_end_distributions",
                url="https://impaxam.com/customer-service/distributions/",
                fixture="2025_year_end_distributions.html",
                live=False,
            )
        ]
