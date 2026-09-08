"""Ranks 91–100 boutique US-advisor families with scrapeable public CG books."""

from __future__ import annotations

from app.sources.html_source import HtmlTableSource, PageSpec


class LazardSource(HtmlTableSource):
    slug = "lazard"
    display_name = "Lazard"
    aum_rank = 91
    priority = 91
    notes = (
        "Tax library: https://www.lazardassetmanagement.com/us/en_us/tax-center/document-library "
        "Public 11/24/2025 estimate PDF is the full Institutional / Open / R6 book: "
        "https://www.lazardassetmanagement.com/docs/1791/"
        "LazardFundsAnnualDistributionDeclarationEstimated.pdf "
        "(International Equity Institutional LZIEX ST $0.20 / LT $1.50; "
        "Emerging Markets Equity Advantage Institutional LEAIX LT $0.17; "
        "International Quality Growth Institutional ICMPX ST $0.05 / LT $0.60). "
        "Record 12/18/2025; ex/reinvest 12/19/2025; pay 12/22/2025. "
        "All-dash Concentrated / High Yield rows omitted. Printed 0.00* stored as 0.00."
    )
    live_limitations = (
        "Year-end book is PDF. Fixture transcribes the official Institutional / Open / R6 table."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="tax_document_library_hub",
                url="https://www.lazardassetmanagement.com/us/en_us/tax-center/document-library",
                fixture="tax_document_library_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_estimated_annual_distributions",
                url=(
                    "https://www.lazardassetmanagement.com/docs/1791/"
                    "LazardFundsAnnualDistributionDeclarationEstimated.pdf"
                ),
                fixture="2025_estimated_annual_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            )
        ]


class ManningNapierSource(HtmlTableSource):
    slug = "manning_napier"
    display_name = "Manning & Napier"
    aum_rank = 92
    priority = 92
    notes = (
        "Public 2025 paid-distribution PDF: "
        "https://am.manning-napier.com/media/fund-documents/distributions/2025%20Distributions.pdf "
        "(Callodine Equity Income Class I CEIIX ST $0.4829 / LT $0.46350; "
        "Disciplined Value Class I MNDFX ST $0.0992 / LT $0.56210; "
        "Equity Series Class S EXEYX LT $1.61030; "
        "Pro-Blend Maximum Term Class I MNHIX LT $2.56840). "
        "Year-end record 12/15/2025; ex/reinvest 12/16/2025; pay 12/17/2025. "
        "December YE capital-gain rows only (monthly / quarterly income-only omitted). "
        "Tickers attached only where previously identified (CEIIX / MNDFX / EXEYX / MNHIX); "
        "remaining rows keep official CUSIP / class from the PDF."
    )
    live_limitations = (
        "Paid book is PDF. Fixture transcribes December CG-paying CUSIP/class rows."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_distributions",
                url=(
                    "https://am.manning-napier.com/media/fund-documents/"
                    "distributions/2025%20Distributions.pdf"
                ),
                fixture="2025_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            )
        ]


class WestwoodSource(HtmlTableSource):
    slug = "westwood"
    display_name = "Westwood"
    aum_rank = 93
    priority = 93
    notes = (
        "Tax hub: https://westwoodgroup.com/dividend-tax-information/ "
        "Public 2025 estimate PDF: "
        "https://westwoodgroup.com/wp-content/uploads/2025/10/"
        "Fund-Distribution-2025-Cap-Estimate_STAMPED.pdf "
        "(Quality Value Institutional WHGLX LT $2.235; "
        "Quality MidCap Institutional WWMCX ST $0.250 / LT $0.459; "
        "Quality SmallCap Institutional WHGSX ST $0.422 / LT $0.684). "
        "Record 12/11/2025; ex 12/12/2025; pay 12/15/2025. "
        "The PDF is fund-level for all share classes; tickers are public Institutional identifiers."
    )
    live_limitations = (
        "Estimate book is PDF. Fixture transcribes public Institutional identifiers."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_capital_gains",
                url=(
                    "https://westwoodgroup.com/wp-content/uploads/2025/10/"
                    "Fund-Distribution-2025-Cap-Estimate_STAMPED.pdf"
                ),
                fixture="2025_estimated_capital_gains.html",
                live=True,
                role="estimate",
                empty_ok=True,
            )
        ]


class BostonPartnersSource(HtmlTableSource):
    slug = "boston_partners"
    display_name = "Boston Partners"
    aum_rank = 94
    priority = 94
    notes = (
        "Public 10/31/2025 estimate PDF: "
        "https://www.bostonpartners.com/uploads/2025/11/"
        "b15ac374201c51486acab7203763117a/bp-funds-estimated-cap-gain-dist-10_31_2025.pdf "
        "(All Cap Value Institutional BPAIX ST $0.02 / LT $2.73; "
        "Small Cap Value II Institutional BPSIX ST $0.05 / LT $1.93; "
        "Global Equity Institutional BPGIX ST $0.56 / LT $1.76). "
        "Record 12/11/2025; ex/pay 12/12/2025. "
        "Estimated distribution applies to all share classes; fixture uses printed Inst/Inv tickers. "
        "Emerging Markets Dynamic Equity printed dash / liquidation — omitted. "
        "Published $0.00 ST stored."
    )
    live_limitations = (
        "Estimate book is PDF. Fixture transcribes public Institutional + Investor identifiers."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_capital_gains",
                url=(
                    "https://www.bostonpartners.com/uploads/2025/11/"
                    "b15ac374201c51486acab7203763117a/"
                    "bp-funds-estimated-cap-gain-dist-10_31_2025.pdf"
                ),
                fixture="2025_estimated_capital_gains.html",
                live=True,
                role="estimate",
                empty_ok=True,
            )
        ]


class HomesteadSource(HtmlTableSource):
    slug = "homestead"
    display_name = "Homestead"
    aum_rank = 95
    priority = 95
    notes = (
        "Tax hub: https://www.homesteadadvisers.com/general-tax-information/ "
        "Public 2025 year-end PDF: "
        "https://www.homesteadadvisers.com/wp-content/uploads/Year-End-Distributions.pdf "
        "(Value HOVLX LT $3.7449; Growth HNASX ST $0.0121 / LT $2.4302; "
        "Small-Company Stock HSCSX LT $2.1494). "
        "Record 12/12/2025; ex/reinvest 12/15/2025; pay 12/16/2025. "
        "The PDF is fund-level; tickers are public no-load identifiers."
    )
    live_limitations = "Year-end book is PDF. Fixture transcribes public no-load identifiers."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_year_end_distributions",
                url="https://www.homesteadadvisers.com/wp-content/uploads/Year-End-Distributions.pdf",
                fixture="2025_year_end_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            )
        ]


class MadisonSource(HtmlTableSource):
    slug = "madison"
    display_name = "Madison"
    aum_rank = 96
    priority = 96
    notes = (
        "Public 2025 paid tax-center HTML: "
        "https://madisonfunds.com/resources/tax-center/ "
        "(Large Cap Class A MNVAX LT $1.92670046; "
        "Dividend Income Class A MADAX LT $2.55489945; "
        "Mid Cap Class Y GTSGX ST $0.03280265 / LT $0.45061810). "
        "Amounts are based on gains through October 31. "
        "The live table is fund-level with no ticker column; fixture attaches public "
        "Class A / Y identifiers. Official ETF tickers from "
        "https://madisonfunds.com/etfs/ (MAGG LT $0.00386; MSTI LT $0.05541). "
        "All-None Conservative Allocation / Core Bond / Covered Call omitted."
    )
    live_limitations = (
        "Public HTML is fund-name / ST / LT only (no ticker column). Fixture fallback."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_capital_gains",
                url="https://madisonfunds.com/resources/tax-center/",
                fixture="2025_capital_gains.html",
                live=True,
                role="estimate",
                empty_ok=True,
            )
        ]


class LsvSource(HtmlTableSource):
    slug = "lsv"
    display_name = "LSV"
    aum_rank = 97
    priority = 97
    notes = (
        "Public 2025 year-end PDF: "
        "https://www.lsvasset.com/pdf/fund-docs/2025-Distributions-12-25.pdf "
        "(Value Equity Institutional LSVEX LT $4.4395; "
        "Conservative Value Equity Institutional LSVVX ST $0.0410 / LT $1.5946; "
        "US Managed Volatility Institutional LSVMX ST $0.1063 / LT $1.7713). "
        "Capital-gain record 12/16/2025; ex 12/17/2025; pay 12/18/2025. "
        "The PDF lists Institutional / Investor ticker pairs; fixture uses both. "
        "Income rows use the official December dividend table (record 12/29/2025). "
        "Published $0.0000 ST stored."
    )
    live_limitations = (
        "Year-end book is PDF. Fixture transcribes public Institutional + Investor identifiers."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_year_end_distributions",
                url="https://www.lsvasset.com/pdf/fund-docs/2025-Distributions-12-25.pdf",
                fixture="2025_year_end_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            )
        ]


class LkcmSource(HtmlTableSource):
    slug = "lkcm"
    display_name = "LKCM"
    aum_rank = 98
    priority = 98
    notes = (
        "Public 11/3/2025 estimate PDF: "
        "https://lkcmfunds.com/wp-content/uploads/"
        "2025-LKCM-Year-End-Mutual-Fund-Distribution-Estimates-11-3-25.pdf "
        "(Equity LKEQX LT $3.8475; Small Cap Equity LKSCX LT $1.8102; "
        "Balanced LKBAX ST $0.0059 / LT $1.1276). "
        "Record 12/29/2025; ex/pay 12/30/2025."
    )
    live_limitations = "Estimate book is PDF. Fixture transcribes public ticker rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_year_end_distributions",
                url=(
                    "https://lkcmfunds.com/wp-content/uploads/"
                    "2025-LKCM-Year-End-Mutual-Fund-Distribution-Estimates-11-3-25.pdf"
                ),
                fixture="2025_estimated_year_end_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            )
        ]


class OberweisSource(HtmlTableSource):
    slug = "oberweis"
    display_name = "Oberweis"
    aum_rank = 99
    priority = 99
    notes = (
        "Resources: https://oberweisfunds.com/resources/ "
        "Public 2025 final PDF: "
        "https://oberweisfunds.com/wp-content/uploads/2026/03/2025-Final-Distributions-Sheet.pdf "
        "(Global Opportunities Investor OBEGX LT $3.9791; "
        "Micro-Cap Investor OBMCX LT $0.7189). "
        "Record 12/29/2025; pay 12/30/2025."
    )
    live_limitations = "Year-end book is PDF. Fixture transcribes public Investor / Institutional rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_final_distributions",
                url="https://oberweisfunds.com/wp-content/uploads/2026/03/2025-Final-Distributions-Sheet.pdf",
                fixture="2025_final_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            )
        ]


class RiverparkSource(HtmlTableSource):
    slug = "riverpark"
    display_name = "RiverPark"
    aum_rank = 100
    priority = 100
    notes = (
        "Tax hub: https://www.riverparkfunds.com/how-to-invest.html "
        "Public December 2025 final PDF: "
        "https://riverparkfunds.com/assets/pdfs/news/"
        "Distribution_Info_2025_Website_RFT_FINAL_CAP_GAINS_FINAL_INCOME.pdf "
        "(Large Growth Institutional RPXIX LT $2.6688; "
        "Wedgewood Institutional RWGIX ST $0.0068 / LT $0.5577; "
        "Next Century Large Growth Institutional RPNLX LT $0.7953). "
        "Capital-gain record 12/16/2025; ex 12/17/2025; pay 12/18/2025. "
        "Institutional + Retail paying rows only. All-dash Long/Short, Short Term "
        "High Yield, Floating Rate CMBS, and Next Century Growth omitted."
    )
    live_limitations = (
        "Year-end book is PDF. Fixture transcribes public Institutional + Retail paying rows. "
        "Weekly walk hits the how-to-invest hub (empty/403/PDF-bytes = no-op success)."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="how_to_invest_hub",
                url="https://www.riverparkfunds.com/how-to-invest.html",
                fixture="how_to_invest_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_final_distributions",
                url=(
                    "https://riverparkfunds.com/assets/pdfs/news/"
                    "Distribution_Info_2025_Website_RFT_FINAL_CAP_GAINS_FINAL_INCOME.pdf"
                ),
                fixture="2025_final_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            )
        ]
