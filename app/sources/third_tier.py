from __future__ import annotations

from app.sources.html_source import HtmlTableSource, PageSpec


class AllspringSource(HtmlTableSource):
    slug = "allspring"
    display_name = "Allspring"
    aum_rank = 21
    priority = 21
    notes = (
        "Weekly watch: product-alerts hub "
        "https://www.allspringglobal.com/resources/product-alerts/ "
        "(midyear / special / interim books would land here first). As of "
        "2026-09-07 there is no open-end midyear capital-gains table — the latest "
        "family book is Allspring Funds 2025 Capital Gains Estimates (10/10/2025) "
        "https://www.allspringglobal.com/globalassets/assets/public/pdf/product-alerts/20251010-productalert.pdf "
        "(image/gated; append ?view=1). Public product pages publish HTML paid "
        "year-end history, e.g. Special Mid Cap Value "
        "https://www.allspringglobal.com/investments/equity/mutual-funds/special-mid-cap-value/ "
        "(2025-12-15 ST $0.34918 / LT $4.26857) and Growth "
        "https://www.allspringglobal.com/investments/equity/mutual-funds/growth/i/ "
        "(2025-12-15 ST $0.01467 / LT $8.85612). Fixture transcribes those paid rows."
    )
    live_limitations = (
        "Family estimate PDF is gated/image-based. Product-page tables put the date "
        "in the first column, so static parse may return 0 rows. Fixture fallback."
    )

    def source_urls(self) -> list[str]:
        return [
            "https://www.allspringglobal.com/resources/product-alerts/",
            *super().source_urls(),
        ]

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_paid_product_pages",
                url="https://www.allspringglobal.com/investments/equity/mutual-funds/special-mid-cap-value/",
                fixture="2025_paid_distributions.html",
                live=True,
            )
        ]


class JanusHendersonSource(HtmlTableSource):
    slug = "janus_henderson"
    display_name = "Janus Henderson"
    aum_rank = 22
    priority = 22
    notes = (
        "Advisor tax hub: "
        "https://www.janushenderson.com/en-us/advisor/annual-distributions-supplemental-tax-documents-mutual-funds/ "
        "hosts public estimate and final PDFs. 2025 final year-end estimates "
        "(income and gains through 11/03/2025): "
        "https://2deaa804a6dc693855a0-eba658c6bc03668a61900f643427d64d.ssl.cf1.rackcdn.com/"
        "Documents/product/distribution-tax/2025-Janus-Henderson-Final-Distribution-Estimates.pdf "
        "(e.g. Forty Fund JDCAX LT $6.92 / 10.77% of NAV; Enterprise JDMAX ST $0.27 / LT $9.88)."
    )
    live_limitations = "Year-end book is PDF. Fixture transcribes public A-share estimate rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_final_distribution_estimates",
                url=(
                    "https://2deaa804a6dc693855a0-eba658c6bc03668a61900f643427d64d.ssl.cf1.rackcdn.com/"
                    "Documents/product/distribution-tax/2025-Janus-Henderson-Final-Distribution-Estimates.pdf"
                ),
                fixture="2025_final_distribution_estimates.html",
                live=False,
            )
        ]


class AmericanCenturySource(HtmlTableSource):
    slug = "american_century"
    display_name = "American Century"
    aum_rank = 23
    priority = 23
    notes = (
        "Tax-center HTML hub "
        "https://www.americancentury.com/plan/tax-center/estimated-distributions/ "
        "is a JavaScript grid (verified 2026-09-07). The same 10/31/2025 book is a "
        "public PDF: https://res.americancentury.com/docs/estimated-distributions-november-retail.pdf "
        "(e.g. Growth Investor TWCGX LT $10.4978 / 15.30% of NAV; Equity Growth "
        "Investor BEQGX ST $0.2159 / LT $3.6325)."
    )
    live_limitations = "Family HTML grid is JavaScript-rendered; the retail PDF is the parseable book."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_distributions",
                url="https://res.americancentury.com/docs/estimated-distributions-november-retail.pdf",
                fixture="2025_estimated_distributions.html",
                live=False,
            )
        ]


class DodgeCoxSource(HtmlTableSource):
    slug = "dodge_cox"
    display_name = "Dodge & Cox"
    aum_rank = 24
    priority = 24
    notes = (
        "Tax center: https://www.dodgeandcox.com/institutional-investor/us/en/resources/tax-center.html "
        "Current public estimate PDF (Q1 2026, as of 2/23/2026): "
        "https://www.dodgeandcox.com/content/dam/dc/us/en/pdf/dc-us-estimated-distributions-1Q2026.pdf "
        "(Balanced DODBX / Stock DODGX LT $0.09 / $0.16; Income DODIX is not listed — "
        "no estimated Q1 2026 capital gain). Paid 2025 per-share amounts "
        "are in the Supplemental Tax Letter "
        "https://www.dodgeandcox.com/content/dam/dc/us/en/pdf/guides/dc_us_supplemental_tax_letter.pdf "
        "(Income DODIX ordinary income only, e.g. Dec 2025 $0.1347; no 2025 ST/LT)."
    )
    live_limitations = "Estimates and the tax letter are PDF. Fixtures transcribe those public tables."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="1q2026_estimated_capital_gains",
                url="https://www.dodgeandcox.com/content/dam/dc/us/en/pdf/dc-us-estimated-distributions-1Q2026.pdf",
                fixture="1q2026_estimated_capital_gains.html",
                live=False,
            ),
            PageSpec(
                name="2025_supplemental_tax_letter",
                url="https://www.dodgeandcox.com/content/dam/dc/us/en/pdf/guides/dc_us_supplemental_tax_letter.pdf",
                fixture="2025_supplemental_tax_letter.html",
                live=False,
            ),
        ]


class MfsSource(HtmlTableSource):
    slug = "mfs"
    display_name = "MFS Investment Management"
    aum_rank = 25
    priority = 25
    notes = (
        "Tax center: https://www.mfs.com/en-us/individual-investor/resources/service-support/tax-center.html "
        "Public 2025 capital-gain estimate PDF (as of 9/30/2025, published 11/7/2025): "
        "https://www.mfs.com/content/dam/mfs-enterprise/mfscom/backlot/mfs_cg_fly.pdf "
        "(e.g. Massachusetts Investors Growth Stock Class A LT 8%–9% of average NAV; "
        "Massachusetts Investors Trust all classes LT 10%–12%)."
    )
    live_limitations = "Estimates are PDF percent-of-NAV ranges. Fixture transcribes public rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_capital_gain_estimates",
                url="https://www.mfs.com/content/dam/mfs-enterprise/mfscom/backlot/mfs_cg_fly.pdf",
                fixture="2025_capital_gain_estimates.html",
                live=False,
            )
        ]


class LordAbbettSource(HtmlTableSource):
    slug = "lord_abbett"
    display_name = "Lord Abbett"
    aum_rank = 26
    priority = 26
    notes = (
        "Capital-gains hub "
        "https://www.lordabbett.com/en-us/financial-advisor/resources/tax-center/capital-gains-distributions.html "
        "is a JavaScript shell. The public 2025 estimate document is a no-pay list: "
        "https://www.lordabbett.com/content/dam/lordabbett-captivate/documents/TaxCenter/UnitedStates/Funds-with-Losses.pdf "
        "(Bond Debenture, Developing Growth, and many others 'not expected to pay "
        "2025 capital gain distributions'). Fixture stores those as $0.00 estimates. "
        "Tickers are the public Class A identifiers; the PDF is fund-level."
    )
    live_limitations = (
        "HTML hub has no table. The public PDF lists funds expected to pay $0, "
        "not a per-share paying-fund grid."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_funds_not_expected_to_pay",
                url=(
                    "https://www.lordabbett.com/content/dam/lordabbett-captivate/documents/"
                    "TaxCenter/UnitedStates/Funds-with-Losses.pdf"
                ),
                fixture="2025_funds_not_expected_to_pay.html",
                live=False,
            )
        ]


class AllianceBernsteinSource(HtmlTableSource):
    slug = "ab"
    display_name = "AllianceBernstein"
    aum_rank = 27
    priority = 27
    notes = (
        "Tax center: https://www.alliancebernstein.com/us/en-us/investments/resources/tax-center.html "
        "Public 10/31/2025 estimate PDF: "
        "https://www.alliancebernstein.com/content/dam/alliancebernstein/us-retail/us-retail-pdfs/tax-center/Final_GEN-5796-1025.pdf "
        "(e.g. AB Growth Fund ST $0.73 / LT $16.36 / 13.68% of Class A NAV; "
        "AB Large Cap Growth ST $0.48 / LT $10.37 / 9.84%)."
    )
    live_limitations = "Estimates are PDF. Fixture transcribes public Class A rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_capital_gains",
                url=(
                    "https://www.alliancebernstein.com/content/dam/alliancebernstein/"
                    "us-retail/us-retail-pdfs/tax-center/Final_GEN-5796-1025.pdf"
                ),
                fixture="2025_estimated_capital_gains.html",
                live=False,
            )
        ]


class FederatedHermesSource(HtmlTableSource):
    slug = "federated_hermes"
    display_name = "Federated Hermes"
    aum_rank = 28
    priority = 28
    notes = (
        "Tax-center HTML grids "
        "https://www.federatedhermes.com/us/resources/resource-centers/tax-center/capital-gains/preliminary.do "
        "and .../final.do are JavaScript (API-backed; verified 2026-09-07). "
        "Public Section 19(a) notices publish per-share estimates, e.g. Enhanced "
        "Income ETF (PAYR) "
        "https://www.federatedhermes.com/siteassets/documents/regulatory/19a-notices/g85307-06.pdf "
        "(12/31/2025 income $0.184310 / ST $0.010122 / LT $0.015178)."
    )
    live_limitations = "Family tax-center tables are JavaScript. Fixture transcribes a public 19(a) notice."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_payr_section_19a",
                url="https://www.federatedhermes.com/siteassets/documents/regulatory/19a-notices/g85307-06.pdf",
                fixture="2025_section_19a_sample.html",
                live=False,
            )
        ]


class VirtusSource(HtmlTableSource):
    slug = "virtus"
    display_name = "Virtus"
    aum_rank = 29
    priority = 29
    notes = (
        "Tax center: https://www.virtus.com/investor-resources/mutual-fund-account-information-resources/tax-center "
        "Public June 2026 capital-gains estimate PDF (as of 5/29/2026): "
        "https://www.virtus.com/assets/files/abi/cap_gains_estimate_6-26_8569.pdf "
        "(e.g. Ceredex Large-Cap Value Equity ST $0.2779 / LT $0.1767; "
        "Zevenbergen Innovative Growth Stock LT $2.4917 / 3.74% of NAV). "
        "2025 paid calendar-year detail: "
        "https://www.virtus.com/assets/files/8ua/2025-mfs_distributions_calyr_detail.pdf."
    )
    live_limitations = "Estimate book is PDF. Fixture transcribes the public June 2026 table."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2026_june_capital_gain_estimates",
                url="https://www.virtus.com/assets/files/abi/cap_gains_estimate_6-26_8569.pdf",
                fixture="2026_june_capital_gain_estimates.html",
                live=False,
            )
        ]


class EatonVanceSource(HtmlTableSource):
    slug = "eaton_vance"
    display_name = "Eaton Vance"
    aum_rank = 30
    priority = 30
    notes = (
        "Morgan Stanley already covers MSIM open-end/ETF year-end PDFs. Eaton Vance "
        "still publishes distinct public CEF Section 19(b) estimated-source notices, "
        "e.g. https://www.eatonvance.com/content/dam/im/assets/publication/thought-leadership/"
        "press-release/combined19bpressreleasemarch2025.pdf "
        "(Enhanced Equity Income Fund EOI March 2025 distribution $0.1338, 100% LT). "
        "Business Wire reprints the same monthly tables. Open-end family estimate "
        "HTML was not found on 2026-09-07."
    )
    live_limitations = (
        "Open-end estimates are not a public HTML grid. Fixture transcribes a public CEF 19(b) notice."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_cef_section_19b",
                url=(
                    "https://www.eatonvance.com/content/dam/im/assets/publication/"
                    "thought-leadership/press-release/combined19bpressreleasemarch2025.pdf"
                ),
                fixture="2025_cef_section_19b_sample.html",
                live=False,
            )
        ]
