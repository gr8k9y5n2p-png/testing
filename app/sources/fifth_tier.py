from __future__ import annotations

from app.sources.html_source import HtmlTableSource, PageSpec


class HarborSource(HtmlTableSource):
    slug = "harbor"
    display_name = "Harbor"
    aum_rank = 41
    priority = 41
    notes = (
        "US-domiciled. Tax center: https://www.harborcapital.com/tax-center/ "
        "No public filled ICI. Public 10/23/2025 year-end estimate PDF: "
        "https://assets.harborcapital.com/docs/Distribution_Estimates_Mutual_Funds_2025.pdf "
        "(Capital Appreciation Institutional HACAX LT $11.89 / 9% of NAV). "
        "2024 sibling Distribution_Estimates_Mutual_Funds_2024.pdf 404. "
        "Institutional tickers attached from the official Harbor Funds prospectus "
        "(HACAX / HSICX / HAOSX / HASCX / HAIDX / HAISX / HAVLX / HMCLX / HAMVX). "
        "Third-party combined dividend totals unused (no official ST/LT split). "
        "Weekly walk also hits the tax-center hub."
    )
    live_limitations = "Estimate book is PDF. Fixture transcribes public Institutional-class rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_year_end_distributions",
                url="https://assets.harborcapital.com/docs/Distribution_Estimates_Mutual_Funds_2025.pdf",
                fixture="2025_estimated_year_end_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="tax_center_hub",
                url="https://www.harborcapital.com/tax-center/",
                fixture="tax_center_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
        ]


class NationwideSource(HtmlTableSource):
    slug = "nationwide"
    display_name = "Nationwide"
    aum_rank = 42
    priority = 42
    notes = (
        "US-domiciled. Year-end hub: "
        "https://www.nationwide.com/personal/investing/mutual-funds/year-end-information/ "
        "No public filled ICI. Public 2025 capital-gains distribution PDF (MFN-0435AO): "
        "https://nationwidefinancial.com/media/pdf/MFN-0435AO.pdf "
        "(Bailard Technology & Science Class A NWHOX LT $3.7231 / 12.48% of NAV). "
        "2024 sibling MFN-0434AO is not a capital-gains book (HTML/8937-style). "
        "MFN-1042AO extract is not an ST/LT grid. "
        "Hub PDF link is unversioned — prior-year ST/LT not transcribed. "
        "Weekly walk also hits the year-end information hub. "
        "Live MFN-0435AO GET 403 this session — deferred after noting; "
        "existing Class A fixture left as-is (no invented amounts)."
    )
    live_limitations = (
        "Family book is PDF. Automated GET is sometimes Akamai-denied without a "
        "browser/query token; fixture transcribes public Class A rows. "
        "403 this session is no-op success."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_capital_gains_distributions",
                url="https://nationwidefinancial.com/media/pdf/MFN-0435AO.pdf",
                fixture="2025_capital_gains_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="year_end_information_hub",
                url="https://www.nationwide.com/personal/investing/mutual-funds/year-end-information/",
                fixture="year_end_information_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
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
        "use this adapter, not a distinct allianzgi source. "
        "2024 estimate PDF: https://individuals.voya.com/document/tax-center/2024-estimated-capital-gains.pdf "
        "(Large-Cap Growth NLCAX ST $0.000 / LT $1.905 / 3.39% of NAV)."
    )
    live_limitations = "Estimate book is PDF. Fixture transcribes public open-end rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_capital_gains",
                url="https://individuals.voya.com/document/tax-center/2025-estimated-capital-gains.pdf",
                fixture="2025_estimated_capital_gains.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2024_estimated_capital_gains",
                url="https://individuals.voya.com/document/tax-center/2024-estimated-capital-gains.pdf",
                fixture="2024_estimated_capital_gains.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="tax_center_hub",
                url="https://individuals.voya.com/product/tax-center/about-capital-gain-distributions",
                fixture="tax_center_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
        ]


class OakmarkSource(HtmlTableSource):
    slug = "oakmark"
    display_name = "Oakmark / Harris Associates"
    aum_rank = 44
    priority = 44
    notes = (
        "Public 2025 year-end distribution HTML: "
        "https://oakmark.com/news-insights/2025-oakmark-year-end-fund-distributions/ "
        "with official Investor / Advisor / Institutional / R6 tickers from "
        "https://oakmark.com/our-funds/ "
        "(e.g. International Small Cap Investor OAKEX LT $0.7640 / 5.13% of NAV; "
        "Oakmark Fund Investor OAKMX income $1.5797 / 0.91% of NAV — no 2025 CG). "
        "Record 12/10/2025; ex 12/11/2025; pay 12/12/2025. "
        "Published $0.0000 stored. "
        "2024 paid YE HTML (live sibling 404; Wayback): Investor OAKEX ST $0.0276 / LT $0.7241; "
        "OAKMX / OAKIX published $0.0000 CG stored. "
        "Tax estimates hub is % of NAV only (no ST/LT $/share). "
        "Tax guide: https://oakmark.com/wp-content/uploads/sites/3/documents/HarrisOakmark-Tax-Information-Guide.pdf"
    )
    live_limitations = (
        "Live page is public HTML with class-section tables and no ticker column. "
        "Static parse may return 0 rows. Fixture fallback with official share-class tickers."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_year_end_distributions",
                url="https://oakmark.com/news-insights/2025-oakmark-year-end-fund-distributions/",
                fixture="2025_year_end_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2024_year_end_distributions",
                url="https://oakmark.com/news-insights/2024-oakmark-year-end-fund-distributions/",
                fixture="2024_year_end_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="capital_gain_tax_estimates_hub",
                url="https://oakmark.com/news-insights/oakmark-capital-gain-tax-estimates/",
                fixture="capital_gain_tax_estimates_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
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
        "Record 12/10/2025; ex/pay/reinvest 12/11/2025. "
        "2024 estimate PDF: "
        "https://www.tweedyfunds.com/wp-content/uploads/sites/10/2024/09/"
        "2024-Estimated-Distributions-8-31-24.pdf "
        "(International Value TBGVX LT $1.706; Value Fund TWEBX LT $1.604; printed None ST omitted). "
        "2024 Final Distributions sibling URLs 404."
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
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2024_estimated_year_end_distributions",
                url=(
                    "https://www.tweedyfunds.com/wp-content/uploads/sites/10/2024/09/"
                    "2024-Estimated-Distributions-8-31-24.pdf"
                ),
                fixture="2024_estimated_year_end_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="estimated_distributions_hub",
                url="https://www.tweedyfunds.com/mutual-funds/international-value-fund-distributions/",
                fixture="estimated_distributions_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
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
        "Record 12/26/2025; ex/pay/reinvest 12/29/2025. "
        "2024 year-end dividend summary (Wayback; live GET 403): "
        "https://gabelli.com/wp-content/uploads/2025/09/GabelliTetonKeeleyETF-2024-Year-End-Dividend-Summary-1.pdf "
        "(Growth AAA GABGX LT $6.96640; Asset AAA GABAX LT $6.83330). "
        "Live 2025 memo GET 403 this session — deferred after noting; "
        "existing Class AAA fixture left as-is (no invented amounts)."
    )
    live_limitations = (
        "Year-end book is PDF. Live GET is sometimes 403; fixture transcribes "
        "public Class AAA rows. 403 this session is no-op success."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_year_end_distributions",
                url="https://gabelli.com/wp-content/uploads/2025/12/Distribution-memo-12.29.2025.pdf",
                fixture="2025_year_end_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2024_year_end_distributions",
                url="https://gabelli.com/wp-content/uploads/2025/09/GabelliTetonKeeleyETF-2024-Year-End-Dividend-Summary-1.pdf",
                fixture="2024_year_end_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="open_end_distributions_hub",
                url="https://gabelli.com/funds/open-ends/distributions/",
                fixture="open_end_distributions_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
        ]


class RoyceSource(HtmlTableSource):
    slug = "royce"
    display_name = "Royce"
    aum_rank = 47
    priority = 47
    notes = (
        "Public 2025 open-end year-end distribution HTML: "
        "https://www.royceinvest.com/news/2025/4Q25/open-end-funds-2025-year-end-distributions "
        "Full printed ticker PDF: "
        "https://www.royceinvest.com/news/2025/4Q25/PDF/royce-open-end-funds-distributions-2025.pdf "
        "(e.g. Small-Cap Total Return Investment RYTRX ST $0.0257 / LT $0.7656; "
        "Micro-Cap Investment RYOTX LT $1.6509). "
        "Record 12/10/2025; ex/pay 12/11/2025. Printed em-dashes omitted. "
        "2024 paid YE PDF: "
        "https://www.royceinvest.com/news/2024/4Q24/PDF/royce-open-end-funds-distributions-2024.pdf "
        "(Small-Cap Total Return Investment RYTRX ST $0.0584 / LT $0.2980). "
        "CEF 19(a) notices are a separate closed-end book."
    )
    live_limitations = (
        "Live HTML is public but table layout/headers may not parse. "
        "Fixture transcribes the official full printed ticker book."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_year_end_distributions",
                url="https://www.royceinvest.com/news/2025/4Q25/open-end-funds-2025-year-end-distributions",
                fixture="2025_year_end_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2024_year_end_distributions",
                url="https://www.royceinvest.com/news/2024/4Q24/PDF/royce-open-end-funds-distributions-2024.pdf",
                fixture="2024_year_end_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="year_end_distributions_hub",
                url="https://www.royceinvest.com/news/2024/4Q24/open-end-funds-2024-year-end-distributions",
                fixture="year_end_distributions_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
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
        "MainStay funds were rebranded NYLI; this adapter covers both names. "
        "2025 flyer is the full paying-fund estimate book (Class I tickers from "
        "official NYLI prices/equities pages). No harvestable 2024 ST/LT family "
        "book found (do not invent ranges)."
    )
    live_limitations = "Estimate book is PDF with per-share ranges. Fixture transcribes public Class I identifiers."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_capital_gains",
                url="https://www.nylim.com/assets/documents/tax/cap-gains-estimate.pdf",
                fixture="2025_estimated_capital_gains.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
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
        "Record 12/10/2025; ex/pay 12/11/2025. Class A tickers from official "
        "westernsouthern.com/touchstone product pages (TVLAX / TMAPX / SEBLX / TFOAX / "
        "TACLX / TCVAX / TEQAX / TGVFX / TEGAX / TSNAX / SAGWX); ETF tickers "
        "TSEC / SIO / TUSI from official Touchstone ETF pages. Dividend Equity / "
        "International Value / Large Cap Focused / Large Company Growth remain "
        "name-only. "
        "2024 supplemental tax PDF is DRD / Treasury-source, not an ST/LT CG book."
    )
    live_limitations = "Year-end book is PDF. Fixture transcribes public Class A rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_capital_gains",
                url="https://www.westernsouthern.com/-/media/files/touchstone/tax-planning/capital-gains.pdf",
                fixture="2025_capital_gains.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
        ]


class VictorySource(HtmlTableSource):
    slug = "victory"
    display_name = "Victory Capital"
    aum_rank = 50
    priority = 50
    notes = (
        "Distinct from Pioneer / Amundi US: Pioneer open-end books stay on `amundi` "
        "(alias `pioneer` / `victory_pioneer`). This adapter is Victory Portfolios I/II "
        "(Integrity / Sycamore / Multi-Cap) — public 10/31/2025 estimate PDF: "
        "https://investor.vcm.com/assets/resources-mutualfunddoc/Victory-Funds-2025-Estimated-Capital-Gains.pdf "
        "(e.g. Integrity Discovery Class A MMEAX ST $0.607411 / LT $3.876127 / 10.07% of NAV; "
        "S&P 500 Index Class A MUXAX ST $0.040958 / LT $1.957923 / 6.72%). "
        "Capital-gains record 12/11/2025; ex 12/12/2025; pay 12/15/2025. "
        "USAA (Portfolios III) and RS books have separate public estimate PDFs on vcm.com. "
        "2025 final Portfolios I/II + RS + Portfolios III (USAA) official PDFs "
        "are the full printed books (MMEAX LT $3.922505; RSGRX LT $1.817625; "
        "USSPX ST $0.026267 / LT $2.615144). Pioneer / Victory Portfolios IV "
        "is covered by the included `amundi` adapter (Eric 2026-09-08). "
        "2024 final Class A book: "
        "https://investor.vcm.com/assets/resources-mutualfunddoc/Victory-Funds-2024-Final-Ordinary-Income-and-Capital-Gains.pdf "
        "(Integrity Discovery MMEAX ST $0.801347 / LT $3.015874 / 8.95% of NAV). "
        "Wave 7 lookback: official 2022 hyphenated + 2023 space-encoded I/II finals "
        "(MMEAX 2022 LT $2.389672 / 2023 LT $0.390522; VETAX 2022 LT $2.782434 / "
        "2023 LT $2.095967), 2023–2024 RS MF books (RSGRX 2023 LT $0.036599 / "
        "2024 LT $2.023191; VIP series omitted), and 2023–2024 Portfolios III "
        "(USSPX 2023 LT $0.515883 / 2024 LT $1.855318). 2021 I/II / RS / III "
        "sibling URLs still 404 — unmatched / Undisclosed."
    )
    live_limitations = (
        "Integrity/Sycamore/RS/USAA books are PDF. Weekly walk uses the tax-center "
        "hub + 2025 estimate PDF; empty/PDF-bytes pages are no-op success."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="tax_center_hub",
                url="https://investor.vcm.com/tools-resources/tax-center",
                fixture="tax_center_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_estimated_capital_gains",
                url="https://investor.vcm.com/assets/resources-mutualfunddoc/Victory-Funds-2025-Estimated-Capital-Gains.pdf",
                fixture="2025_estimated_capital_gains.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_final_ordinary_income_and_capital_gains",
                url="https://investor.vcm.com/assets/resources-mutualfunddoc/Victory-Funds-2025-Final-Ordinary-Income-and-Capital-Gains-Distributions.pdf",
                fixture="2025_final_ordinary_income_and_capital_gains.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2025_rs_final_ordinary_income_and_capital_gains",
                url="https://investor.vcm.com/assets/resources-mutualfunddoc/Victory-RS-Funds-2025-Final-Ordinary-Income-and-Capital-Gains%20Distributions.pdf",
                fixture="2025_rs_final_ordinary_income_and_capital_gains.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2025_portfolios_iii_final_ordinary_income_and_capital_gains",
                url="https://investor.vcm.com/assets/resources-mutualfunddoc/Victory-Portfolios-III-Mutual-Funds-Final-2025-Ordinary-Income-and-Capital-Gain-Distributions.pdf",
                fixture="2025_portfolios_iii_final_ordinary_income_and_capital_gains.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2024_final_ordinary_income_and_capital_gains",
                url="https://investor.vcm.com/assets/resources-mutualfunddoc/Victory-Funds-2024-Final-Ordinary-Income-and-Capital-Gains.pdf",
                fixture="2024_final_ordinary_income_and_capital_gains.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2024_rs_final_ordinary_income_and_capital_gains",
                url="https://investor.vcm.com/assets/resources-mutualfunddoc/Victory-RS-and-VVI-Funds-2024-Final-Ordinary-Income-and-Capital-Gains.pdf",
                fixture="2024_rs_final_ordinary_income_and_capital_gains.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2024_portfolios_iii_final_ordinary_income_and_capital_gains",
                url="https://investor.vcm.com/assets/resources-mutualfunddoc/Victory-Portfolios-III-Mutual-Funds-2024-Final-Income-and-Capital-Gain-Distributions.pdf",
                fixture="2024_portfolios_iii_final_ordinary_income_and_capital_gains.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2023_final_ordinary_income_and_capital_gains",
                url="https://investor.vcm.com/assets/resources-mutualfunddoc/Victory%20Funds%202023%20Final%20Ordinary%20Income%20and%20Capital%20Gains.pdf",
                fixture="2023_final_ordinary_income_and_capital_gains.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2023_rs_final_ordinary_income_and_capital_gains",
                url="https://investor.vcm.com/assets/resources-mutualfunddoc/Victory%20RS%20and%20VVI%202023%20Final%20Ordinary%20Income%20and%20Capital%20Gains.pdf",
                fixture="2023_rs_final_ordinary_income_and_capital_gains.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2023_portfolios_iii_final_ordinary_income_and_capital_gains",
                url="https://investor.vcm.com/assets/resources-mutualfunddoc/Victory%20Portfolios%20III%202023%20Final%20Capital%20Gain%20and%20Income%20Distributions.pdf",
                fixture="2023_portfolios_iii_final_ordinary_income_and_capital_gains.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2022_final_ordinary_income_and_capital_gains",
                url="https://investor.vcm.com/assets/resources-mutualfunddoc/Victory-Funds-2022-Final-Ordinary-Income-and-Capital-Gains.pdf",
                fixture="2022_final_ordinary_income_and_capital_gains.html",
                live=False,
                role="history",
            ),
        ]
