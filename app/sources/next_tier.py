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
                live=True,
                role="estimate",
                empty_ok=True,
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
        "is a JavaScript SPA (verified 2026-09-08). Public Section 19(a) notices: "
        "Franklin Universal Trust (FT) "
        "https://www.franklintempleton.com/forms-literature/download/ft-section-19-notice-12-31-2025 "
        "(Dec 2025 income $0.0358 / ST $0.0004 / RoC $0.0061), "
        "Franklin Limited Duration Income Trust (FTF) "
        "`.../ftf-section-19-notice-12-31-2025` (income $0.0418 / RoC $0.0197), "
        "Templeton Emerging Markets Income Fund (TEI) "
        "`.../tei-section-19-notice-12-31-2025` (income $0.1031 / ST $0.0648 / RoC $0.1846), "
        "and ClearBridge Tactical Dividend Income Class C (SMDLX) "
        "`.../SMDLX-section-19-notice-12-31-2025` (paid $0.149600 / RoC $0.073334). "
        "2024 sibling `.../ft-section-19-notice-12-31-2024` (income $0.0387 / RoC $0.0038). "
        "ICI reports hub is a JS SPA; no public filled Primary Layout download. "
        "≥$1B open-end (FKINX) amounts were not on a scrapeable family PDF — skipped. "
        "Wave 3: open-end estimate hub remains a JS SPA — no YE 2021–2023 MF book ingested."
    )
    live_limitations = (
        "Open-end December estimate tool is JavaScript-rendered. "
        "Use fixture mode or POST /ingest/distributions for advisor-exported grids."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="capital_gains_distribution_hub",
                url="https://www.franklintempleton.com/tools-and-resources/capital-gains-distribution",
                fixture="capital_gains_distribution_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
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
        "Paid December YE from official product-page Distributions History tables "
        "for DGAGX / DAGVX / DREVX / DREQX / DNLDX / PGROX / DGLAX (2021–2025). "
        "Appreciation DGAGX: 2025 LT $6.4552; 2024 LT $5.6247; 2023 LT $1.9798; "
        "2022 LT $2.7106; 2021 LT $1.6171. Dynamic Value DAGVX 2021 LT $6.7140. "
        "OI is published NQ+Q dividends; ST is published NQ+Q ST; published $0 omitted. "
        "DMCVX / PEOPX product URLs 404. Research Growth page prints DREQX "
        "(DWOAX Class A not on that table). Family 2021 estimate PDF URLs were 0-byte; "
        "2023 Dreyfus estimate PDF is preliminary — not YE finals. "
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
                live=True,
                role="estimate",
                empty_ok=True,
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
            PageSpec(
                name="2021_paid_year_end",
                url=product,
                fixture="2021_paid_year_end.html",
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
                live=True,
                role="estimate",
                empty_ok=True,
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
        "omitted. 2025 .../estimated-capital-gains-2025.pdf filename is the "
        "official paid YE equity CG book (page copy: 'In 2025 Northern Funds "
        "paid capital gain distributions on December 18th'; NOSIX ST $0.041654 "
        "/ LT $1.182288; NOMIX ST $0.136686 / LT $1.011150; NSGRX/NSCKX ST "
        "$0.189098 / LT $3.454742). 2024 .../estimated-capital-gains-2024.pdf "
        "is likewise the paid YE equity CG book ('In 2024 Northern Funds paid "
        "capital gain distributions on December 19th'; NOSIX ST $0.088060 / "
        "LT $0.699110; NSGRX/NSCKX LT $4.052773; NOSGX LT $7.263053). Page "
        "paid + year-end copy wins over the estimated-*.pdf filename so "
        "lookback counts these as final, not preliminary_estimate. "
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
                live=True,
                role="estimate",
                empty_ok=True,
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
                name="tax_forms_hub",
                url="https://www.morganstanley.com/im/publication/forms/tax",
                fixture="tax_forms_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_etf_year_end",
                url=f"{tax}/2025_etf_year_end_distributions.pdf",
                fixture="2025_etf_year_end_sample.html",
                live=True,
                role="estimate",
                empty_ok=True,
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
        "Family annual SPA "
        "https://www.schwabassetmanagement.com/resource/schwab-funds-actual-annual-distributions-2025 "
        "is still JavaScript (verified 2026-09-08). The official 2025 Actual Annual "
        "Distributions PDF https://schwab.bynder.com/m/3990d008e1558d0d/ is the full "
        "listed mutual-fund book (SWTSX income $0.1805; SWANX LT $1.5191; SWLSX LT "
        "$0.4957; daily NII omitted). 2021–2024 ≥$1B product-page history adds SWSSX / "
        "SWISX / SWLGX alongside SWTSX / SWPPX "
        "(SWSSX 2021 ST $0.3715 / LT $2.3981; SWLGX 2021 LT $0.9628). "
        "Schwab ETF product pages add December YE income for SCHD / SCHX / SCHB / "
        "SCHF / SCHG plus additional ≥$1B ETFs SCHA / SCHM / SCHE / SCHV / SCHP / "
        "SCHZ / SCHH / SCHC / FNDF (SCHD 2025 $0.2782; SCHA 2025 $0.1301; SCHM 2025 "
        "$0.1334; official $0.0000 ST/LT stored; 3-for-1 SCHD split 10/10/2024 "
        "printed as published). Family MF PDF does not include these ETFs. "
        "No public filled ICI file. Skip SPA family grids."
    )
    live_limitations = (
        "Family annual grid is JavaScript-rendered. Product pages mix performance "
        "tables with multi-year history; fixtures transcribe December rows only."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="annual_distributions_hub",
                url="https://www.schwabassetmanagement.com/resource/schwab-funds-actual-annual-distributions-2025",
                fixture="annual_distributions_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_annual_distributions",
                url="https://schwab.bynder.com/m/3990d008e1558d0d/",
                fixture="2025_annual_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
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
            PageSpec(
                name="etf_product_page_distributions",
                url="https://www.schwabassetmanagement.com/products/schd",
                fixture="etf_product_page_distributions.html",
                live=False,
                large_aum_only=False,
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
        "is the full MF/ETF table (DISVX income $0.305 / LT $0.184; DFELX income "
        "$0.288 / LT $0.012; DFQTX income $0.101 / published $0.000 CG stored). "
        "Official tax-center paid sheets (not the 332797 year-alias trap): "
        "2023 Mutual Funds Tax Sheet "
        "https://www.dimensional.com/chmedia/480410/source/download/2023-tax-sheet-mutual-fund-(main).pdf "
        "(Paid in 2023; DISVX NII $0.796370 / LT $0.025620; DFQTX NII $0.432810 / LT $0.131910; "
        "dashes omitted) and 2025 Tax Sheet Main "
        "https://www.dimensional.com/chmedia/480267/source/download/2025-Tax-Sheet-Main.pdf "
        "(Paid in 2025; DISVX NII $1.159770 / LT $1.059970; DFELX ST $0.752160 / LT $1.233710). "
        "QDI % / DRD / 163(j) pages skipped. Tickers mapped from the 2024 December book. "
        "2021–2022 tax-sheet siblings were not on the live tax center; "
        ".../332797/.../2021|2022|2023-distributions.pdf alias the 2024 December file. "
        "No public filled ICI file. Tax center: https://www.dimensional.com/us-en/tax"
    )
    live_limitations = "Year-end book is PDF. Fixture transcribes public paid/estimate rows."

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_capital_gain_distributions",
                url="https://www.dimensional.com/chmedia/440098/source/download/2025-capital-gain-distribution-estimates.pdf",
                fixture="2025_capital_gain_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2024_capital_gain_distributions",
                url="https://www.dimensional.com/chmedia/332797/source/download/2024-distributions.pdf",
                fixture="2024_capital_gain_distributions.html",
                live=False,
            ),
            PageSpec(
                name="2023_tax_sheet_paid",
                url="https://www.dimensional.com/chmedia/480410/source/download/2023-tax-sheet-mutual-fund-(main).pdf",
                fixture="2023_tax_sheet_paid.html",
                live=False,
            ),
            PageSpec(
                name="2025_tax_sheet_paid",
                url="https://www.dimensional.com/chmedia/480267/source/download/2025-Tax-Sheet-Main.pdf",
                fixture="2025_tax_sheet_paid.html",
                live=False,
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
        "(December Class A; LBSAX LT $1.38581; LEGAX Large Cap Growth LT $4.05105; "
        "ELGAX is Select Large Cap Growth Dec LT $0.72066). "
        "2022 YE finals "
        "https://www.columbiathreadneedleus.com/binaries/content/assets/cti/public/2022_cap_gains_year_end.pdf "
        "(LBSAX LT $0.56114; CBLAX LT $1.55549; published $0 omitted). "
        "June midyear rows skipped. 2021 book is estimates (ranges) — not YE finals. "
        "2023/2025 YE sibling URLs 404. No public filled ICI file. "
        "The 2025 mid-year all-funds PDF is wrap-unsafe (share-class % ranges "
        "interleaved with $0.00 fund headers) — not a column-safe full extract. "
        "Investor hub: https://www.columbiathreadneedleus.com/investor"
    )
    live_limitations = (
        "Estimates are PDF. Fixture transcribes the public mid-year ranges and "
        "2022 / 2024 YE Class A December rows."
    )

    def pages(self) -> list[PageSpec]:
        cti = "https://www.columbiathreadneedleus.com/binaries/content/assets/cti/public"
        return [
            PageSpec(
                name="2025_midyear_estimates",
                url=f"{cti}/2025-mid-year-cap-gain-estimates-all-funds.pdf",
                fixture="2025_midyear_estimates.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2024_year_end_distributions",
                url=f"{cti}/2024-cap-gains---mutual-funds.pdf",
                fixture="2024_year_end_distributions.html",
                live=False,
                large_aum_only=False,
            ),
            PageSpec(
                name="2022_year_end_distributions",
                url=f"{cti}/2022_cap_gains_year_end.pdf",
                fixture="2022_year_end_distributions.html",
                live=False,
                large_aum_only=False,
            ),
        ]


class AmundiSource(HtmlTableSource):
    slug = "amundi"
    display_name = "Amundi US / Pioneer"
    aum_rank = 20
    priority = 20
    notes = (
        "Included per Eric 2026-09-08 (Victory-hosted Pioneer tax center). "
        "US Pioneer retail funds transferred to Victory Capital (April 2025). "
        "Weekly walk: Pioneer / Amundi / Victory tax-center hubs plus the "
        "10/15/2025 estimate PDF and 2025 final PDFs that still resolve. "
        "Official 10/15/2025 Class A estimate book "
        "https://pioneerinvestments.com/content/dam/pioneer/en/documents/resources/tax-center/2025/10152025-mutual-funds-2025-capital-gain-estimates.pdf "
        "(Victory Pioneer Fund PIODX ST $0.53 / LT $3.73 / 9.09% of NAV). "
        "2025 finals: "
        "https://pioneerinvestments.com/content/dam/pioneer/en/documents/resources/tax-center/2025/2025-final-ord-inc-cap-gain-distributions.pdf "
        "and Victory-hosted "
        "https://investor.vcm.com/assets/resources-mutualfunddoc/Victory-Portfolios-IV-Mutual-Funds-2025-Final-Capital-Gains.pdf "
        "(PIODX Class A ST $0.8354 / LT $3.4776). Pioneer ILS Interval Fund XILSX omitted. "
        "Hubs: https://www.amundi.com/usinvestors/Resources/Tax-Center (redirects to Pioneer), "
        "https://pioneerinvestments.com/resources/tax-center, "
        "https://investor.vcm.com/tools-resources/tax-center. "
        "YE history: official 2024 Final Capital Gain Distributions (PIODX LT $4.1900) and "
        "2024 special year-end income estimates; official 2023 finals + 10/31/2023 estimates. "
        "Printed N/A / dashes omitted; published $0 stored. No public filled ICI file. "
        "Live fetch prefers issuer URLs with fixture fallback — never invent amounts."
    )
    live_limitations = (
        "Pioneer/Victory tax hubs are HTML shells; estimate/final books are PDF. "
        "Weekly walk is no-op success on empty/PDF-bytes pages; fixtures transcribe the official tables."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="pioneer_tax_center_hub",
                url="https://pioneerinvestments.com/resources/tax-center",
                fixture="pioneer_tax_center_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="amundi_tax_center_hub",
                url="https://www.amundi.com/usinvestors/Resources/Tax-Center",
                fixture="amundi_tax_center_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="victory_tax_center_hub",
                url="https://investor.vcm.com/tools-resources/tax-center",
                fixture="victory_tax_center_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_capital_gain_estimates",
                url=(
                    "https://pioneerinvestments.com/content/dam/pioneer/en/documents/"
                    "resources/tax-center/2025/10152025-mutual-funds-2025-capital-gain-estimates.pdf"
                ),
                fixture="2025_capital_gain_estimates.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_final_ordinary_income_and_capital_gains",
                url=(
                    "https://pioneerinvestments.com/content/dam/pioneer/en/documents/"
                    "resources/tax-center/2025/2025-final-ord-inc-cap-gain-distributions.pdf"
                ),
                fixture="2025_final_ordinary_income_and_capital_gains.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_victory_portfolios_iv_final_capital_gains",
                url=(
                    "https://investor.vcm.com/assets/resources-mutualfunddoc/"
                    "Victory-Portfolios-IV-Mutual-Funds-2025-Final-Capital-Gains.pdf"
                ),
                fixture="victory_portfolios_iv_final_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2024_final_capital_gains",
                url=(
                    "https://pioneerinvestments.com/content/dam/pioneer/en/documents/"
                    "resources/tax-center/2024/2024-Final-Capital-Gain-Distributions.pdf"
                ),
                fixture="2024_final_capital_gains.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2024_special_year_end_distributions",
                url=(
                    "https://pioneerinvestments.com/content/dam/pioneer/en/documents/"
                    "resources/tax-center/2024-Special-Year-End-Distributions.pdf"
                ),
                fixture="2024_special_year_end_distributions.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2023_final_capital_gains",
                url=(
                    "https://pioneerinvestments.com/content/dam/pioneer/en/documents/"
                    "resources/tax-center/2023/2023-Final-Capital-Gain-Distributions.pdf"
                ),
                fixture="2023_final_capital_gains.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2023_capital_gain_estimates",
                url=(
                    "https://pioneerinvestments.com/content/dam/pioneer/en/documents/"
                    "resources/tax-center/2023/Capital-Gain-Distribution-Estimates-as-of-10-31-2023.pdf"
                ),
                fixture="2023_capital_gain_estimates.html",
                live=False,
                role="history",
            ),
        ]
