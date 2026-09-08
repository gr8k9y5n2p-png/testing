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
        "(midyear / special / interim books would land here first). No public "
        "filled ICI Primary Layout. Family estimate PDFs (20251010 / 20241015 "
        "product-alert paths) are gated HTML login pages. Public product pages "
        "publish HTML paid YE history for ≥$1B Institutional classes: Special "
        "Mid Cap Value WFMIX "
        "https://www.allspringglobal.com/investments/equity/mutual-funds/special-mid-cap-value/ "
        "(2025 LT $4.26857; 2024 LT $2.93497; 2023 LT $1.7935; 2022 LT $3.13277) "
        "and Growth SGRNX "
        "https://www.allspringglobal.com/investments/equity/mutual-funds/growth/i/ "
        "(2025 LT $8.85612; 2024 LT $9.55498; 2023 LT $2.92658; 2022 LT $1.62055)."
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
            ),
            PageSpec(
                name="2024_paid_product_pages",
                url="https://www.allspringglobal.com/investments/equity/mutual-funds/special-mid-cap-value/",
                fixture="2024_paid_distributions.html",
                live=False,
                large_aum_only=True,
            ),
            PageSpec(
                name="2023_paid_product_pages",
                url="https://www.allspringglobal.com/investments/equity/mutual-funds/special-mid-cap-value/",
                fixture="2023_paid_distributions.html",
                live=False,
                large_aum_only=True,
            ),
            PageSpec(
                name="2022_paid_product_pages",
                url="https://www.allspringglobal.com/investments/equity/mutual-funds/special-mid-cap-value/",
                fixture="2022_paid_distributions.html",
                live=False,
                large_aum_only=True,
            ),
        ]


class JanusHendersonSource(HtmlTableSource):
    slug = "janus_henderson"
    display_name = "Janus Henderson"
    aum_rank = 22
    priority = 22
    notes = (
        "Advisor tax hub: "
        "https://www.janushenderson.com/en-us/advisor/annual-distributions-supplemental-tax-documents-mutual-funds/ "
        "hosts public estimate, final, and filled ICI Primary Layout PDFs on the "
        "rackcdn distribution-tax path. **ICI first** for 2021–2025 paid YE "
        "(column-safe 31-token layout; income / ST / LT at tokens 4 / 5 / 12; "
        "December rows only; Daily income lines skipped): "
        "Janus Henderson ICI Primary Layout 2021.pdf (JDCAX ST $0.253328 / LT $4.95363; "
        "Forty Fund is on ICI, not the 2021 FINAL PDF), "
        "Janus Henderson 2022 ICI Primary Layout.pdf (JDCAX LT $0.02107), "
        "Janus Henderson 2023 ICI Primary Layout.pdf (JDCAX LT $3.88875), "
        "Janus-Henderson-2024-ICI-Primary-Layout.pdf (JDCAX ST $0.19019347 / LT $5.46939), "
        "Janus Henderson 2025 ICI Primary Layout.pdf (JDCAX LT $6.96694). "
        "2025 final YE estimates (through 11/03/2025) remain as the estimate book "
        "(JDCAX LT $6.92). 2024 Preliminary Distribution Estimates 2024.pdf "
        "(JDCAX LT $5.42). 2023 Final Distribution Estimates 2023.pdf "
        "(JDCAX LT $3.87). 2021–2022 FINAL paid PDFs remain as companion books "
        "(JDBAX 2021 LT $1.50790)."
    )
    live_limitations = (
        "Year-end book is PDF. 2021–2025 ICI Primary Layout PDFs are the paid "
        "full-book fixtures. Estimate PDFs coexist (2023–2025). 2021–2022 finals "
        "are share-class transcriptions (live=False)."
    )

    def pages(self) -> list[PageSpec]:
        cdn = (
            "https://2deaa804a6dc693855a0-eba658c6bc03668a61900f643427d64d.ssl.cf1.rackcdn.com/"
            "Documents/product/distribution-tax"
        )
        return [
            PageSpec(
                name="ici_primary_2025",
                url=f"{cdn}/Janus%20Henderson%202025%20ICI%20Primary%20Layout.pdf",
                fixture="ici_primary_2025.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
            ),
            PageSpec(
                name="ici_primary_2024",
                url=f"{cdn}/Janus-Henderson-2024-ICI-Primary-Layout.pdf",
                fixture="ici_primary_2024.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
            ),
            PageSpec(
                name="ici_primary_2023",
                url=f"{cdn}/Janus%20Henderson%202023%20ICI%20Primary%20Layout.pdf",
                fixture="ici_primary_2023.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
            ),
            PageSpec(
                name="ici_primary_2022",
                url=f"{cdn}/Janus%20Henderson%202022%20ICI%20Primary%20Layout.pdf",
                fixture="ici_primary_2022.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
            ),
            PageSpec(
                name="ici_primary_2021",
                url=f"{cdn}/Janus%20Henderson%20ICI%20Primary%20Layout%202021.pdf",
                fixture="ici_primary_2021.csv",
                live=False,
                parser="ici",
                large_aum_only=False,
            ),
            PageSpec(
                name="2025_final_distribution_estimates",
                url=f"{cdn}/2025-Janus-Henderson-Final-Distribution-Estimates.pdf",
                fixture="2025_final_distribution_estimates.html",
                live=False,
            ),
            PageSpec(
                name="2024_distribution_estimates",
                url=(
                    f"{cdn}/Janus%20Henderson%20Preliminary%20Distribution%20Estimates%202024.pdf"
                ),
                fixture="2024_distribution_estimates.html",
                live=False,
                large_aum_only=True,
            ),
            PageSpec(
                name="2023_final_distribution_estimates",
                url=f"{cdn}/Janus%20Henderson%20Final%20Distribution%20Estimates%202023.pdf",
                fixture="2023_final_distribution_estimates.html",
                live=False,
                large_aum_only=True,
            ),
            PageSpec(
                name="2022_final_distributions",
                url=f"{cdn}/Janus%20Henderson%20Funds%20Final%20Distribution%2012.20.22.pdf",
                fixture="2022_final_distributions.html",
                live=False,
            ),
            PageSpec(
                name="2021_final_distributions",
                url=f"{cdn}/Janus%20Henderson%20Funds%20Final%20Distribution%2012.22.21.pdf",
                fixture="2021_final_distributions.html",
                live=False,
            ),
        ]


class AmericanCenturySource(HtmlTableSource):
    slug = "american_century"
    display_name = "American Century"
    aum_rank = 23
    priority = 23
    notes = (
        "Tax-center HTML hub "
        "https://www.americancentury.com/plan/tax-center/estimated-distributions/ "
        "is a JavaScript grid (verified 2026-09-07). No public filled ICI. "
        "2025 retail estimate PDF "
        "https://res.americancentury.com/docs/estimated-distributions-november-retail.pdf "
        "is the full share-class book (TWCGX LT $10.4978 / 15.30% of NAV). Official Growth product page "
        "https://www.americancentury.com/invest/funds/growth/twcgx/ publishes "
        "2025 paid Total $9.7631 (no ST/LT split — stored as total capital gains). "
        "2023 full retail estimate book recovered from Wayback "
        "https://web.archive.org/web/20240807220342/https://res.americancentury.com/docs/estimated-distributions-september-aci-retail.pdf "
        "(title 2023 Estimated Distributions as of October 31, 2023; TWCGX ST $0.0349 / LT $2.4201 / 5.58% of NAV). "
        "Daily bond income lines skipped. 2024 unversioned retail PDF is the 2025 book; "
        "2022/2021 sibling PDFs were not fetchable. Historical-distribution CSV is not public."
    )
    live_limitations = "Family HTML grid is JavaScript-rendered; the retail PDF is the parseable book."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_distributions",
                url="https://res.americancentury.com/docs/estimated-distributions-november-retail.pdf",
                fixture="2025_estimated_distributions.html",
                live=False,
            ),
            PageSpec(
                name="2023_estimated_distributions",
                url=(
                    "https://web.archive.org/web/20240807220342/"
                    "https://res.americancentury.com/docs/estimated-distributions-september-aci-retail.pdf"
                ),
                fixture="2023_estimated_distributions.html",
                live=False,
                large_aum_only=False,
            ),
            PageSpec(
                name="2025_paid_twcgx",
                url="https://www.americancentury.com/invest/funds/growth/twcgx/",
                fixture="2025_paid_distributions.html",
                live=False,
                large_aum_only=True,
            ),
        ]


class DodgeCoxSource(HtmlTableSource):
    slug = "dodge_cox"
    display_name = "Dodge & Cox"
    aum_rank = 24
    priority = 24
    notes = (
        "Tax center: https://www.dodgeandcox.com/institutional-investor/us/en/resources/tax-center.html "
        "No public filled ICI. Q1 2026 estimate PDF "
        "https://www.dodgeandcox.com/content/dam/dc/us/en/pdf/dc-us-estimated-distributions-1Q2026.pdf "
        "(DODGX LT $0.16; DODIX not listed). Paid December YE from Supplemental "
        "Tax Letters: 2025 "
        "https://www.dodgeandcox.com/content/dam/dc/us/en/pdf/guides/dc_us_supplemental_tax_letter.pdf "
        "(DODGX LT $1.1999; DODIX income $0.1347) and 2024 "
        ".../dc_us_supplemental_tax_letter_2024.pdf (DODGX LT $12.036). 2023–2021 letter "
        "PDF siblings 404; Dec YE 2021–2023 transcribed from the public product-page "
        "API https://api-v1.dodgeandcox.com/api/funds-distribution (DODIX Dec income "
        "$0.0570 / $0.1010 / $0.1290; DODGX Dec LT $3.3800 / $7.2500 / $3.9800). "
        "March/June/September rows omitted so one as_of is not summed."
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
            PageSpec(
                name="2024_supplemental_tax_letter",
                url="https://www.dodgeandcox.com/content/dam/dc/us/en/pdf/guides/dc_us_supplemental_tax_letter_2024.pdf",
                fixture="2024_supplemental_tax_letter.html",
                live=False,
                large_aum_only=True,
            ),
            PageSpec(
                name="2023_supplemental_tax_letter",
                url="https://api-v1.dodgeandcox.com/api/funds-distribution",
                fixture="2023_supplemental_tax_letter.html",
                live=False,
                large_aum_only=True,
            ),
            PageSpec(
                name="2022_supplemental_tax_letter",
                url="https://api-v1.dodgeandcox.com/api/funds-distribution",
                fixture="2022_supplemental_tax_letter.html",
                live=False,
                large_aum_only=True,
            ),
            PageSpec(
                name="2021_supplemental_tax_letter",
                url="https://api-v1.dodgeandcox.com/api/funds-distribution",
                fixture="2021_supplemental_tax_letter.html",
                live=False,
                large_aum_only=True,
            ),
        ]


class MfsSource(HtmlTableSource):
    slug = "mfs"
    display_name = "MFS Investment Management"
    aum_rank = 25
    priority = 25
    notes = (
        "Tax center: https://www.mfs.com/en-us/individual-investor/resources/service-support/tax-center.html "
        "No public filled ICI. 2025 estimate PDF "
        "https://www.mfs.com/content/dam/mfs-enterprise/mfscom/backlot/mfs_cg_fly.pdf "
        "is the full % of average NAV book (175 published share-class / "
        "all-classes rows; MIGHX LT 8%–9%; published 0% stored). Tickers only "
        "MIGHX / MITTX — the PDF has no ticker column. Paid YE / midyear from "
        "product pages MIGHX / MITTX (2025 YE MIGHX LT $4.20618; 2026 midyear "
        "LT $0.54043). 2024 mfs_cg_fly_2024.pdf 404. Earlier years are behind "
        "a download control, not static HTML — skipped, not invented."
    )
    live_limitations = "Estimates are PDF percent-of-NAV ranges. Fixture transcribes public rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_capital_gain_estimates",
                url="https://www.mfs.com/content/dam/mfs-enterprise/mfscom/backlot/mfs_cg_fly.pdf",
                fixture="2025_capital_gain_estimates.html",
                live=False,
            ),
            PageSpec(
                name="2025_paid_year_end",
                url=(
                    "https://www.mfs.com/en-us/individual-investor/product-strategies/"
                    "mutual-funds/MIGHX-massachusetts-investors-growth-stock-fund.html"
                ),
                fixture="2025_paid_year_end.html",
                live=False,
                large_aum_only=True,
            ),
            PageSpec(
                name="2026_midyear_paid",
                url=(
                    "https://www.mfs.com/en-us/individual-investor/product-strategies/"
                    "mutual-funds/MIGHX-massachusetts-investors-growth-stock-fund.html"
                ),
                fixture="2026_midyear_paid.html",
                live=False,
                large_aum_only=True,
            ),
        ]


class LordAbbettSource(HtmlTableSource):
    slug = "lord_abbett"
    display_name = "Lord Abbett"
    aum_rank = 26
    priority = 26
    notes = (
        "Capital-gains hub "
        "https://www.lordabbett.com/en-us/financial-advisor/resources/tax-center/capital-gains-distributions.html "
        "is a JavaScript shell. No public filled ICI. The public 2025 document is "
        "a no-pay list: "
        "https://www.lordabbett.com/content/dam/lordabbett-captivate/documents/TaxCenter/UnitedStates/Funds-with-Losses.pdf "
        "(Bond Debenture, Developing Growth, Total Return 'not expected to pay "
        "2025 capital gain distributions'). Fixture stores those as $0.00 estimates. "
        "2024 Funds-with-Losses sibling 404. No public paying-fund ST/LT $/share "
        "grid — skipped, not invented."
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
        "No public filled ICI. 2025 estimate PDF Final_GEN-5796-1025.pdf "
        "is the full paying-fund book (AGRFX LT $16.36; Class A tickers only "
        "where previously identified). The unversioned FINAL_GEN-5796.pdf path now serves "
        "2025; 2024 was overwritten (not invented). 2023 book GEN–5796–1023 is "
        "still in the public Wayback snapshot of that path "
        "(AGRFX LT $6.95; APGAX LT $1.50)."
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
            ),
            PageSpec(
                name="2023_estimated_capital_gains",
                url=(
                    "https://web.archive.org/web/20241115000000/"
                    "https://www.alliancebernstein.com/content/dam/alliancebernstein/"
                    "us-retail/us-retail-pdfs/tax-center/FINAL_GEN-5796.pdf"
                ),
                fixture="2023_estimated_capital_gains.html",
                live=False,
                large_aum_only=True,
            ),
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
        "ICI Primary/Secondary tax-info PDFs are listed on services.federatedhermes.com "
        "token URLs (not a stable public download; some books are monthly muni "
        "lines). Public Section 19(a) notices publish per-share amounts, e.g. "
        "Enhanced Income ETF (PAYR) "
        "https://www.federatedhermes.com/siteassets/documents/regulatory/19a-notices/g85307-06.pdf "
        "(12/31/2025 income $0.184310 / ST $0.010122 / LT $0.015178). Kaufmann "
        "product pages do not expose a scrapeable ST/LT history grid."
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
        "No public filled ICI. June 2026 estimate "
        "https://www.virtus.com/assets/files/abi/cap_gains_estimate_6-26_8569.pdf "
        "is the full listed-fund PDF (STVTX ST $0.2779 / LT $0.1767). 2025 paid calendar-year book "
        "https://www.virtus.com/assets/files/8ua/2025-mfs_distributions_calyr_detail.pdf "
        "(STVTX Dec ST $0.664597 / LT $0.427834). 2024 Section 19(a) "
        "https://www.virtus.com/assets/files/8o4/section-19a-notice--retail-oef-template-12.18.2024.pdf "
        "(STVTX income $0.141942 / total CG $1.907616 — notice is not ST/LT split)."
    )
    live_limitations = "Estimate book is PDF. Fixture transcribes the public June 2026 table."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2026_june_capital_gain_estimates",
                url="https://www.virtus.com/assets/files/abi/cap_gains_estimate_6-26_8569.pdf",
                fixture="2026_june_capital_gain_estimates.html",
                live=False,
            ),
            PageSpec(
                name="2025_paid_year_end",
                url="https://www.virtus.com/assets/files/8ua/2025-mfs_distributions_calyr_detail.pdf",
                fixture="2025_paid_year_end.html",
                live=False,
                large_aum_only=True,
            ),
            PageSpec(
                name="2024_section_19a",
                url=(
                    "https://www.virtus.com/assets/files/8o4/"
                    "section-19a-notice--retail-oef-template-12.18.2024.pdf"
                ),
                fixture="2024_section_19a.html",
                live=False,
                large_aum_only=True,
            ),
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
        "(EOI March 2025 $0.1338, 100% LT). No public filled ICI. 2024 sibling "
        "combined19bpressreleasemarch2024.pdf / combined_19b_press_release_022924.pdf "
        "returned 403. Open-end family estimate HTML was not found on 2026-09-07."
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
