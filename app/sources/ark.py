"""ARK Invest ETF distribution adapter."""

from __future__ import annotations

from app.sources.html_source import HtmlTableSource, PageSpec


class ArkSource(HtmlTableSource):
    slug = "ark"
    display_name = "ARK Invest"
    aum_rank = 114
    priority = 114
    notes = (
        "Official 2021 FINAL ordinary-income / capital-gain handout "
        "https://etfs.ark-funds.com/hubfs/1_Download_Files_ETF_Website/Distribution%20Files/"
        "ARKETFs_12021_Handout_Capital_Gains_Distribution_2021.pdf "
        "(ex 12/29/2021; record 12/30/2021; pay 12/31/2021). "
        "ARKK ST $0.5249 / LT $0.2577; ARKQ ST $0.3132 / LT $0.3010; "
        "ARKW ST $0.1962 / LT $3.1181; ARKG ST $0.3824; "
        "PRNT income $0.00057; IZRL $0.09558; CTRU $0.03136. "
        "Dashes omitted (ARKF / ARKX — not invented $0). "
        "2022 official FINAL states the sponsor does not expect distributions "
        "across the ETFs — no invented $0 rows. "
        "2023–2025 sibling PDFs were not on the ARK distribution library this wave. "
        "Hub: https://www.ark-funds.com/"
    )
    live_limitations = (
        "Family book is PDF. Weekly walk uses the ARK funds hub; empty/PDF-bytes "
        "pages are no-op success. 2022–2025 paid YE stay unmatched when unpublished."
    )

    def pages(self) -> list[PageSpec]:
        handout = (
            "https://etfs.ark-funds.com/hubfs/1_Download_Files_ETF_Website/"
            "Distribution%20Files/ARKETFs_12021_Handout_Capital_Gains_Distribution_2021.pdf"
        )
        return [
            PageSpec(
                name="tax_center_hub",
                url="https://www.ark-funds.com/",
                fixture="tax_center_hub.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="2021_final_distributions",
                url=handout,
                fixture="2021_final_distributions.html",
                live=False,
                role="history",
            ),
        ]
