from __future__ import annotations

from app.sources.html_source import HtmlTableSource, PageSpec


class UbsSource(HtmlTableSource):
    slug = "ubs"
    display_name = "UBS Asset Management"
    aum_rank = 11
    priority = 11
    notes = (
        "US mutual-fund estimated capital gains are a public PDF linked from "
        "https://www.ubs.com/us/en/assetmanagement/funds/products/mutual-fund "
        "(October 2025 ranges, e.g. U.S. Allocation LT $2.88–$4.05). Paid per-share "
        "amounts also appear on the public price page "
        "https://www.ubs.com/us/en/assetmanagement/funds/mutual-fund-price.html "
        "(PWTAX ST $0.0521 / LT $4.0999 as of 12/17/2025, verified 2026-09-07). "
        "The estimate PDF is behind rotating AEM JCR URLs and is often bot-blocked; "
        "fixture mode transcribes those public figures."
    )
    live_limitations = (
        "Estimate PDF is AEM/JCR and often 403 from automated clients. "
        "Price-page HTML tables start with share class, not fund name, so static "
        "parse may return 0 rows. Fixture / partner ingest is the supported path."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="october_estimates",
                url="https://www.ubs.com/us/en/assetmanagement/funds/products/mutual-fund",
                fixture="estimated_capital_gains.html",
                live=False,
            ),
            PageSpec(
                name="paid_price_page",
                url="https://www.ubs.com/us/en/assetmanagement/funds/mutual-fund-price.html",
                fixture="paid_year_end.html",
                live=True,
            ),
        ]


class FranklinTempletonSource(HtmlTableSource):
    slug = "franklin_templeton"
    display_name = "Franklin Templeton"
    aum_rank = 12
    priority = 12
    notes = (
        "Tax-center hub: https://www.franklintempleton.com/tools-and-resources/tax-center "
        "(December capital-gains estimates, late October / late November). "
        "Family estimate grid https://www.franklintempleton.com/tools-and-resources/capital-gains-distribution "
        "is a JavaScript SPA (verified 2026-09-07). Public Section 19(a) notices "
        "exist for closed-end funds, e.g. Franklin Universal Trust (FT) "
        "https://www.franklintempleton.com/forms-literature/download/ft-section-19-notice-12-31-2025. "
        "Fixture transcribes that 19(a) table."
    )
    live_limitations = (
        "Open-end December estimate tool is JavaScript-rendered. "
        "Use fixture mode or POST /ingest/distributions for advisor-exported grids."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="ft_section_19a",
                url="https://www.franklintempleton.com/forms-literature/download/ft-section-19-notice-12-31-2025",
                fixture="capital_gains_sample.html",
                live=False,
            )
        ]


class BnyMellonSource(HtmlTableSource):
    slug = "bny_mellon"
    display_name = "BNY Mellon / Dreyfus"
    aum_rank = 13
    priority = 13
    notes = (
        "Public 2025 estimate PDF "
        "https://www.bny.com/assets/investments/im/documents/manual/tax-forms/2025-Estimated-capital-gains.pdf "
        "(as of 10/31/2025; e.g. Appreciation Fund LT $6.29 / 15.0% of NAV). "
        "Tax-center hubs: "
        "https://www.bny.com/investments/us/en/individual/resources/tax-center.html "
        "and https://www.dreyfus.com/resources/tax-center.html (no HTML grid)."
    )
    live_limitations = "Estimates are PDF, not an HTML grid. Fixture transcribes the public PDF."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_capital_gains",
                url="https://www.bny.com/assets/investments/im/documents/manual/tax-forms/2025-Estimated-capital-gains.pdf",
                fixture="2025_estimated_capital_gains.html",
                live=False,
            )
        ]


class NuveenSource(HtmlTableSource):
    slug = "nuveen"
    display_name = "Nuveen / TIAA"
    aum_rank = 14
    priority = 14
    notes = (
        "Estimated 2025 annual taxable distributions (as of 10/31/2025) live in "
        "Nuveen’s document viewer "
        "https://documents.nuveen.com/Documents/Nuveen/Default.aspx?uniqueId=3c3be13d-d800-48e2-a537-c251162ab9f4 "
        "(e.g. Core Equity TIIRX LT $1.97 / 6.49% of NAV). Hub: "
        "https://www.nuveen.com/en-us/investments/tax-information-forms-and-applications"
    )
    live_limitations = "Estimate book is a PDF viewer, not scrapeable HTML. Fixture transcribes public rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_estimated_taxable_distributions",
                url="https://documents.nuveen.com/Documents/Nuveen/Default.aspx?uniqueId=3c3be13d-d800-48e2-a537-c251162ab9f4",
                fixture="2025_estimated_taxable_distributions.html",
                live=False,
            )
        ]


class NorthernTrustSource(HtmlTableSource):
    slug = "northern_trust"
    display_name = "Northern Trust"
    aum_rank = 15
    priority = 15
    notes = (
        "Public 2025 capital-gain PDF "
        "https://ntam.northerntrust.com/content/dam/ntam/us/en/documents/account-resources/tax-center/all-investor/estimated-capital-gains-2025.pdf "
        "(paid 12/18/2025; e.g. Stock Index NOSIX ST $0.041654 / LT $1.182288). "
        "Tax center: https://www.ntam.northerntrust.com/united-states/all-investor/account-resources/tax-center"
    )
    live_limitations = "Year-end figures are PDF. Fixture transcribes the public Northern Funds table."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_capital_gain_distributions",
                url="https://ntam.northerntrust.com/content/dam/ntam/us/en/documents/account-resources/tax-center/all-investor/estimated-capital-gains-2025.pdf",
                fixture="2025_capital_gain_distributions.html",
                live=False,
            )
        ]


class MorganStanleySource(HtmlTableSource):
    slug = "morgan_stanley"
    display_name = "Morgan Stanley Investment Management"
    aum_rank = 16
    priority = 16
    notes = (
        "Public 2025 ETF year-end PDF "
        "https://www.morganstanley.com/im/publication/forms/tax/2025_etf_year_end_distributions.pdf "
        "(ex/record 12/23/2025, payable 12/30/2025; e.g. CVLC income $0.283927, 0% capital gains). "
        "Open-end estimate PDFs follow the same /im/publication/forms/tax/ path "
        "(2024_estimated_year_end_distributions.pdf is public; 2025 open-end PDF was "
        "Akamai-blocked from this environment on 2026-09-07). Tax center: msim.com/taxcenter."
    )
    live_limitations = (
        "Year-end PDFs are often Akamai-walled to automated clients. "
        "Fixture transcribes the public 2025 ETF table."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_etf_year_end",
                url="https://www.morganstanley.com/im/publication/forms/tax/2025_etf_year_end_distributions.pdf",
                fixture="2025_etf_year_end_sample.html",
                live=False,
            )
        ]


class SchwabSource(HtmlTableSource):
    slug = "schwab"
    display_name = "Charles Schwab Investment Management"
    aum_rank = 17
    priority = 17
    notes = (
        "Family annual page "
        "https://www.schwabassetmanagement.com/resource/schwab-funds-actual-annual-distributions-2025 "
        "is a JS SPA (verified 2026-09-07). Per-fund product pages publish HTML "
        "distribution tables, e.g. https://www.schwabassetmanagement.com/products/swlvx "
        "(SWLVX 12/12/2025 income $0.2940 / ST $0.0299 / LT $0.0049)."
    )
    live_limitations = (
        "Family annual grid is JavaScript-rendered. Product pages mix performance "
        "tables with distributions; fixture transcribes the public 2025 annual rows."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_annual_distributions",
                url="https://www.schwabassetmanagement.com/resource/schwab-funds-actual-annual-distributions-2025",
                fixture="2025_annual_distributions.html",
                live=True,
            )
        ]


class DimensionalSource(HtmlTableSource):
    slug = "dimensional"
    display_name = "Dimensional Fund Advisors"
    aum_rank = 18
    priority = 18
    notes = (
        "Public 2025 capital-gain distribution PDF "
        "https://www.dimensional.com/chmedia/440098/source/download/2025-capital-gain-distribution-estimates.pdf "
        "(e.g. DISVX LT $1.060 / 3.42% of NAV; DFELX ST $0.752 / LT $1.234). "
        "Tax center: https://www.dimensional.com/us-en/tax"
    )
    live_limitations = "Year-end book is PDF. Fixture transcribes public paid/estimate rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_capital_gain_distributions",
                url="https://www.dimensional.com/chmedia/440098/source/download/2025-capital-gain-distribution-estimates.pdf",
                fixture="2025_capital_gain_distributions.html",
                live=False,
            )
        ]


class ColumbiaThreadneedleSource(HtmlTableSource):
    slug = "columbia_threadneedle"
    display_name = "Columbia Threadneedle"
    aum_rank = 19
    priority = 19
    notes = (
        "Public 2025 mid-year estimate PDF "
        "https://www.columbiathreadneedleus.com/binaries/content/assets/cti/public/2025-mid-year-cap-gain-estimates-all-funds.pdf "
        "(e.g. IEVAX 0.86–1.25% of 5/31 NAV; ELGAX 18.62–21.95%). Investor hub: "
        "https://www.columbiathreadneedleus.com/investor. Year-end 2025 book was not "
        "a public HTML grid on 2026-09-07 (2024 finals remain as a separate PDF)."
    )
    live_limitations = "Estimates are PDF. Fixture transcribes the public mid-year ranges."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_midyear_estimates",
                url="https://www.columbiathreadneedleus.com/binaries/content/assets/cti/public/2025-mid-year-cap-gain-estimates-all-funds.pdf",
                fixture="2025_midyear_estimates.html",
                live=False,
            )
        ]


class AmundiSource(HtmlTableSource):
    slug = "amundi"
    display_name = "Amundi US / Pioneer"
    aum_rank = 20
    priority = 20
    notes = (
        "US Pioneer retail funds transferred to Victory Capital (April 2025). "
        "Public 10/15/2025 estimate PDF remains on the Pioneer/Amundi tax center: "
        "https://pioneerinvestments.com/content/dam/pioneer/en/documents/resources/tax-center/2025/10152025-mutual-funds-2025-capital-gain-estimates.pdf "
        "(e.g. Victory Pioneer Fund PIODX ST $0.53 / LT $3.73 / 9.09% of NAV). "
        "Hubs: https://www.amundi.com/usinvestors/Resources/Tax-Center and "
        "https://pioneerinvestments.com/resources/tax-center. Final 2025 PDF: "
        "2025-final-ord-inc-cap-gain-distributions.pdf on the same path."
    )
    live_limitations = "US estimates are PDF on the Pioneer/Victory tax center. Fixture transcribes that table."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_capital_gain_estimates",
                url=(
                    "https://pioneerinvestments.com/content/dam/pioneer/en/documents/"
                    "resources/tax-center/2025/10152025-mutual-funds-2025-capital-gain-estimates.pdf"
                ),
                fixture="2025_capital_gain_estimates.html",
                live=False,
            )
        ]
