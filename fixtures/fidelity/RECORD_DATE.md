# Record date proof — Fidelity midyear estimates + Conestoga 2026 book

Eric: Record date is the shareholder-of-record gate. This file is the written
proof that the manager pages used for the live unpaid FBGRX-class rows (and
Conestoga CMIRX/CCALX) **do not publish** a Record / Record Date / Date of
Record field. `record_date` stays null. Do not invent from ex−1.

Checked 2026-09-10 against the live books (same amounts/dates as the fixtures).

## Fidelity (FBGRX / FBCVX / FDGFX and siblings)

**Estimate source (the book that produces these unpaid prelims):**

- https://institutional.fidelity.com/app/tabbed/products/FIIS_SP52_DPL6.html?navId=324
- Public clearing/custody mirror (same table; institutional host is Akamai-walled from some clients):
  https://clearingcustody.fidelity.com/app/tabbed/products/FIIS_SP52_DPL6.html

**Published columns (live + `estimated_capital_gains.html`):**

`Fund Name | Ex Date | Pay Date | NAV | % of NAV | Short-Term | Long-Term | Total Per Share | As of*`

There is no Record / Record Date / Date of Record column. Row cells for FBGRX
are Ex `09/11/2026`, Pay `09/14/2026`, As of `07/31/2026`. Same Ex/Pay/As-of
for FBCVX and FDGFX.

**Q&A (not a per-fund date feed):**

- https://www.fidelity.com/bin-public/060_www_fidelity_com/documents/mutual-funds/Cap-Gains-Q-A.pdf
- Institutional literature item 779188 (same Q&A)

The Q&A defines Record Date as “usually the business day prior to the
ex-dividend date” and states that **the Ex-Date and Pay Date are disclosed in
the table**. That glossary heuristic is not a published per-fund Record Date.

**Other Fidelity siblings checked:**

| Source | Record? |
| --- | --- |
| Prior-year paid DPL6 `FIIS_SP10_DPL6` (`prior_year_distributions.html`) | No — Fund / Ex Date / Pay Date / Reinvest NAV / Dividends / ST / LT / Total |
| Advisor estimate DPL2 `FIIS_SP52_DPL2_DSC1` (A/C/M/I/Z `shareClassId`) | No — same estimate columns as DPL6 |
| Advisor prior-year DPL2 `FIIS_SP10_DPL2_DSC1` (A/C/M/I/Z `shareClassId`) | No — same paid columns as DPL6 |
| Filled ICI Primary Layout for these fiscal estimates | Not published (blank ici.org templates are not a feed) |
| ETF Annual-Distribution-Calendar PDF | Yes, Record Date — **ETF schedule only**, not this mutual-fund estimate book |
| Retail distributions hub (`fidelity.com/mutual-funds/information/distributions`) | JS SPA; not a second column set |

**Re-harvest:** fixture parse of FIIS_SP52_DPL6 Sep 2026 unpaid rows is unchanged
(amounts/ex/pay/as_of already matched live 2026-09-10). `record_date` remains
null because the manager did not print one.

## Conestoga (CMIRX / CCALX)

**Estimate source:**

- https://conestogacapital.com/capital-gains-information/

Live 2026-09-10 copy: “estimated year-end distributions for the Conestoga Funds
as of July 31, 2026 … not final … Updated figures will be available in October.”

**Published columns:** Fund (all share classes) / Short-Term / Long-Term / Total.

No Record, Ex, or Payable column and no dated prose on the 2026 estimate page.
CCALX LT `$19.71` and CMIRX LT `$0.31` match the fixture. Dates stay null.

When Conestoga later posts finals with prose such as “record date of Tuesday,
December 2, 2025, and an ex-date of Wednesday, December 3, 2025,” the HTML
parser stores those **published** dates. That language is not on the current
estimate book, so it is not applied here.

## Before / after (API path)

| Ticker | Stage | as_of | ex_date | payable_date | record_date before | record_date after |
| --- | --- | --- | --- | --- | --- | --- |
| FBGRX | preliminary_estimate | 2026-07-31 | 2026-09-11 | 2026-09-14 | null | **null** (unpublished) |
| FBCVX | preliminary_estimate | 2026-07-31 | 2026-09-11 | 2026-09-14 | null | **null** (unpublished) |
| FDGFX | preliminary_estimate | 2026-07-31 | 2026-09-11 | 2026-09-14 | null | **null** (unpublished) |
| CMIRX | preliminary_estimate | 2026-07-31 | null | null | null | **null** (unpublished) |
| CCALX | preliminary_estimate | 2026-07-31 | null | null | null | **null** (unpublished) |

Parser change: `Record` / `Date of Record` / page-level “record date of &lt;date&gt;”
are recognized **when printed**. No ex−1 fallback.
