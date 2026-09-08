"""DWS / Xtrackers US ETF distribution adapter."""

from __future__ import annotations

from app.sources.html_source import HtmlTableSource, PageSpec


class DwsSource(HtmlTableSource):
    slug = "dws"
    display_name = "DWS / Xtrackers"
    aum_rank = 112
    priority = 112
    notes = (
        "US Xtrackers ETFs only (DBX Advisors). UCITS / Luxembourg books omitted. "
        "Tax hub: https://www.dws.com/en-us/resources/tax-center/ "
        "Official 2025 ICI Primary Layout "
        "https://www.dws.com/globalassets/cio/dam-us/pdfs/resources/tax-center/forms/"
        "2025-xtrackers-etfs-primary-layout.pdf "
        "(report date 01/13/2026) is the full US book: 42 listed tickers; "
        "205 non-zero income/ST rows ingested with official ex/pay dates "
        "(DBEF 6/20/2025 income $1.419 / 12/19/2025 $1.25062; "
        "HYLB monthly income e.g. 2/3/2025 $0.19723 / 12/22/2025 $0.20891; "
        "HDEF 6/20/2025 $0.63065; ASHR 12/19/2025 $0.75811; "
        "PSWD 12/5/2025 ST $0.15778). Printed $0.00 ICI lines omitted. "
        "ASHS and IND printed all-zero 2025 ICI rows — omitted, not stored as $0. "
        "2025 estimated CG PDF "
        "https://etf.dws.com/download/asset/9a1f54ed-fcf9-4b50-9d74-ae2343ee5bef "
        "lists the family; only PSWD printed a non-zero estimate (ST $0.1599). "
        "2025 final CG PDF "
        "https://www.dws.com/globalassets/cio/dam-us/pdfs/resources/tax-center/forms/"
        "xtrackers_etf_capital_gains.pdf "
        "confirms PSWD ST $0.1578 (matches ICI). Other printed $0.0000 CG omitted. "
        "2024 ICI / CG siblings 404 on the tax-center forms path — not invented. "
        "2026 dividend schedule "
        "https://etf.dws.com/en-us/etf-documents/dividend-schedules-2026/ "
        "has dates only (no per-share amounts). "
        "etf.dws.com product list is a JavaScript SPA — no public CSV/JSON product API. "
        "Growth of $X added for DBEF."
    )
    live_limitations = (
        "Family books are PDF. Weekly walk uses the DWS tax-center hub, "
        "2025 estimated CG PDF, 2025 final CG PDF, 2026 dividend-schedule hub, "
        "and etf.dws.com home (SPA). Empty/PDF-bytes pages are no-op success. "
        "2024 ICI primary URL 404s. Do not invent 2026 amounts from the date schedule."
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
                name="2025_estimated_capital_gains",
                url="https://etf.dws.com/download/asset/9a1f54ed-fcf9-4b50-9d74-ae2343ee5bef",
                fixture="2025_estimated_capital_gains.html",
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
                name="2025_final_capital_gains",
                url=f"{forms}/xtrackers_etf_capital_gains.pdf",
                fixture="2025_final_capital_gains.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="ici_primary_2025",
                url=f"{forms}/2025-xtrackers-etfs-primary-layout.pdf",
                fixture="ici_primary_2025.csv",
                live=False,
                parser="ici",
            ),
        ]
