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
        "2024 ICI / CG siblings 404 — not invented. "
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
        "or ICI secondary percentages."
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
                name="ici_secondary_hub",
                url=f"{forms}/2025_xtrackers_etfs_secondary_layout.pdf",
                fixture="ici_secondary_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
        ]
