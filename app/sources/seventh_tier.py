from __future__ import annotations

from app.sources.html_source import HtmlTableSource, PageSpec


class TcwSource(HtmlTableSource):
    slug = "tcw"
    display_name = "TCW"
    aum_rank = 61
    priority = 61
    notes = (
        "Public 2025 paid capital-gains PDF: "
        "https://edge.sitecorecloud.io/thetcwgroupc320-tcwweb7bc3-prod0f26-25f9/media/"
        "Downloads/TCW/Products/US-Funds/TCW-Funds/Distribution-and-Tax-Information/"
        "TCW-FUND-Distributions-final.pdf?sc_lang=en "
        "(e.g. Relative Value Large Cap TGDIX LT $3.4797; Relative Value Mid Cap "
        "TGVOX LT $5.7329; Concentrated Large Cap Growth TGCEX LT $3.7713). "
        "Equity record 12/26/2025, ex/pay 12/29/2025. Allocation fund record "
        "12/30/2025, ex/pay 12/31/2025. The PDF is fund-level; tickers are "
        "public Class I identifiers. "
        "The unversioned TCW-FUND-Distributions-final.pdf filename now serves 2025; "
        "no dated official 2024 sibling stored. "
        "Official 5y parallel R leftover re-probe (2026-09-13): dated 2021–2024 "
        "final siblings unpublished; product-page capital-gains history is "
        "Incapsula-walled. Leftover years stay unmatched."
    )
    live_limitations = (
        "Year-end book is PDF. Weekly walk uses the unversioned final PDF; "
        "empty/PDF-bytes pages are no-op success. 2024 dated URL missing."
    )

    def pages(self) -> list[PageSpec]:
        pdf = (
            "https://edge.sitecorecloud.io/thetcwgroupc320-tcwweb7bc3-prod0f26-25f9/"
            "media/Downloads/TCW/Products/US-Funds/TCW-Funds/"
            "Distribution-and-Tax-Information/TCW-FUND-Distributions-final.pdf"
            "?sc_lang=en"
        )
        return [
            PageSpec(
                name="tax_center_hub",
                url=pdf,
                fixture="tax_center_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_capital_gains",
                url=pdf,
                fixture="2025_capital_gains.html",
                live=False,
                role="history",
            ),
        ]


class BridgewaySource(HtmlTableSource):
    slug = "bridgeway"
    display_name = "Bridgeway"
    aum_rank = 62
    priority = 62
    notes = (
        "Hub: https://bridgewayfunds.com/mutual-funds/distributions/ "
        "Public 2025 year-end estimate PDF: "
        "https://bridgewayfunds.com/wp-content/uploads/sites/2/2025/11/"
        "2025-Distribution-Estimates-for-Website.pdf "
        "(e.g. Aggressive Investors 1 BRAGX LT $17.63983; Ultra-Small Company "
        "BRUSX LT $3.25592; Global Opportunity BRGOX ST $0.45243). "
        "Record 12/15/2025; ex/pay 12/16/2025. "
        "Official 2024 estimate PDF: "
        "https://bridgewayfunds.com/wp-content/uploads/sites/2/2024/11/"
        "2024-Distribution-Estimates-for-Website.pdf "
        "(BRAGX LT $2.54426; BRUSX ST $1.13357; BRSVX LT $2.17584; BOSVX LT $1.41164). "
        "BRGOX 2024 NII expected with no amount — omitted. "
        "Official 5y parallel R leftover: issuer product-page Historical "
        "Distribution tables plus paid 2022 / 2024 PDFs fill leftover years "
        "(BRAGX / BRUSX / BRSVX / BOSVX 2021–2025; BRGOX 2024–2025; "
        "BRSIX 2022+2024). Published $0.0000 stored. BRSIX 2021/2023/2025 "
        "and BRGOX 2021–2023 (inception 10/15/2024) stay unmatched. "
        "BRBPX / BOTSX are not in-book leftovers."
    )
    live_limitations = (
        "Estimate book is PDF. Weekly walk uses the distributions hub + 2025 estimate PDF; "
        "empty/PDF-bytes pages are no-op success."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="distributions_hub",
                url="https://bridgewayfunds.com/mutual-funds/distributions/",
                fixture="distributions_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_estimated_distributions",
                url=(
                    "https://bridgewayfunds.com/wp-content/uploads/sites/2/2025/11/"
                    "2025-Distribution-Estimates-for-Website.pdf"
                ),
                fixture="2025_estimated_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2024_estimated_distributions",
                url=(
                    "https://bridgewayfunds.com/wp-content/uploads/sites/2/2024/11/"
                    "2024-Distribution-Estimates-for-Website.pdf"
                ),
                fixture="2024_estimated_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="leftover_paid_parallel_r",
                url="https://bridgewayfunds.com/mutual-funds/distributions/",
                fixture="leftover_paid_parallel_r.html",
                live=False,
                role="history",
            ),
        ]


class JensenSource(HtmlTableSource):
    slug = "jensen"
    display_name = "Jensen"
    aum_rank = 63
    priority = 63
    notes = (
        "Public 2025 paid capital-gains HTML: "
        "https://www.jenseninvestment.com/insights/2025-growth-mutual-fund-distributions/ "
        "(Quality Growth Class J JENSX / Class I JENIX ST $0.15 / LT $16.65). "
        "Record 11/12/2025; ex/pay 11/13/2025. "
        "Official 2024 PDF "
        "https://www.jenseninvestment.com/wp-content/uploads/2024/11/"
        "2024.11.13-jensen-funds-quality-growth-quality-mid-cap-capital-gains-dividend-distributions.pdf "
        "(JENSX / JENIX LT $6.77; printed no-ST omitted; Mid Cap LT $1.10 "
        "share-class tickers were not printed — omitted). "
        "Official 5y parallel R leftover re-probe (2026-09-13): 2021–2023 "
        "insights / dated YE PDFs 404; live quality-growth page 403. "
        "Fiscal annual-report totals are not calendar YE with printed dates — "
        "leftover years stay unmatched."
    )
    live_limitations = (
        "Live page is public HTML with prose lists, not a parseable table. "
        "Weekly walk uses the 2025 HTML; empty/SPA pages are no-op success."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_year_end_distributions",
                url="https://www.jenseninvestment.com/insights/2025-growth-mutual-fund-distributions/",
                fixture="2025_year_end_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2024_year_end_distributions",
                url=(
                    "https://www.jenseninvestment.com/wp-content/uploads/2024/11/"
                    "2024.11.13-jensen-funds-quality-growth-quality-mid-cap-capital-gains-"
                    "dividend-distributions.pdf"
                ),
                fixture="2024_year_end_distributions.html",
                live=False,
                role="history",
            ),
        ]


class DiamondHillSource(HtmlTableSource):
    slug = "diamond_hill"
    display_name = "Diamond Hill"
    aum_rank = 64
    priority = 64
    notes = (
        "Paid history HTML: https://www.diamond-hill.com/investment-strategies/distributions/mutual-funds/ "
        "Public 10/31/2025 estimate PDF: "
        "https://www.diamond-hill.com/sitefiles/live/documents/distributions/"
        "dhf-capital-gain-estimates-as-of-10-31-25.pdf "
        "(e.g. Small Cap DHSCX LT $1.393 / 5.46% of NAV; Mid Cap DHPAX LT $2.698 / "
        "14.46%; Large Cap DHLAX ST $0.001 / LT $1.829 / 5.45%). "
        "Record 12/11/2025; ex 12/12/2025; pay 12/15/2025. "
        "The PDF is fund-level; Investor tickers from official diamond-hill.com "
        "product pages (DHSCX / DHMAX / DHPAX / DHLAX / DHTAX / DIAMX / DHIAX). "
        "Loss-carryforward bond funds omitted. "
        "Official 2024 estimate sibling "
        "https://www.diamond-hill.com/sitefiles/live/documents/distributions/"
        "dhf-capital-gain-estimates-as-of-10-31-24.pdf "
        "(DHSCX LT $2.511; DHPAX LT $1.311; DHLAX ST $0.035 / LT $2.900; "
        "printed dash ST omitted; loss-carryforward funds omitted). "
        "Official 5y parallel R leftover: issuer paid-history HTML "
        "https://www.diamond-hill.com/investment-strategies/distributions/mutual-funds/ "
        "fills leftover Investor years 2021–2025 (DHSCX / DHMAX / DHPAX / "
        "DHLAX / DHTAX / DIAMX / DHIAX). Class I / Y / C are not in-book "
        "leftovers — omitted, not copied."
    )
    live_limitations = (
        "Estimate book is PDF. Weekly walk uses the 2025 estimate PDF; "
        "empty/PDF-bytes pages are no-op success."
    )

    def pages(self) -> list[PageSpec]:
        docs = "https://www.diamond-hill.com/sitefiles/live/documents/distributions"
        return [
            PageSpec(
                name="2025_estimated_capital_gains",
                url=f"{docs}/dhf-capital-gain-estimates-as-of-10-31-25.pdf",
                fixture="2025_estimated_capital_gains.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2024_estimated_capital_gains",
                url=f"{docs}/dhf-capital-gain-estimates-as-of-10-31-24.pdf",
                fixture="2024_estimated_capital_gains.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="distributions_hub",
                url="https://www.diamond-hill.com/investment-strategies/distributions/mutual-funds/",
                fixture="distributions_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="leftover_paid_parallel_r",
                url="https://www.diamond-hill.com/investment-strategies/distributions/mutual-funds/",
                fixture="leftover_paid_parallel_r.html",
                live=False,
                role="history",
            ),
        ]


class ChamplainSource(HtmlTableSource):
    slug = "champlain"
    display_name = "Champlain"
    aum_rank = 65
    priority = 65
    notes = (
        "Public 12/16/2025 final PDF: "
        "https://cipvt.com/wp-content/uploads/2025/12/"
        "Champlain-Funds-2025-Year-End-Distributions-Final-12-16-25.pdf "
        "(e.g. Mid Cap CIPIX ST $0.0609 / LT $3.5103 / 14.65% of NAV; "
        "Small Company CIPNX ST $0.9250 / LT $2.9217 / 17.79% of NAV). "
        "Record 12/15/2025; ex 12/16/2025; pay 12/17/2025. "
        "October estimate reprint: "
        "https://cipvt.com/wp-content/uploads/2025/10/"
        "Champlain-Estimated-Yr-End-Distributions-2025-vr2-93025.pdf "
        "Leftover paid year-end 2021–2024 for in-book Institutional CIPIX / CIPNX / CIPTX. "
        "Advisor CIPMX / CIPSX and Emerging Markets CIPDX / CIPQX not attached. "
        "Official printed $0.0000 stored (2023 ST; CIPTX 2023 ST/LT). "
        "CIPTX 2021–2022 unpublished on issuer year-end books."
    )
    live_limitations = "Year-end book is PDF. Fixture transcribes public Institutional tickers."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_final_distributions",
                url=(
                    "https://cipvt.com/wp-content/uploads/2025/12/"
                    "Champlain-Funds-2025-Year-End-Distributions-Final-12-16-25.pdf"
                ),
                fixture="2025_final_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="leftover_paid_year_end_parallel_s",
                url=(
                    "https://cipvt.com/wp-content/uploads/2024/12/"
                    "Champlain-Yr-End-Distributions-2024.pdf"
                ),
                fixture="leftover_paid_year_end_parallel_s.html",
                live=False,
                role="history",
                large_aum_only=False,
            ),
        ]


class DriehausSource(HtmlTableSource):
    slug = "driehaus"
    display_name = "Driehaus"
    aum_rank = 66
    priority = 66
    notes = (
        "Public 2025 year-end distributions PDF: "
        "https://www.driehaus.com/system/uploads/fae/file/asset/419/"
        "DMF_Year_end_Distribution_2025.pdf "
        "(e.g. Micro Cap Growth DMCRX ST $0.079978 / LT $2.073159; "
        "Global DMAGX ST $0.776804 / LT $1.422216). "
        "Record 12/17/2025; ex/pay 12/18/2025. Published $0.00 stored. "
        "Tickers from official driehaus.com fund pages / SEC series list "
        "(DMCRX / DVSMX / DNSMX / DSMDX / DRIOX / DIDEX / DREGX / DIEMX / DRESX / "
        "DEVDX / DMAGX). Amounts unchanged. Official 5y parallel T leftover "
        "re-probe: DMF_Year_end_Distribution_2021–2024 sibling PDFs unpublished "
        "(Wayback CDX empty for Distribution filenames; performance Dividends "
        "& Distributions tab is JS). Leftover 2021–2024 stay unmatched."
    )
    live_limitations = (
        "Year-end book is PDF. Fixture transcribes the official full book; "
        "tickers from official product pages / SEC series list."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_year_end_distributions",
                url=(
                    "https://www.driehaus.com/system/uploads/fae/file/asset/419/"
                    "DMF_Year_end_Distribution_2025.pdf"
                ),
                fixture="2025_year_end_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            )
        ]


class HotchkisWileySource(HtmlTableSource):
    slug = "hotchkis"
    display_name = "Hotchkis & Wiley"
    aum_rank = 67
    priority = 67
    notes = (
        "Public December 2025 paid PDF: "
        "https://www.hwcm.com/wp-content/uploads/2025/03/"
        "HW-Funds-Dec-2025-Div-Cap-Gain-Distributions.pdf "
        "(e.g. Large Cap Fundamental Value I HWLIX LT $2.83442; "
        "Value Opportunities I HWAIX ST $0.65132 / LT $0.40605; "
        "International Value I HWNIX ST $0.15175 / LT $1.77125). "
        "Record 12/3/2025; ex/pay 12/4/2025. "
        "Leftover paid year-end 2021–2024 for in-book Class I HWLIX / HWAIX / HWNIX. "
        "Class A / C / Z not attached. Printed dashes omitted. "
        "2025 page left as-is (additive leftover only)."
    )
    live_limitations = "Year-end book is PDF. Fixture transcribes public Class I rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_year_end_distributions",
                url=(
                    "https://www.hwcm.com/wp-content/uploads/2025/03/"
                    "HW-Funds-Dec-2025-Div-Cap-Gain-Distributions.pdf"
                ),
                fixture="2025_year_end_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="leftover_paid_year_end_parallel_s",
                url=(
                    "https://www.hwcm.com/wp-content/uploads/2024/11/"
                    "HW-Funds-Dec-2024-Div-Cap-Gain-distributions-FINAL.pdf"
                ),
                fixture="leftover_paid_year_end_parallel_s.html",
                live=False,
                role="history",
                large_aum_only=False,
            ),
        ]


class MarsicoSource(HtmlTableSource):
    slug = "marsico"
    display_name = "Marsico"
    aum_rank = 68
    priority = 68
    notes = (
        "Public 2025 paid distribution HTML: "
        "https://www.marsicofunds.com/investor-resources/content/distributions.fs "
        "Full Investor + Institutional book "
        "(e.g. Focus Investor MFOCX LT $4.9890; Growth Investor MGRIX LT $4.0748; "
        "Midcap Growth Focus Investor MXXIX ST $0.5894 / LT $6.0842). "
        "Record 12/18/2025; pay 12/19/2025. Published $0.0000 stored. "
        "MXXIX is Midcap Growth Focus (official). "
        "Official 5y parallel T leftover: Wayback snapshots of the same "
        "distributions page fill in-book leftovers. Investor MFOCX / MGRIX / "
        "MXXIX / MIOFX / MGLBX complete 2021–2025 (2021 Oct + Dec paid). "
        "Institutional MIFOX / MIGWX / MIDFX / MIIOX / MIGOX are 2022–2025 "
        "(2021 unpublished — not copied from Investor). Printed $0.0000 stored."
    )
    live_limitations = (
        "Live HTML is public but table layout may not parse. "
        "Fixture transcribes the official Investor + Institutional book. "
        "Leftover 2021–2024 is Wayback of the distributions page."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_year_end_distributions",
                url="https://www.marsicofunds.com/investor-resources/content/distributions.fs",
                fixture="2025_year_end_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="leftover_paid_year_end_parallel_t",
                url=(
                    "https://web.archive.org/web/20251118035530id_/"
                    "https://www.marsicofunds.com/investor-resources/content/"
                    "distributions.fs"
                ),
                fixture="leftover_paid_year_end_parallel_t.html",
                live=False,
                role="history",
                large_aum_only=False,
            ),
        ]


class OsterweisSource(HtmlTableSource):
    slug = "osterweis"
    display_name = "Osterweis"
    aum_rank = 69
    priority = 69
    notes = (
        "Tax center: https://www.osterweis.com/mutual_funds/tax_center "
        "Public 10/31/2025 estimate PDF: "
        "https://www.osterweis.com/files/Distribution-Estimates.pdf "
        "(e.g. Osterweis Fund OSTFX LT $1.10; Opportunity OSTGX LT $0.39; "
        "Growth & Income OSTVX LT $0.23). "
        "Equity record 12/12/2025; ex/pay 12/15/2025. "
        "Paid history: https://www.osterweis.com/files/OSTFX_Historical_Distributions.pdf "
        "Official 5y parallel U leftover: issuer historical-distribution PDFs "
        "fill leftover paid YE 2021–2025 (OSTFX / OSTGX / OSTVX). Official "
        "printed $0.00000 stored. OSTIX / OSTAX not in-book leftovers."
    )
    live_limitations = (
        "Estimate book is PDF. Weekly walk uses the tax-center hub + estimate PDF; "
        "empty/PDF-bytes pages are no-op success."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="tax_center_hub",
                url="https://www.osterweis.com/mutual_funds/tax_center",
                fixture="tax_center_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_estimated_distributions",
                url="https://www.osterweis.com/files/Distribution-Estimates.pdf",
                fixture="2025_estimated_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="leftover_paid_history_parallel_u",
                url="https://www.osterweis.com/files/OSTFX_Historical_Distributions.pdf",
                fixture="leftover_paid_history_parallel_u.html",
                live=False,
                role="history",
            ),
        ]


class DavisSource(HtmlTableSource):
    slug = "davis"
    display_name = "Davis Funds"
    aum_rank = 70
    priority = 70
    notes = (
        "Public paid distribution HTML (midyear + year-end + 2026 semi-annual): "
        "https://davisfunds.com/funds/distributions "
        "(NYVTX Class A midyear LT $2.10 on 6/25/2025; year-end LT $0.89 on "
        "12/12/2025; 2026 semi-annual ST $0.12 / LT $1.60 on 6/24/2026). "
        "Fixture transcribes those Class A rows; other share classes stay on the live page. "
        "Leftover paid year-end 2022–2024 for in-book Class A NYVTX / DGFAX / RPEAX. "
        "Class C / Y not attached. 2021 Wayback unpublished (CDX earliest 2023-09-26). "
        "DGFAX 2022 all-dash OI/ST/LT unmatched."
    )
    live_limitations = (
        "Live HTML is public but multi-fund / multi-class tables may not parse. "
        "Fixture fallback with Class A year-end rows."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_year_end_distributions",
                url="https://davisfunds.com/funds/distributions",
                fixture="2025_year_end_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="leftover_paid_year_end_parallel_s",
                url=(
                    "https://web.archive.org/web/20250121014455/"
                    "https://davisfunds.com/funds/distributions"
                ),
                fixture="leftover_paid_year_end_parallel_s.html",
                live=False,
                role="history",
                large_aum_only=False,
            ),
        ]
