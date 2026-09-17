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
        "All-dash Concentrated / High Yield rows omitted. Printed 0.00* stored as 0.00. "
        "Official 5y parallel W leftover re-probe (2026-09-16): live tax library still "
        "serves estimate / Important Tax Information / Form 8937 only. The 2021 "
        "https://www.lazardassetmanagement.com/docs/1631/LazardFundsAnnualDistributions.pdf "
        "is an Estimated Distribution Per Share book. 2022–2024 December paid "
        "declaration PDFs unpublished. "
        "Official 5y WAVE BY leftover (existing in-book only): Lazard Funds, Inc. "
        "FYE December 31 N-CSR Financial Highlights unlock leftover Institutional "
        "2021–2025 paid history on estimate-only in-book identities (LZIEX / LZEMX / "
        "GLIFX / LDMIX / LISIX / LZFIX / LEAIX / ICMPX / LZESX / LZUSX / LZCOX / "
        "LZISX / LEOIX / LCAIX). Calendar-safe as_of 12/31. Class-level "
        "Institutional — never sibling-copied onto Open / R6. Income is ordinary "
        "income; net realized gain is unsplit total capital gains; printed return "
        "of capital stored. Issuer dashes omitted. Heroes: LZIEX 2025 OI $0.48 / "
        "CG $1.84; LZEMX 2025 OI $0.51; GLIFX 2025 OI $0.51 / CG $0.62. N-CSR "
        "https://www.sec.gov/Archives/edgar/data/874964/000093041326000617/"
        "c114847_ncsr-ixbrl.htm (0000930413-26-000617) verified against 2023 "
        "0000930413-24-000784. US Convertibles CONIX incomplete Institutional "
        "lookback years stay unmatched. Sister WAVE BX Pioneer Mid Cap Value "
        "PCCGX / PYCGX / PMCKX, BW Rainier RAIIX, BV HMDCX, BU PCGRX, BT "
        "Federated SVD, BS PEQIX, BR Grandeur Peak, BQ Pioneer Dec 31, BP Beacon, "
        "BO–BI / BK / BG DWS, BM Baird, BL Thrivent, BJ RiverPark, BH TCW, and "
        "prior BD–BF books stay on their leftover pages — not re-emitted here. "
        "Alger leftovers stay reserved / disjoint. WAVE BY leftover N-CSR paid "
        "history is fixture-only."
    )
    live_limitations = (
        "Year-end book is PDF. Fixture transcribes the official Institutional / Open / R6 table. "
        "Paid 2021–2024 declaration siblings unpublished. "
        "WAVE BY Lazard Institutional 2021–2025 leftover N-CSR is fixture-only."
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
            ),
            PageSpec(
                name="leftover_ncsr_institutional_2021_2025_wave_by",
                url=(
                    "https://www.sec.gov/Archives/edgar/data/874964/"
                    "000093041326000617/c114847_ncsr-ixbrl.htm"
                ),
                fixture="leftover_ncsr_institutional_2021_2025_wave_by.html",
                live=False,
                role="history",
            ),
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
        "Tickers from official am.manning-napier.com/products/mutual-funds "
        "(CEIIX / CEISX / CEIZX / MNDFX / MDFSX / MDVWX / MDVZX / EXEYX / MEYWX / "
        "MNHAX / MNHYX / MHYWX / MHYZX / MNBIX / MNECX / MNBRX / MNBAX / MNBWX / "
        "MNHIX / MNHCX / MNHRX / EXHAX / MNHWX / MNMIX / MNMCX / MNMRX / EXBAX / "
        "MNMWX / RAIIX / RISAX / RAIWX / RAIRX / MSHIX / MSYSX / MSHWX / MSYZX). "
        "Amounts and CUSIPs unchanged. "
        "Official 5y parallel W leftover: December paid YE from the same "
        "`YYYY%20Distributions.pdf` path for 2021–2024 "
        "(MNHIX 2021 ST $0.83490 / LT $0.85360; EXEYX 2024 LT $1.73250). "
        "Callodine 2021–2022, Systematic High Yield 2021–2024, and "
        "RISAX 2022+2024 December rows unpublished. "
        "Official 5y WAVE BW leftover (existing in-book only): Rainier "
        "International Discovery Class I FYE October 31 N-CSR Financial "
        "Highlights unlock leftover 2022 CG $0.51 on the Parallel W / 2025 "
        "December paid Class I book (RAIIX). Calendar-safe as_of 10/31. "
        "Class-level — never sibling-copied (RISAX / RAIWX / RAIRX). Income "
        "dash omitted — never invent $0. Rainier N-CSR "
        "https://www.sec.gov/Archives/edgar/data/751173/000199937126000259/"
        "mn-ncsr_103125.htm (0001999371-26-000259) verified against 2024 "
        "0001999371-25-000097. Sister WAVE BV HMDCX, BU PCGRX, BT Federated "
        "SVD, BS PEQIX, BR Grandeur Peak, BQ Pioneer Dec 31, BP Beacon, "
        "BO–BI / BK / BG DWS, BM Baird, BL Thrivent, BJ RiverPark, BH TCW, "
        "and prior BD–BF books stay on their leftover pages — not re-emitted "
        "here. Alger leftovers stay reserved / disjoint. WAVE BW leftover "
        "N-CSR paid history is fixture-only."
    )
    live_limitations = (
        "Paid book is PDF. Fixture transcribes December CG-paying CUSIP/class rows. "
        "Weekly walk hits the current-year PDF; older leftover years are fixture history. "
        "WAVE BW Rainier Class I 2022 leftover N-CSR is fixture-only."
    )

    def pages(self) -> list[PageSpec]:
        dist = "https://am.manning-napier.com/media/fund-documents/distributions"
        return [
            PageSpec(
                name="2025_distributions",
                url=f"{dist}/2025%20Distributions.pdf",
                fixture="2025_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="leftover_paid_year_end_parallel_w",
                url=f"{dist}/2024%20Distributions.pdf",
                fixture="leftover_paid_year_end_parallel_w.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="leftover_ncsr_raiix_2022_wave_bw",
                url=(
                    "https://www.sec.gov/Archives/edgar/data/751173/"
                    "000199937126000259/mn-ncsr_103125.htm"
                ),
                fixture="leftover_ncsr_raiix_2022_wave_bw.html",
                live=False,
                role="history",
            ),
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
        "The PDF is fund-level for all share classes; tickers are public Institutional identifiers. "
        "Official 5y parallel W leftover: Institutional paid history "
        "https://westwoodgroup.com/assets/distribution-history/ "
        "(WHGLX 2025 LT $2.4094 / 2021 ST $0.3881 / LT $1.8895). A / C / Ultra "
        "siblings are not in-book leftovers. WWMCX 2021–2022 unpublished on the "
        "Institutional history (inception 11/30/2021; 2022 N-CSR OI dash — "
        "never invent $0). Official 5y WAVE BI leftover remasure: WQAIX 2025 "
        "N-CSR FYE Oct 31 reprints already-booked December 2024 paid amounts "
        "(OI $0.16 / CG $0.45); the 2025 AllCap final line is blank and "
        "subsequent events omit AllCap after 97.5% redemptions. Ultra sibling "
        "WQAUX never copied. WQAIX leftover 2025 stays unmatched."
    )
    live_limitations = (
        "Estimate book is PDF. Fixture transcribes public Institutional identifiers. "
        "Paid history is a multi-class PDF; leftover fixture keeps in-book Institutional rows."
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
            ),
            PageSpec(
                name="leftover_paid_history_parallel_w",
                url="https://westwoodgroup.com/assets/distribution-history/",
                fixture="leftover_paid_history_parallel_w.html",
                live=False,
                role="history",
            ),
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
        "Published $0.00 ST stored. "
        "Official 5y parallel W leftover: 2025 final "
        "https://www.bostonpartners.com/uploads/2026/01/"
        "b74c74af65fea1e9b9f5d0e970e8a009/bp-funds-2025-final-cap-gain-distv2.pdf "
        "(BPAIX ST $0.02 / LT $2.68) and 2024 final "
        "https://www.bostonpartners.com/uploads/2024/12/"
        "6a90ad46be706c82555fd6c9ea3d7cd2/bp-funds-2024-final-cap-gain-dist.pdf "
        "(BPAIX ST $0.04 / LT $2.81). BELSX / WPGHX not in-book leftovers. "
        "2021–2023 December finals unpublished on the live uploads tree."
    )
    live_limitations = (
        "Estimate book is PDF. Fixture transcribes public Institutional + Investor identifiers. "
        "Paid leftover years are fixture history."
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
            ),
            PageSpec(
                name="leftover_paid_finals_parallel_w",
                url=(
                    "https://www.bostonpartners.com/uploads/2026/01/"
                    "b74c74af65fea1e9b9f5d0e970e8a009/bp-funds-2025-final-cap-gain-distv2.pdf"
                ),
                fixture="leftover_paid_finals_parallel_w.html",
                live=False,
                role="history",
            ),
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
        "The PDF is fund-level; tickers are public no-load identifiers. "
        "Official 5y parallel W leftover re-probe (2026-09-16): live product pages "
        "print current + previous calendar year only (HOVLX 2025 YE already in book; "
        "2026 mid-year is outside the window). Dated 2021–2024 Year-End-Distributions.pdf "
        "siblings unpublished; Wayback CDX was offline on re-probe. "
        "Official 5y WAVE AR leftover (existing in-book only): Homestead Funds, Inc. "
        "FYE December 31 N-CSR Financial Highlights unlock leftover 2021–2024 on the "
        "2025 no-load book (HSTIX / HOVLX / HNASX / HISIX / HSCSX). Calendar-safe "
        "as_of 12/31. Class-level single-class no-load — never sibling-copied. "
        "2024 N-CSR https://www.sec.gov/Archives/edgar/data/865733/000114554925016761/8dd5cf6f78f6691.htm "
        "verified against 2023/2022/2021 N-CSR siblings. Income is ordinary income; "
        "net realized gain is unsplit total capital gains. Issuer dashes and "
        "less-than-$0.01 omitted (HSCSX 2022 OI; HNASX 2021–2024 OI). Bond / "
        "money-market / liquidated Rural America names are not in-book leftovers. "
        "WAVE AR leftover N-CSR paid history is fixture-only."
    )
    live_limitations = (
        "Year-end book is PDF. Fixture transcribes public no-load identifiers. "
        "Product-page history is current + previous year only. "
        "Leftover 2021–2024 N-CSR paid history is fixture-only."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_year_end_distributions",
                url="https://www.homesteadadvisers.com/wp-content/uploads/Year-End-Distributions.pdf",
                fixture="2025_year_end_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="leftover_ncsr_2021_2024_wave_ar",
                url="https://www.sec.gov/Archives/edgar/data/865733/000114554925016761/8dd5cf6f78f6691.htm",
                fixture="leftover_ncsr_2021_2024_wave_ar.html",
                live=False,
                role="history",
            ),
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
        "All-None Conservative Allocation / Core Bond / Covered Call omitted. "
        "Official 5y parallel W leftover re-probe (2026-09-16): live tax-center "
        "HTML is the 2025 book only. Dated 2021–2024 tax-center / capital-gains "
        "siblings unpublished; Wayback CDX was offline on re-probe. Class Y / I / R6 "
        "siblings not in the tickered leftover set are not copied. "
        "Official 5y WAVE BA leftover (existing in-book only): Madison Funds "
        "FYE October 31 N-CSR Financial Highlights unlock leftover 2021–2024 "
        "on the 2025 tax-center paid book (Aggressive Allocation MAGSX, "
        "Diversified Income MBLAX, Dividend Income MADAX, Large Cap MNVAX, "
        "Mid Cap GTSGX, Moderate Allocation MMDAX, Small Cap BVAOX). "
        "Calendar-safe as_of 10/31. Class-level Class A / Y — never "
        "sibling-copied. Conservative Allocation / Core Bond / Covered Call "
        "are not on the 2025 paid book and are not in-book leftovers. ETF "
        "wrappers MAGG / MSTI leftover years remasured as walls (different "
        "trust; calendar Dec 31, not this Oct 31 N-CSR). Income is ordinary "
        "income; capital gains are unsplit total capital gains. Issuer dashes "
        "and printed $0.00 less-than / rounded footnotes omitted (GTSGX 2022 "
        "OI; BVAOX 2022 OI). 2025 stays on the existing tax-center book "
        "(MNVAX LT $1.92670046 is not overwritten by N-CSR CG $1.59). "
        "N-CSR https://www.sec.gov/Archives/edgar/data/1040612/"
        "000175392626000073/g211434_ncsr.htm. WAVE BA leftover N-CSR paid "
        "history is fixture-only."
    )
    live_limitations = (
        "Public HTML is fund-name / ST / LT only (no ticker column). Fixture fallback. "
        "Prior-year tax-center tables unpublished. "
        "Leftover 2021–2024 N-CSR paid history is fixture-only."
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
            ),
            PageSpec(
                name="leftover_ncsr_2021_2024_wave_ba",
                url=(
                    "https://www.sec.gov/Archives/edgar/data/1040612/"
                    "000175392626000073/g211434_ncsr.htm"
                ),
                fixture="leftover_ncsr_2021_2024_wave_ba.html",
                live=False,
                role="history",
            ),
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
        "Published $0.0000 ST stored. "
        "Official 5y parallel W leftover: 2024 paid "
        "https://www.lsvasset.com/pdf/fund-docs/2024-Distributions.pdf "
        "(LSVEX ST $0.0152 / LT $1.6848; income $0.5666). 2021–2023 year-end PDFs "
        "404. Official 5y WAVE AU leftover (existing in-book only): Advisors' "
        "Inner Circle Fund FYE October 31 N-CSR Financial Highlights unlock "
        "leftover 2021–2023 on the 2024–2025 Institutional / Investor paid book "
        "(LSVEX / LVAEX / LSVVX / LVAVX / LSVQX / LVAQX / LSVMX / LVAMX / "
        "LSVZX / LVAZX / LSVFX / LVAFX / LSVGX / LVAGX). Calendar-safe as_of "
        "10/31. Class-level Institutional / Investor — never sibling-copied. "
        "2023 Value Equity N-CSR "
        "https://www.sec.gov/Archives/edgar/data/878719/000119312524005240/d676331dncsr.htm "
        "verified against Conservative Value / Small Cap Value / U.S. Managed "
        "Volatility / Emerging Markets / Global Managed Volatility / Global Value "
        "2023 N-CSR siblings. Income is ordinary income; net realized gain is "
        "unsplit total capital gains. Issuer dashes omitted (LSVQX 2021–2023 CG; "
        "LSVZX 2023 CG; LSVVX 2021 CG; LSVFX 2021–2022 CG; LSVGX 2021 CG; "
        "LVAGX 2023 OI). WAVE AU leftover N-CSR paid history is fixture-only."
    )
    live_limitations = (
        "Year-end book is PDF. Fixture transcribes public Institutional + Investor identifiers. "
        "2021–2023 year-end PDFs 404. Leftover 2021–2023 N-CSR paid history is fixture-only."
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
            ),
            PageSpec(
                name="leftover_paid_year_end_parallel_w",
                url="https://www.lsvasset.com/pdf/fund-docs/2024-Distributions.pdf",
                fixture="leftover_paid_year_end_parallel_w.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="leftover_ncsr_2021_2023_wave_au",
                url="https://www.sec.gov/Archives/edgar/data/878719/000119312524005240/d676331dncsr.htm",
                fixture="leftover_ncsr_2021_2023_wave_au.html",
                live=False,
                role="history",
            ),
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
        "Record 12/29/2025; ex/pay 12/30/2025. "
        "Official 5y WAVE BC leftover (existing in-book only): LKCM Funds FYE "
        "December 31 N-CSR Financial Highlights unlock leftover 2021–2025 on "
        "the 2025 estimate book (Equity LKEQX, Small Cap LKSCX, Balanced LKBAX; "
        "Small-Mid LKSMX is official year-depth only). Calendar-safe as_of "
        "12/31. Class-level — never sibling-copied. Fixed Income / "
        "International / Aquinas Catholic Equity are not on the 2025 estimate "
        "book and are not in-book leftovers. 2025 estimate rows stay estimates "
        "(LKEQX LT $3.8475 is not overwritten by N-CSR CG $2.91). Income is "
        "ordinary income; capital gains are unsplit total capital gains. "
        "Issuer dashes and printed $0.00 less-than / rounded footnotes omitted "
        "(LKSCX 2025 OI; LKSMX 2023–2024 CG dashes). N-CSR "
        "https://www.sec.gov/Archives/edgar/data/918942/000113322826003110/"
        "lf-efp22616_ncsr.htm verified against 2024 0001133228-25-002005 and "
        "2023 0001193125-24-058053. WAVE BC leftover N-CSR paid history is "
        "fixture-only."
    )
    live_limitations = (
        "Estimate book is PDF. Fixture transcribes public ticker rows. "
        "Leftover 2021–2025 N-CSR paid history is fixture-only."
    )

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
            ),
            PageSpec(
                name="leftover_ncsr_2021_2025_wave_bc",
                url=(
                    "https://www.sec.gov/Archives/edgar/data/918942/"
                    "000113322826003110/lf-efp22616_ncsr.htm"
                ),
                fixture="leftover_ncsr_2021_2025_wave_bc.html",
                live=False,
                role="history",
            ),
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
        "High Yield, Floating Rate CMBS, and Next Century Growth omitted. "
        "Official 5y WAVE BJ leftover (existing in-book only): tax-center December "
        "Final Capital Gains & Income PDFs unlock leftover 2021–2024 on the "
        "2025 paid Final book. Wedgewood Institutional RWGIX / Retail RWGFX "
        "complete 5y (2021 ST $0.0066 / LT $0.6912; 2022 ST $0.0077 / LT $0.5773; "
        "2023 LT $0.0994; 2024 LT $0.8195). Large Growth RPXIX / RPXFX is "
        "year-depth only (2021 ST $1.0083 / LT $3.0750; RPXIX 2022 income "
        "$0.0011; 2024 LT $2.0330) — 2023 official dashes stay unmatched. "
        "Calendar-safe December ex / payable dates. Class-level Institutional / "
        "Retail — never sibling-copied. Next Century Large Growth 2024 dashes, "
        "Long/Short, Short Term High Yield, Floating Rate CMBS, Strategic Income, "
        "and Next Century Growth are not in-book leftovers. 2025 stays on the "
        "existing paid Final PDF (RWGIX ST $0.0068 / LT $0.5577 is not "
        "overwritten). Official leftovers "
        "https://www.riverparkfunds.com/assets/pdfs/news/"
        "Year_End_Final_Distribution_Information_2021.pdf "
        "https://www.riverparkfunds.com/assets/pdfs/news/"
        "Year_End_Final_Distribution_Information_2022.pdf "
        "https://www.riverparkfunds.com/assets/pdfs/news/"
        "Distribution_Info_2023_Website_RFT_FINAL_CAP_GAINS_FINAL_INCOME.pdf "
        "https://riverparkfunds.com/assets/pdfs/news/"
        "Distribution_Info_2024_Website_RFT_FINAL_CAP_GAINS_FINAL_INCOME.pdf "
        "WAVE BJ leftover paid history is fixture-only. Live most-recent 2025 "
        "Final still omits 2021–2024."
    )
    live_limitations = (
        "Year-end book is PDF. Fixture transcribes public Institutional + Retail paying rows. "
        "Weekly walk hits the how-to-invest hub (empty/403/PDF-bytes = no-op success). "
        "Leftover 2021–2024 tax-center paid history is fixture-only."
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
            ),
            PageSpec(
                name="leftover_paid_year_end_2021_2024_wave_bj",
                url=(
                    "https://www.riverparkfunds.com/assets/pdfs/news/"
                    "Year_End_Final_Distribution_Information_2021.pdf"
                ),
                fixture="leftover_paid_year_end_2021_2024_wave_bj.html",
                live=False,
                role="history",
            ),
        ]
