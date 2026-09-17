"""DWS / Xtrackers US ETF + open-end mutual-fund distribution adapter."""

from __future__ import annotations

from app.sources.html_source import HtmlTableSource, PageSpec


class DwsSource(HtmlTableSource):
    slug = "dws"
    display_name = "DWS / Xtrackers"
    aum_rank = 112
    priority = 112
    notes = (
        "US open-end only (DBX Advisors ETFs + DWS Distributors mutual funds). "
        "UCITS / Luxembourg and closed-end omitted. "
        "Tax hub: https://www.dws.com/en-us/resources/tax-center/ "
        "Official 2025 ICI Primary Layout "
        "https://www.dws.com/globalassets/cio/dam-us/pdfs/resources/tax-center/forms/"
        "2025-xtrackers-etfs-primary-layout.pdf "
        "(report date 01/13/2026) is the full US Xtrackers ETF book: 42 listed "
        "tickers; 40 payers ingested "
        "(DBEF 6/20/2025 income $1.419 / 12/19/2025 $1.25062; "
        "HYLB 2/3/2025 $0.19723 / 12/22/2025 $0.20891; "
        "HDEF 6/20/2025 $0.63065; ASHR 12/19/2025 $0.75811; "
        "PSWD 12/5/2025 ST $0.15778). Printed $0.00 ICI lines omitted. "
        "ASHS and IND printed all-zero 2025 ICI rows — omitted. "
        "2025 Xtrackers CG PDFs list the family; only PSWD printed non-zero "
        "(estimate ST $0.1599; final ST $0.1578). "
        "Official 2025 retail MF CG PDF "
        "https://www.dws.com/globalassets/cio/dam-us/pdfs/resources/tax-center/forms/"
        "capital-gains-retail-final.pdf "
        "is fund-level; Class A tickers (Equity 500 Index Class S BTIEX) from "
        "the 2026 sales-charge Nasdaq table "
        "https://www.dws.com/document/specific/MARKETING/sales_charge_schedule.pdf/049518/ "
        "(SDGAX LT $9.7933; SUWAX LT $3.5547; KTCAX ST $0.0981 / LT $3.5700; "
        "SXPAX ST $0.4200 / LT $1.3491). Printed $0.0000 and CEF section omitted. "
        "2026 mid-year MF estimate PDF "
        "https://www.dws.com/globalassets/cio/dam-us/pdfs/resources/tax-center/forms/"
        "2026-dws-mutual-funds-estimated-mid-year-capital-gains.pdf "
        "(SXPAX LT $0.6101; TOLLX ST $0.0176 / LT $0.2419; BTIEX LT $6.1523; "
        "COMAX LT $0.4142). "
        "2024 ICI / CG siblings 404 on the live tax-center path this session; "
        "Parallel L leftover ICI Primary (report date 01/21/2025) is the official "
        "filled 2024 Xtrackers book transcribed from issuer PDF bytes "
        "(ASHR 12/20/2024 income $0.29945; DBEF 12/20/2024 $0.29706; "
        "HYLB 12/23/2024 $0.21907). 2021–2023 ICI siblings still 404 / "
        "Wayback CDX empty — leftover ETFs stay 2y, not 5y. "
        "Official 5y WAVE BG leftover (existing in-book only): DWS Equity 500 "
        "Index Class S BTIEX and S&P 500 Index Class A SXPAX FYE December 31 "
        "N-CSR Financial Highlights unlock leftover 2021–2024 on the 2025 paid "
        "retail book. Calendar-safe as_of 12/31. Class-level Class S / Class A "
        "— never sibling-copied onto Institutional / Class R / Class C / Class S "
        "siblings (BTIIX / BTIRX / SXPCX / SCPIX / SXPRX). Income is ordinary "
        "income; net realized gain is unsplit total capital gains. 2025 stays "
        "on the existing paid retail PDF (BTIEX ST $3.5046 / LT $16.0529 is not "
        "overwritten by N-CSR 2-decimal highlights). Equity 500 Index N-CSR "
        "https://www.sec.gov/Archives/edgar/data/862157/000008805326000209/"
        "ar123125e500.htm and S&P 500 Index N-CSR "
        "https://www.sec.gov/Archives/edgar/data/862157/000008805326000213/"
        "ar123125spf500if.htm verified against 2023 N-CSR 0000088053-24-000160. "
        "Official 5y WAVE BI leftover (existing in-book only): DWS Science and "
        "Technology Class A KTCAX FYE October 31 N-CSR Financial Highlights "
        "unlock leftover 2021–2024 on the 2025 paid retail book. Calendar-safe "
        "as_of 10/31. Class-level Class A — never sibling-copied onto Class C / "
        "Institutional / Class S leftovers (KTCCX / KTCIX / KTCSX). KTCAX "
        "2021–2024 are net investment loss years — no ordinary-income row "
        "stored (never invent $0). 2025 stays on the existing paid retail PDF "
        "(KTCAX ST $0.0981 / LT $3.5700 is not overwritten by N-CSR 2-decimal "
        "highlights). N-CSR "
        "https://www.sec.gov/Archives/edgar/data/88048/000008805325001134/"
        "ar103125dstf.htm verified against 2024 N-CSR 0000088053-25-000013. "
        "WAVE BG Dec 31 BTIEX / SXPAX stay on their leftover page — not "
        "re-emitted here. Official 5y WAVE BK leftover (existing in-book only): "
        "DWS RREEF Global Infrastructure Class A TOLLX FYE December 31 N-CSR "
        "Financial Highlights unlock leftover 2021–2024 on the 2025 paid retail "
        "book. Calendar-safe as_of 12/31. Class-level Class A — never "
        "sibling-copied onto Class C / Class S / Institutional / Class R6 "
        "leftovers (TOLCX / TOLSX / TOLIX / TOLZX). Income is ordinary income; "
        "net realized gain is unsplit total capital gains. 2025 stays on the "
        "existing paid retail PDF (TOLLX ST $0.1280 / LT $1.1959 is not "
        "overwritten by N-CSR 2-decimal highlights). N-CSR "
        "https://www.sec.gov/Archives/edgar/data/793597/000008805326000211/"
        "ar123125drgif.htm verified against 2024 N-CSR 0000088053-25-000195. "
        "WAVE BG Dec 31 BTIEX / SXPAX and WAVE BI Oct 31 KTCAX stay on their "
        "leftover pages — not re-emitted here. SUWAX / SDGAX FYE September 30, "
        "DESAX / KDHAX ~November 30, SZCAX / DCUAX FYE September 30, and SUHAX "
        "FYE May 31 are not calendar-safe. Official 5y WAVE BN leftover "
        "(existing in-book only): DWS Global Small Cap Class A KGDAX FYE "
        "October 31 N-CSR Financial Highlights unlock leftover 2021–2024 on "
        "the 2025 paid retail book. Calendar-safe as_of 10/31. Class-level "
        "Class A — never sibling-copied onto Class C / Class S / "
        "Institutional / Class R6 leftovers (KGDCX / SGSCX / KGDIX / KGDZX). "
        "Income is ordinary income; net realized gain is unsplit total "
        "capital gains. Issuer dashes omitted (2021 OI). Issuer printed "
        "$0.00* 2023 OI omitted — never invent $0. 2025 stays on the "
        "existing paid retail PDF (KGDAX ST $0.5664 / LT $2.5269 is not "
        "overwritten by N-CSR 2-decimal highlights). N-CSR "
        "https://www.sec.gov/Archives/edgar/data/793597/000008805325001132/"
        "ar103125dgsc.htm verified against 2024 N-CSR 0000088053-25-000010 "
        "and the April 30 2025 N-CSRS leftover columns. WAVE BL Thrivent "
        "TMAIX / TMCVX / TSCSX / TCAIX / IBBFX / TWAIX, WAVE BK DWS RREEF "
        "TOLLX, WAVE BI Oct 31 KTCAX, WAVE BJ RiverPark RWGIX / RWGFX, "
        "WAVE BG Dec 31 BTIEX / SXPAX, and WAVE BH TCW stay on their leftover "
        "pages — not re-emitted here. WAVE BM Baird Chautauqua CCGIX / "
        "CCGSX / CCWIX / CCWSX stay on their leftover page — not "
        "re-emitted here. Official 5y WAVE BO leftover (existing in-book "
        "only): DWS Global Income Builder Class A KTRAX FYE October 31 "
        "N-CSR Financial Highlights unlock leftover 2021–2024 on the 2025 "
        "paid retail book. Calendar-safe as_of 10/31. Class-level Class A "
        "— never sibling-copied onto Class C / Class S / Institutional / "
        "Class R6 leftovers (KTRCX / KTRSX / KTRIX / KTRZX). Income is "
        "ordinary income; net realized gain is unsplit total capital "
        "gains. Issuer dashes omitted (2024 / 2023 / 2021 CG) — never "
        "invent $0. 2025 stays on the existing paid retail PDF (KTRAX ST "
        "$0.2807 / LT $0.1744 is not overwritten by N-CSR 2-decimal "
        "highlights). N-CSR "
        "https://www.sec.gov/Archives/edgar/data/95603/000008805325001130/"
        "ar103125dgib.htm verified against the issuer Oct 31 2025 Annual "
        "Financial Statements and 2023 N-CSR 0000088053-23-000904. WAVE BN "
        "Global Small Cap KGDAX, WAVE BL Thrivent TMAIX / TMCVX / TSCSX / "
        "TCAIX / IBBFX / TWAIX, WAVE BK DWS RREEF TOLLX, WAVE BI Oct 31 "
        "KTCAX, WAVE BJ RiverPark RWGIX / RWGFX, WAVE BG Dec 31 BTIEX / "
        "SXPAX, and WAVE BH TCW stay on their leftover pages — not "
        "re-emitted here. WAVE BM Baird Chautauqua CCGIX / CCGSX / CCWIX / "
        "CCWSX stay on their leftover page — not re-emitted here. Alger "
        "leftovers stay reserved / disjoint. WAVE BG / BI / BK / BN / BO "
        "leftover N-CSR paid history is fixture-only. Live most-recent "
        "retail PDF still omits 2021–2024; Wayback CDX offline. "
        "2026 Xtrackers dividend schedule has dates only. "
        "etf.dws.com and dws.com mutual-fund product lists are JavaScript SPAs. "
        "ICI secondary is 1099 characterization, not amounts. "
        "VIP / variable series omitted. Growth of $X added for DBEF."
    )
    live_limitations = (
        "Family books are PDF. Weekly walk uses the DWS tax-center hub, "
        "Xtrackers estimated/final CG PDFs, Xtrackers ICI primary/secondary URLs, "
        "2025 retail MF CG PDF, 2026 MF mid-year estimate PDF, "
        "2026 dividend-schedule hub, etf.dws.com home, and the mutual-fund SPA. "
        "Empty/PDF-bytes pages are no-op success. "
        "2024 ICI primary URL 404s. Do not invent amounts from the date schedule "
        "or ICI secondary percentages. Leftover 2021–2024 N-CSR paid history "
        "(WAVE BG Dec 31, WAVE BI Oct 31, WAVE BK RREEF Dec 31, WAVE BN "
        "Global Small Cap Oct 31, and WAVE BO Global Income Builder Oct 31) "
        "is fixture-only."
    )

    def pages(self) -> list[PageSpec]:
        forms = "https://www.dws.com/globalassets/cio/dam-us/pdfs/resources/tax-center/forms"
        return [
            PageSpec(
                name="tax_center_hub",
                url="https://www.dws.com/en-us/resources/tax-center/",
                fixture="tax_center_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="etf_home",
                url="https://etf.dws.com/en-us/",
                fixture="etf_home.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="mf_products_hub",
                url="https://www.dws.com/en-us/products/mutual-funds/",
                fixture="mf_products_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_estimated_capital_gains",
                url="https://etf.dws.com/download/asset/9a1f54ed-fcf9-4b50-9d74-ae2343ee5bef",
                fixture="2025_estimated_capital_gains.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_final_capital_gains",
                url=f"{forms}/xtrackers_etf_capital_gains.pdf",
                fixture="2025_final_capital_gains.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_retail_capital_gains",
                url=f"{forms}/capital-gains-retail-final.pdf",
                fixture="2025_retail_capital_gains.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2026_estimated_midyear_capital_gains",
                url=f"{forms}/2026-dws-mutual-funds-estimated-mid-year-capital-gains.pdf",
                fixture="2026_estimated_midyear_capital_gains.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2026_dividend_schedule_hub",
                url="https://etf.dws.com/en-us/etf-documents/dividend-schedules-2026/",
                fixture="2026_dividend_schedule_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="ici_primary_2025",
                url=f"{forms}/2025-xtrackers-etfs-primary-layout.pdf",
                fixture="ici_primary_2025.csv",
                live=True,
                role="estimate",
                empty_ok=True,
                parser="ici",
            ),
            PageSpec(
                name="ici_leftover_2024",
                url=f"{forms}/2024-xtrackers-etfs-primary-layout.pdf",
                fixture="ici_leftover_2024.csv",
                live=False,
                role="history",
                large_aum_only=False,
                parser="ici",
            ),
            PageSpec(
                name="ici_secondary_hub",
                url=f"{forms}/2025_xtrackers_etfs_secondary_layout.pdf",
                fixture="ici_secondary_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="leftover_ncsr_2021_2024_wave_bg",
                url=(
                    "https://www.sec.gov/Archives/edgar/data/862157/"
                    "000008805326000209/ar123125e500.htm"
                ),
                fixture="leftover_ncsr_2021_2024_wave_bg.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="leftover_ncsr_2021_2024_wave_bi",
                url=(
                    "https://www.sec.gov/Archives/edgar/data/88048/"
                    "000008805325001134/ar103125dstf.htm"
                ),
                fixture="leftover_ncsr_2021_2024_wave_bi.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="leftover_ncsr_2021_2024_wave_bk",
                url=(
                    "https://www.sec.gov/Archives/edgar/data/793597/"
                    "000008805326000211/ar123125drgif.htm"
                ),
                fixture="leftover_ncsr_2021_2024_wave_bk.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="leftover_ncsr_2021_2024_wave_bn",
                url=(
                    "https://www.sec.gov/Archives/edgar/data/793597/"
                    "000008805325001132/ar103125dgsc.htm"
                ),
                fixture="leftover_ncsr_2021_2024_wave_bn.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="leftover_ncsr_2021_2024_wave_bo",
                url=(
                    "https://www.sec.gov/Archives/edgar/data/95603/"
                    "000008805325001130/ar103125dgib.htm"
                ),
                fixture="leftover_ncsr_2021_2024_wave_bo.html",
                live=False,
                role="history",
            ),
        ]
