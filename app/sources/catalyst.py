"""Catalyst Funds (catalystmf.com) open-end mutual-fund distribution adapter."""

from __future__ import annotations

from app.sources.html_source import HtmlTableSource, PageSpec


class CatalystSource(HtmlTableSource):
    slug = "catalyst"
    display_name = "Catalyst Funds"
    aum_rank = 113
    priority = 113
    notes = (
        "US open-end only (Mutual Fund Series Trust). Interval CSIOX omitted. "
        "Product census: https://catalystmf.com/ and "
        "https://catalystmf.com/api/data/catalyst-fund-data.js "
        "(16 open-end funds / 50 share-class tickers; Class C-1 MBXFX / CFRFX). "
        "Official 2025 annual distributions PDF "
        "https://catalystmf.com/docs/Other/2025%20Capital%20Gains%20Distributions.pdf "
        "(created 12/16/2025; record 12/12/2025; ex 12/15/2025; pay 12/16/2025) "
        "is the YE book: 24 paying classes ingested "
        "(CPEAX / CPEIX / CPECX LT $3.4499; CLTAX / CLTIX / CLTCX LT $1.5946; "
        "CLPAX / CLPFX / CLPCX LT $1.2262; CAXIX income $0.2482 / LT $1.0636; "
        "CAXAX income $0.2004 / LT $1.0636; CAXCX income $0.0521 / LT $1.0636; "
        "MLXAX / MLXIX / MLXCX LT $0.7840; CASAX / CASIX / CASCX LT $0.2419; "
        "SHIIX income $0.3285; SHIEX $0.3004; SHINX $0.2141; "
        "CWXIX income $0.2373; CWXAX $0.2115; CWXCX $0.1103). "
        "Printed dash / 0.0% ST+LT+income rows omitted "
        "(MBX* / EIX* / INS* / IIX* / ATR* / CFR* / TRX* / HII* / TRI* / CWE*). "
        "2024 / 2026 / estimate / ICI sibling URLs 404 — not invented. "
        "Literature Other/Misc is an admin-ajax SPA; Northern Lights / Ultimus "
        "distributor pages did not publish a Catalyst CG book this session. "
        "Monthly product-page income tables not densified. "
        "Growth of $X added for CPEAX."
    )
    live_limitations = (
        "Family book is PDF. Weekly walk uses the homepage product list, "
        "literature hub (SPA / admin-ajax Other/Misc), catalyst-fund-data.js, "
        "and the 2025 annual CG PDF. Empty/PDF-bytes/403 pages are no-op success. "
        "2024–2026 estimate / ICI sibling URLs 404. Do not invent amounts from "
        "the advisor-guide date schedule or all-dash PDF rows."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="home_products_hub",
                url="https://catalystmf.com/",
                fixture="home_products_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="literature_hub",
                url="https://catalystmf.com/literature-and-forms/",
                fixture="literature_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="fund_data_js",
                url="https://catalystmf.com/api/data/catalyst-fund-data.js",
                fixture="fund_data_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2025_annual_distributions",
                url="https://catalystmf.com/docs/Other/2025%20Capital%20Gains%20Distributions.pdf",
                fixture="2025_annual_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
        ]
