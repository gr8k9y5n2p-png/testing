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
        "fixture mode transcribes those public figures. No public filled ICI file. "
        "2023–2024 paid/estimate archives were not fetchable (403 / rotating JCR) "
        "— skipped, not invented."
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
        "https://www.franklintempleton.com/forms-literature/download/ft-section-19-notice-12-31-2025 "
        "and the 2024 sibling `.../ft-section-19-notice-12-31-2024` "
        "(Dec 2024 income $0.0387 / RoC $0.0038). ICI reports hub is a JS SPA; "
        "no public filled Primary Layout download. ≥$1B open-end (FKINX) amounts "
        "were not on a scrapeable PDF/HTML grid — skipped, not invented."
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
            ),
            PageSpec(
                name="ft_section_19a_2024",
                url="https://www.franklintempleton.com/forms-literature/download/ft-section-19-notice-12-31-2024",
                fixture="2024_section_19a.html",
                live=False,
            ),
        ]


class BnyMellonSource(HtmlTableSource):
    slug = "bny_mellon"
    display_name = "BNY Mellon / Dreyfus"
    aum_rank = 13
    priority = 13
    notes = (
        "Public 2025 estimate PDF is the full paying-fund book "
        "https://www.bny.com/assets/investments/im/documents/manual/tax-forms/2025-Estimated-capital-gains.pdf "
        "(as of 10/31/2025; e.g. Appreciation Fund LT $6.29 / 15.0% of NAV) plus the "
        "ETF estimate book "
        "https://www.bny.com/content/dam/im/documents/manual/tax-forms/2025-exchange-traded-funds-estimated-capital-gains.pdf "
        "(12 ETFs; published $0.00 total CG stored). "
        "Paid YE for DGAGX (≥$1B Investor class) from the public product page "
        "https://www.bny.com/investments/us/en/intermediary/products/lt/fund/"
        "bny-mellon-appreciation-fund-inc.html "
        "(2025 LT $6.4552; 2024 LT $5.6247; 2023 LT $1.9798; 2022 LT $2.7106). "
        "No public filled ICI file. 2024 family estimate PDF URL was empty."
    )
    live_limitations = "Estimates are PDF, not an HTML grid. Fixture transcribes the public PDF / product table."

    def pages(self) -> list[PageSpec]:
        product = (
            "https://www.bny.com/investments/us/en/intermediary/products/lt/fund/"
            "bny-mellon-appreciation-fund-inc.html"
        )
        return [
            PageSpec(
                name="2025_estimated_capital_gains",
                url="https://www.bny.com/assets/investments/im/documents/manual/tax-forms/2025-Estimated-capital-gains.pdf",
                fixture="2025_estimated_capital_gains.html",
                live=False,
            ),
            PageSpec(
                name="2025_etf_estimated_capital_gains",
                url="https://www.bny.com/content/dam/im/documents/manual/tax-forms/2025-exchange-traded-funds-estimated-capital-gains.pdf",
                fixture="2025_etf_estimated_capital_gains.html",
                live=False,
            ),
            PageSpec(
                name="2025_paid_year_end",
                url=product,
                fixture="2025_paid_year_end.html",
                live=False,
            ),
            PageSpec(
                name="2024_paid_year_end",
                url=product,
                fixture="2024_paid_year_end.html",
                live=False,
                large_aum_only=True,
            ),
            PageSpec(
                name="2023_paid_year_end",
                url=product,
                fixture="2023_paid_year_end.html",
                live=False,
                large_aum_only=True,
            ),
            PageSpec(
                name="2022_paid_year_end",
                url=product,
                fixture="2022_paid_year_end.html",
                live=False,
                large_aum_only=True,
            ),
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
        "https://www.nuveen.com/en-us/investments/tax-information-forms-and-applications. "
        "The document-viewer URL returns a JavaScript shell (no fetchable PDF in this "
        "environment) — remaining funds not transcribed. "
        "No public filled ICI file. 2024 posted files are tax-character letters "
        "(QDI / DRD / US-gov %), not ST/LT $/share — skipped, not invented."
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
        "Filled ICI Primary Reports are public (2022–2025) on the tax center "
        "(e.g. .../nf-ici-primary-reports-2025.pdf, .../nf-ici-primary-2024.pdf). "
        "The ICI first amount is Total Distribution (income+CG); CG-paying "
        "tickers are not ingested from ICI (would double-count). December ICI "
        "totals are stored as ordinary income only for equity funds whose "
        "companion CG PDF lists ST/LT as em-dashes. Daily/monthly FI lines "
        "omitted. 2025 .../estimated-capital-gains-2025.pdf is the full equity "
        "CG book (NOSIX ST $0.041654 / LT $1.182288; NOMIX ST $0.136686 / "
        "LT $1.011150; NSGRX/NSCKX ST $0.189098 / LT $3.454742). "
        "2024 .../estimated-capital-gains-2024.pdf is the full equity CG book "
        "(NOSIX ST $0.088060 / LT $0.699110; NSGRX/NSCKX LT $4.052773; "
        "NOSGX LT $7.263053). "
        "2023 .../capital-gains-2023.pdf is the full equity CG book "
        "(NOSIX LT $1.697952; NOLCX LT $1.865371; NSGRX/NSCKX LT $1.216779). "
        "2022 .../capital-gains-2022.pdf is the full equity CG book "
        "(NOSIX LT $1.243605; NENGX LT $1.892337; NOMIX LT $1.629689). "
        "2021 .../capital-gains-2021.pdf (NOSIX ST $0.096491 / LT $0.985777; "
        "full equity CG book; FI daily/monthly omitted). "
        "Hub: https://ntam.northerntrust.com/united-states/all-investor/account-resources/tax-center"
    )
    live_limitations = "Year-end figures are PDF. Fixture transcribes the public Northern Funds table."

    def pages(self) -> list[PageSpec]:
        tax = "https://ntam.northerntrust.com/content/dam"
        return [
            PageSpec(
                name="2025_capital_gain_distributions",
                url=f"{tax}/ntam/us/en/documents/account-resources/tax-center/all-investor/estimated-capital-gains-2025.pdf",
                fixture="2025_capital_gain_distributions.html",
                live=False,
            ),
            PageSpec(
                name="2025_ici_december_income",
                url=f"{tax}/ntam/us/en/documents/account-resources/tax-center/all-investor/nf-ici-primary-reports-2025.pdf",
                fixture="2025_ici_december_income.html",
                live=False,
            ),
            PageSpec(
                name="2024_capital_gain_distributions",
                url=f"{tax}/northerntrust/investment-management/global/en/documents/account-resources/tax-center/estimated-capital-gains-2024.pdf",
                fixture="2024_capital_gain_distributions.html",
                live=False,
            ),
            PageSpec(
                name="2023_capital_gain_distributions",
                url=f"{tax}/northerntrust/investment-management/global/en/documents/account-resources/tax-center/capital-gains-2023.pdf",
                fixture="2023_capital_gain_distributions.html",
                live=False,
            ),
            PageSpec(
                name="2022_capital_gain_distributions",
                url=f"{tax}/northerntrust/investment-management/global/en/documents/account-resources/tax-center/capital-gains-2022.pdf",
                fixture="2022_capital_gain_distributions.html",
                live=False,
            ),
            PageSpec(
                name="2021_capital_gain_distributions",
                url=f"{tax}/northerntrust/investment-management/global/en/documents/account-resources/tax-center/capital-gains-2021.pdf",
                fixture="2021_capital_gain_distributions.html",
                live=False,
            ),
        ]


class MorganStanleySource(HtmlTableSource):
    slug = "morgan_stanley"
    display_name = "Morgan Stanley Investment Management"
    aum_rank = 16
    priority = 16
    notes = (
        "Public ETF year-end PDFs under /im/publication/forms/tax/: "
        "2025_etf_year_end_distributions.pdf (full listed ETF ordinary-income "
        "table; CVLC income $0.283927; CG columns em-dash / 0.00% omitted) and "
        "2024_etf_year_end_distributions.pdf (CVLC income $0.222291, 0% CG; "
        "ex/record 12/23/2024, payable 12/27/2024). Live GET is often Akamai 403. "
        "No public filled ICI file. Open-end 2025 PDF was Akamai-blocked."
    )
    live_limitations = (
        "Year-end PDFs are often Akamai-walled to automated clients. "
        "Fixture transcribes the public ETF tables."
    )

    def pages(self) -> list[PageSpec]:
        tax = "https://www.morganstanley.com/im/publication/forms/tax"
        return [
            PageSpec(
                name="2025_etf_year_end",
                url=f"{tax}/2025_etf_year_end_distributions.pdf",
                fixture="2025_etf_year_end_sample.html",
                live=False,
            ),
            PageSpec(
                name="2024_etf_year_end",
                url=f"{tax}/2024_etf_year_end_distributions.pdf",
                fixture="2024_etf_year_end.html",
                live=False,
                large_aum_only=True,
            ),
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
        "distribution history: "
        "https://www.schwabassetmanagement.com/products/swtsx , "
        "https://www.schwabassetmanagement.com/products/swppx "
        "(≥$1B index heroes; SWTSX 2025 income $0.1805; 2024 $1.2252; 2023 $1.1379; "
        "2022 $1.0547; 2021 income $0.9649 / ST $0.0352 / LT $0.2022. "
        "SWPPX 2021 LT $0.0678) and the 2025 current-book "
        "https://www.schwabassetmanagement.com/products/swlsx (SWLSX LT $0.4957). "
        "No public filled ICI file. Skip SPA family grids."
    )
    live_limitations = (
        "Family annual grid is JavaScript-rendered. Product pages mix performance "
        "tables with multi-year history; fixtures transcribe December rows only."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_annual_distributions",
                url="https://www.schwabassetmanagement.com/resource/schwab-funds-actual-annual-distributions-2025",
                fixture="2025_annual_distributions.html",
                live=True,
            ),
            PageSpec(
                name="2024_annual_distributions",
                url="https://www.schwabassetmanagement.com/products/swtsx",
                fixture="2024_annual_distributions.html",
                live=False,
                large_aum_only=True,
            ),
            PageSpec(
                name="2023_annual_distributions",
                url="https://www.schwabassetmanagement.com/products/swtsx",
                fixture="2023_annual_distributions.html",
                live=False,
                large_aum_only=True,
            ),
            PageSpec(
                name="2022_annual_distributions",
                url="https://www.schwabassetmanagement.com/products/swtsx",
                fixture="2022_annual_distributions.html",
                live=False,
                large_aum_only=True,
            ),
            PageSpec(
                name="2021_annual_distributions",
                url="https://www.schwabassetmanagement.com/products/swtsx",
                fixture="2021_annual_distributions.html",
                live=False,
                large_aum_only=True,
            ),
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
        "2024 paid December book "
        "https://www.dimensional.com/chmedia/332797/source/download/2024-distributions.pdf "
        "(DISVX income $0.305 / LT $0.184; DFELX income $0.288 / LT $0.012; "
        "DFQTX income $0.101 / $0 CG). No public filled ICI file. "
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
            ),
            PageSpec(
                name="2024_capital_gain_distributions",
                url="https://www.dimensional.com/chmedia/332797/source/download/2024-distributions.pdf",
                fixture="2024_capital_gain_distributions.html",
                live=False,
                large_aum_only=True,
            ),
        ]


class ColumbiaThreadneedleSource(HtmlTableSource):
    slug = "columbia_threadneedle"
    display_name = "Columbia Threadneedle"
    aum_rank = 19
    priority = 19
    notes = (
        "Public 2025 mid-year estimate PDF "
        "https://www.columbiathreadneedleus.com/binaries/content/assets/cti/public/2025-mid-year-cap-gain-estimates-all-funds.pdf "
        "(e.g. IEVAX 0.86–1.25% of 5/31 NAV; ELGAX 18.62–21.95%). "
        "2024 YE finals "
        "https://www.columbiathreadneedleus.com/binaries/content/assets/cti/public/2024-cap-gains---mutual-funds.pdf "
        "(LBSAX LT $1.38581; ELGAX LT $4.05105; IEVAX $0 CG not stored). "
        "No public filled ICI file. 2023 YE PDF URL was 404. "
        "The 2025 mid-year all-funds PDF is wrap-unsafe (share-class % ranges "
        "interleaved with $0.00 fund headers) — not a column-safe full extract. "
        "Investor hub: https://www.columbiathreadneedleus.com/investor"
    )
    live_limitations = "Estimates are PDF. Fixture transcribes the public mid-year ranges and 2024 YE rows."

    def pages(self) -> list[PageSpec]:
        cti = "https://www.columbiathreadneedleus.com/binaries/content/assets/cti/public"
        return [
            PageSpec(
                name="2025_midyear_estimates",
                url=f"{cti}/2025-mid-year-cap-gain-estimates-all-funds.pdf",
                fixture="2025_midyear_estimates.html",
                live=False,
            ),
            PageSpec(
                name="2024_year_end_distributions",
                url=f"{cti}/2024-cap-gains---mutual-funds.pdf",
                fixture="2024_year_end_distributions.html",
                live=False,
                large_aum_only=True,
            ),
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
        "2025-final-ord-inc-cap-gain-distributions.pdf on the same path. "
        "No public filled ICI file. 2024 estimate/final sibling URLs on that "
        "path returned 404 (Pioneer site is now Victory-hosted) — skipped. "
        "Off the multi-year history ladder (non-US parent): do not add prior "
        "years; leave the 2025 fixture as-is."
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
