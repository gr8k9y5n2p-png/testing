# Fund Distribution Estimates API

Backend service that ingests **taxable distribution estimates** published by fund managers and stores them in a searchable database for an Asset Management / Financial Advisor website.

The default demo uses **SQLite** and bundled Capital Group HTML fixtures so the pipeline runs offline. The same SQLAlchemy models work with **Postgres** by changing `DATABASE_URL`.

**Build, not buy.** This service ingests public manager HTML, ICI layout files, and PDF archives. It does not license CapGainsValet, YCharts, or other paid distribution feeds.

Historical packs prefer **ICI Primary Layout / PDF archives** over JavaScript SPA pages (Vanguard advisor year-end and product tables are SPAs; the official ICI PDFs on the tax center are the source of record for prior years).

**>$1B AUM filter.** When expanding *within* a family, historical rows are limited to funds identified as above **$1 billion AUM** — flagship Admiral / Investor classes and mega ETFs — plus locked compare heroes (`AMCPX`, `CGHM`, `TRBCX`, `VFIAX`, `VBIAX`, `FBGRX`). The allowlist lives in `app/sources/aum.py` (`LARGE_AUM_TICKERS`). It is not a live AUM feed. Micro share classes and synthetic parser samples stay out of multi-year packs. Illustrate/compare contracts are unchanged.

## What you get

- Normalized data model for distribution estimates (family, fund, ticker, share class, type, amount + unit, tax dates, source URL, raw JSON audit payload)
- `POST /ingest/distributions` for partner/manual feeds
- `POST /ingest/fetch` to run a pluggable `FundSource` adapter (`fixture` or `live`)
- `python -m app.cli refresh` for weekly all-family ingest (`REFRESH_MODE=auto`: live then fixture)
- Idempotent upserts on `(fund_family, fund identifier, share class, estimate type, as_of, ex-date)`
- Search API with filters, text search, and pagination
- `POST /illustrate` — server-side tax-impact math for a dollar holding (Website Engineering owns the UI)
- `POST /illustrate/portfolio` — book-level review with coverage % and explicit gaps
- `POST /illustrate/portfolio/compare` — Interactive Modules Current vs Proposed Allocation (single snapshot or YoY `periods[]`)
- `POST /illustrate/compare` — Interactive Modules chart contract (`fund_vs_fund` or `yoy`)
- Top-110 US-advisor fund-family adapters (`GET /fund-families`, `GET /coverage`) plus `POST /coverage/gaps` when a portfolio ticker is missing
- Partner ingest (`POST /ingest/distributions`) remains the escape hatch for uncovered names

## Quick start

Requires Python 3.12+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

mkdir -p data
python -m app.cli seed          # load fixtures and print a search example
python -m app.cli refresh --mode fixture   # weekly all-family ingest (offline)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open interactive docs at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### Docker

```bash
docker compose up --build
```

The API listens on port 8000. SQLite is stored in the `dist-data` volume.

## Example curl

```bash
# Health
curl -s http://127.0.0.1:8000/health | jq

# Fetch + parse American Funds fixtures (offline)
curl -s -X POST http://127.0.0.1:8000/ingest/fetch \
  -H 'Content-Type: application/json' \
  -d '{"fund_family":"american_funds","mode":"fixture"}' | jq '{created,updated,mode}'

# Re-run is idempotent (created=0, updated=N)
curl -s -X POST http://127.0.0.1:8000/ingest/fetch \
  -H 'Content-Type: application/json' \
  -d '{"fund_family":"american_funds","mode":"fixture"}' | jq '{created,updated}'

# Manual / partner ingest
curl -s -X POST http://127.0.0.1:8000/ingest/distributions \
  -H 'Content-Type: application/json' \
  -d @fixtures/american_funds/partner_feed.json | jq '{created,updated}'

# Search
curl -s 'http://127.0.0.1:8000/distributions?q=AMCAP&estimate_type=long_term_capital_gains' | jq
curl -s 'http://127.0.0.1:8000/distributions?ticker=CGHM' | jq
curl -s 'http://127.0.0.1:8000/distributions?ex_date_from=2026-06-01&ex_date_to=2026-06-30' | jq
# Multi-year / estimate-vs-actual (same fund_identifier, different as_of + publication_stage)
curl -s 'http://127.0.0.1:8000/distributions?fund_identifier=amcap-fund&as_of_from=2024-01-01&as_of_to=2024-12-31' | jq
curl -s 'http://127.0.0.1:8000/distributions?fund_identifier=amcap-fund&publication_stage=preliminary_estimate' | jq
curl -s 'http://127.0.0.1:8000/distributions?fund_identifier=amcap-fund&publication_stage=final' | jq
curl -s 'http://127.0.0.1:8000/fund-families' | jq
curl -s http://127.0.0.1:8000/coverage | jq '{implemented_count,implemented_pct,families:[.families[]|{slug,coverage_tier,aum_rank}]}'
curl -s -X POST http://127.0.0.1:8000/coverage/gaps \
  -H 'Content-Type: application/json' \
  -d '{"ticker":"XYZAX","fund_family":"dimensional","holding_dollars":150000}' | jq
curl -s http://127.0.0.1:8000/distributions/<id> | jq
```

`POST /ingest/fetch` with `"fund_family":"all"` runs every **implemented** adapter (all 110 registered families in fixture mode).

Live fetch (hits public Capital Group pages; may change or rate-limit):

```bash
curl -s -X POST http://127.0.0.1:8000/ingest/fetch \
  -H 'Content-Type: application/json' \
  -d '{"fund_family":"american_funds","mode":"live"}'
```

## Weekly refresh

More managers now publish **mid-year** (and other interim / special) capital-gains books to get ahead of tax season and limit year-end outflows. Weekly ingest is how those paid midyear amounts land before the year-end preliminary estimates — midyear is first-class, not an off-season afterthought.

Adapters prefer verified midyear / special / interim pages when they exist (Capital Group `midyear-cap-gains`, iShares mid-year + year-end tables, Columbia Threadneedle mid-year estimate PDF, Davis semi-annual rows, Allspring product-alerts as the watch hub). `publication_stage` keeps the books apart so `/illustrate` and compare do not treat a June paid amount as a YE preliminary.

```bash
# Production default (REFRESH_MODE=auto): live HTML where the adapter supports it,
# fixture fallback on 403 / SPA / empty parse / PDF-only families.
python -m app.cli refresh

# Offline / CI
python -m app.cli refresh --mode fixture

# One family
python -m app.cli refresh --mode auto --family american_funds

# JSON + Markdown summaries (used by GitHub Actions)
python -m app.cli refresh --output refresh-summary.json --markdown refresh-summary.md
```

`REFRESH_MODE` (`auto` | `live` | `fixture`, default `auto`) is the env default; `--mode` overrides it.

| Mode | Behavior |
| --- | --- |
| `auto` | Try `live` only when the adapter has scrapeable HTML (`supports_live()`). PDF-only families go straight to fixtures. Live HTTP/parse failure → fixture, logged as `fallback`. |
| `live` | Try live first for every family, then fixture on failure. |
| `fixture` | Bundled HTML only (no outbound HTTP). |

The command is the `POST /ingest/fetch` `fund_family=all` path with per-family error isolation. Upserts stay **idempotent**: the same document (`as_of` + ex-date + estimate type) updates the existing row; a new `as_of` inserts a new snapshot. Exit code is `0` on partial live fallbacks. Exit `1` only when **every** attempted family hard-fails (live and fixture both error).

The JSON / Markdown summary breaks out **midyear vs year-end** created/updated when a row is detectable from the source URL (`midyear`, `mid-year`, `interim`, `semi-annual`, `year-end`) or from `as_of` / `ex_date` month (May–August vs October–January). Unclassified months (for example September) are counted only in the overall created/updated totals.

Live pages often 403, challenge, or render as a JS/SPA shell and parse 0 rows. That is expected for a large share of the top 110 — fixture fallback is the documented recovery, not a job failure.

### GitHub Actions

`.github/workflows/weekly-ingest.yml`:

- Schedule: Mondays at **14:00 UTC** (about 9am America/Chicago)
- Manual: **Actions → Weekly ingest refresh → Run workflow** (`workflow_dispatch`), optional `refresh_mode`
- Installs `requirements-dev.txt`, uses SQLite unless a `DATABASE_URL` repo secret is set (then Postgres + `psycopg2-binary`)
- Writes `refresh-summary.json` / `refresh-summary.md`, appends the Markdown to the job summary, and uploads both as the `weekly-ingest-summary` artifact

## Tax illustration (`POST /illustrate`)

Website Engineering renders the UI; this API owns the math. Pass a holding value plus either `distribution_ids` or `selectors`. **Every tax rate is request-overridable**; omitted fields use the documented defaults below (illustrative top federal brackets + a sample state rate — not tax advice).

### Defaults (when a field is omitted)

| Field | Default | Meaning |
| --- | --- | --- |
| `ordinary_income` | `0.37` | Top federal ordinary |
| `long_term_capital_gains` | `0.20` | Top federal LTCG |
| `short_term_capital_gains` | `0.37` | STCG taxed as ordinary; overridable independently |
| `qualified_dividend` | `0.20` | QDI (same default as LTCG) |
| `return_of_capital` | `0` | Typically not currently taxable |
| `state` | `0.05` | Sample state marginal |

`combine_state_with_federal` (default `true`): `applied_rate = federal + state`. When `false`, federal and state tax are computed separately and summed in `estimated_tax`.

### `estimate_type` → rate field

| `estimate_type` | Rate used |
| --- | --- |
| `ordinary_income` | `ordinary_income` |
| `special_dividend` | `ordinary_income` |
| `other` | `ordinary_income` (conservative) |
| `total` | `ordinary_income` (unspecified total) |
| `short_term_capital_gains` | `short_term_capital_gains` |
| `long_term_capital_gains` | `long_term_capital_gains` |
| `total_capital_gains` | `long_term_capital_gains` (unsplit CG treated as LTCG) |
| `qualified_dividend` | `qualified_dividend` |
| `qualified_short_term_gains` | `qualified_dividend` |
| `return_of_capital` | `return_of_capital` |

The mapping is also echoed on the response as `rate_mapping`.

### Amount units

| `amount_unit` | Dollar math |
| --- | --- |
| `percent_of_nav` | `distribution_dollars = holding_dollars * (amount / 100)`; `amount_min` / `amount_max` produce range fields |
| `per_share` | `shares = shares` or `holding_dollars / nav_per_share`; `distribution_dollars = shares * amount`. **HTTP 422** if neither `nav_per_share` nor `shares` is provided |
| `percent` | **Not a dollar distribution** (e.g. QDI % of income on 1099-DIV). Component is returned with `estimated_tax: null`, `included_in_totals: false`, and `skip_reason` |

Selector queries default to `latest_as_of_only=true` so September estimates and January finals are not double-counted. Pass `as_of` or explicit IDs to pin a snapshot.

```bash
# $1,000,000 AMCAP-style % of NAV estimate with custom rates
# (run ingest/fetch first so amcap-fund exists)
curl -s -X POST http://127.0.0.1:8000/illustrate \
  -H 'Content-Type: application/json' \
  -d '{
    "holding_dollars": 1000000,
    "selectors": {
      "fund_family": "American Funds",
      "fund_identifier": "amcap-fund",
      "as_of": "2025-09-19"
    },
    "tax_rates": {
      "ordinary_income": 0.35,
      "long_term_capital_gains": 0.15,
      "short_term_capital_gains": 0.35,
      "qualified_dividend": 0.15,
      "state": 0.093
    },
    "combine_state_with_federal": true
  }' | jq '{totals, tax_rates, components: [.components[] | {estimate_type, amount_unit, distribution_dollars, distribution_dollars_min, distribution_dollars_max, applied_rate, estimated_tax}]}'

# Per-share paid amount (needs NAV)
curl -s -X POST http://127.0.0.1:8000/illustrate \
  -H 'Content-Type: application/json' \
  -d '{
    "holding_dollars": 1000000,
    "selectors": {"fund_identifier": "amcap-fund", "as_of": "2026-07-08"},
    "nav_per_share": 80,
    "tax_rates": {"long_term_capital_gains": 0.20, "state": 0.05}
  }' | jq .totals
```

Expected for the $1M / 3–5% AMCAP example at 15% LTCG + 9.3% state: midpoint 4% → `$40,000` distributed, `$9,720` tax; range `$30,000–$50,000` / `$7,290–$12,150`.

### Portfolio review (`POST /illustrate/portfolio`)

Aftertax sends a book of holdings. The API reuses single-holding math, then rolls up **portfolio totals**, **coverage by dollars**, and **explicit gaps** (never silently drop an uncovered ticker).

`snapshot.prefer_publication_stages` walks that order and keeps the first stage that has rows for the holding (default: preliminary → updated → final → paid). Pin `snapshot.as_of` for a historical book. Missing `nav_per_share` on `per_share` rows is a **warning**, not a 422 — those components are excluded from dollar totals.

```bash
curl -s -X POST http://127.0.0.1:8000/illustrate/portfolio \
  -H 'Content-Type: application/json' \
  -d '{
    "holdings": [
      {"ticker": "CGHM", "holding_dollars": 250000},
      {"fund_identifier": "amcap-fund", "fund_family": "American Funds", "holding_dollars": 1000000},
      {"ticker": "XYZAX", "fund_family": "dimensional", "holding_dollars": 150000}
    ],
    "tax_rates": {
      "ordinary_income": 0.37,
      "long_term_capital_gains": 0.20,
      "short_term_capital_gains": 0.37,
      "qualified_dividend": 0.20,
      "state": 0.05
    },
    "combine_state_with_federal": true,
    "snapshot": {
      "prefer_publication_stages": ["preliminary_estimate", "updated_estimate", "final", "paid"]
    }
  }' | jq '{coverage, gaps, totals, warnings, holdings: [.holdings[] | {ticker, fund_identifier, covered, publication_stage_used, upcoming, gap_reason, warnings}]}'
```

On the American Funds fixtures: $1.25M covered / $150k uncovered → `coverage_pct` ≈ 89.3%. AMCAP uses the latest preliminary (3–5% NAV → $40,000 / $10,000 tax at 20%+5%). Each covered holding with distribution dollars also gets `upcoming: {distribution_dollars, estimated_tax, as_of, publication_stage}` from that chosen illustration (`null` on gaps or when dollars are zero — e.g. CGHM without NAV). `XYZAX` is a gap.

Holdings may send **`holding_dollars`** or **`weight_pct` + `book_dollars`**. `weight_pct` is Interactive Modules UI percent **0–100** (`25` = 25% of book; `1` = 1%). The server sets `holding_dollars = book_dollars × weight_pct / 100`.

### Current vs Proposed (`POST /illustrate/portfolio/compare`)

Interactive Modules **Current Allocation vs Proposed Allocation**. Same center-zero bars as fund compare, but each series is **Proposed − Current**.

**Single snapshot** (omit `periods`): one shared `snapshot` + `tax_rates`. **YoY** (send `periods[]`, e.g. `[{year:2024,as_of:…},{year:2025,as_of:…}]`): each period re-runs both books with that `as_of` pinned, or a calendar-year window when `as_of` is omitted (`snapshot.as_of_year`). Top-level `current` / `proposed` / `deltas` **copy the latest period** so the diverging-bar sketch still has one pair. `periods[]` is empty in single-snapshot mode.

Each holding sends `ticker` and/or `fund_identifier`, and **either** `holding_dollars` **or** `weight_pct` plus the side’s `book_dollars`. `weight_pct` is **0–100** (UI %). Capital Group HTML has no ticker column: `AMCPX` / `AMCAP` resolve to stored `amcap-fund`; `AGTHX` resolves to `the-growth-fund-of-america`.

Each side is a full `/illustrate/portfolio` result plus `label` (defaults: `Current Allocation` / `Proposed Allocation`). Gaps stay on that side. Covered holdings include `upcoming` (same convenience field as `/illustrate/portfolio`).

**Sign convention:** `deltas` are **proposed − current**.

| Field | Meaning |
| --- | --- |
| `current` / `proposed` | Full `PortfolioIllustrateResponse` + `label` (latest period when YoY) |
| `periods[]` | YoY rows: `{year, as_of, current, proposed, deltas}` |
| `deltas.estimated_tax` | Dollar tax delta |
| `deltas.distribution_dollars` | Dollar distribution delta |
| `deltas.effective_tax_on_holding` | Rate delta (chart field) |
| `deltas.coverage_pct` | Coverage-percentage points |
| `summary` | Dollar fields at **$10,000**. YoY also sets `total_tax_difference`, `annualized_tax_drag_delta`, `distribution_dollars_difference`, `periods_compared`, `common_inception` (same footer idea as `/illustrate/compare`) |

**Sparse history:** Dodge & Cox is still one vintage. Vanguard now has ICI December year-end rows for 2022–2024 (VFIAX / VBIAX / VIGAX) plus the 2025 YE fixture. Fidelity has 2025 paid + 2026 estimate (FBGRX). A YoY `periods[]` pin that misses that `as_of` / year is an explicit **gap** on that side, not a silent $0. American Funds (AMCAP 2024–2025) and T. Rowe Price (TRBCX 2022–2025) have multi-year fixture snapshots.

```bash
curl -s -X POST http://127.0.0.1:8000/illustrate/portfolio/compare \
  -H 'Content-Type: application/json' \
  -d '{
    "current": {
      "label": "Current Allocation",
      "book_dollars": 1000000,
      "holdings": [
        {"ticker": "CGHM", "weight_pct": 25},
        {"ticker": "FBGRX", "holding_dollars": 250000},
        {"ticker": "AMCPX", "fund_identifier": "amcap-fund", "weight_pct": 50}
      ]
    },
    "proposed": {
      "label": "Proposed Allocation",
      "book_dollars": 1000000,
      "holdings": [
        {"ticker": "CGHM", "holding_dollars": 150000},
        {"ticker": "VFIAX", "weight_pct": 40},
        {"ticker": "VBIAX", "weight_pct": 20},
        {"ticker": "TRBCX", "weight_pct": 25}
      ]
    },
    "tax_rates": {},
    "combine_state_with_federal": true,
    "snapshot": {}
  }' | jq '{notes, deltas, summary, current: {label: .current.label, coverage: .current.coverage, gaps: .current.gaps}, proposed: {label: .proposed.label, coverage: .proposed.coverage}}'
```

Hero tickers used in tests: `AMCPX` / `AMCAP` / `amcap-fund`, `AGTHX` / `the-growth-fund-of-america`, `CGHM`, `TRBCX`, `VFIAX`, `VBIAX`, `VIGAX`, `FBGRX`, `DODIX`.

Eric’s beta Current book (`AGTHX` / `DODIX` / `AMCAP` / `VIGAX` at 25%): `AMCAP` and `AGTHX` are ticker aliases onto AF name slugs. `DODIX` is paid 2025 ordinary income from the Dodge Supplemental Tax Letter (Q1 2026 estimate PDF does not list Income — no estimated capital gain). `VIGAX` is 2025 year-end income `$0.251100` from the public Vanguard product distribution table (no 2025 capital-gain row).

YoY example (same books, two `as_of` pins):

```bash
curl -s -X POST http://127.0.0.1:8000/illustrate/portfolio/compare \
  -H 'Content-Type: application/json' \
  -d '{
    "current": {
      "label": "Current Allocation",
      "book_dollars": 1000000,
      "holdings": [{"fund_identifier": "amcap-fund", "weight_pct": 100}]
    },
    "proposed": {
      "label": "Proposed Allocation",
      "book_dollars": 1000000,
      "holdings": [
        {"fund_identifier": "amcap-fund", "weight_pct": 50},
        {"ticker": "CGHM", "weight_pct": 50}
      ]
    },
    "tax_rates": {},
    "periods": [
      {"year": 2024, "as_of": "2024-12-15"},
      {"year": 2025, "as_of": "2025-09-19"}
    ]
  }' | jq '{summary, periods: [.periods[] | {year, as_of, deltas}]}'
```

### Compare chart (`POST /illustrate/compare`)

Interactive Modules plots **one series per period**. The primary chart field is `periods[].deltas.effective_tax_on_holding`. Dollar deltas (`distribution_dollars`, `estimated_tax`, `federal_tax`, `state_tax`, plus `_min`/`_max` when a side published a range) stay in the payload.

**Sign convention:** every delta is **right − left** (B − A). A positive `effective_tax_on_holding` means the right series costs more tax as a fraction of the holding.

`tax_rates: {}` is valid — omitted keys use the same defaults as `POST /illustrate`.

**`mode: "fund_vs_fund"`** — two funds, same `holding_dollars` / rates, one illustration pair per `periods[]` entry. Each period’s `as_of` is pinned onto both sides.

```bash
curl -s -X POST http://127.0.0.1:8000/illustrate/compare \
  -H 'Content-Type: application/json' \
  -d '{
    "mode": "fund_vs_fund",
    "holding_dollars": 1000000,
    "tax_rates": {},
    "combine_state_with_federal": true,
    "left": { "label": "Fund A", "selectors": { "fund_identifier": "amcap-fund" } },
    "right": { "label": "Fund B", "selectors": { "ticker": "CGHM" } },
    "periods": [
      { "year": 2024, "as_of": "2024-12-15" },
      { "year": 2025, "as_of": "2025-09-19" }
    ]
  }' | jq '{mode, notes, periods: [.periods[] | {year, as_of, left: .left.label, right: .right.label, deltas}]}'
```

**`mode: "yoy"`** — two vintages of the **same** fund. Either:

- one `selectors` (or `left.selectors`) block plus `periods` of length ≥ 2 — consecutive pairs; the response `year` / `as_of` are the **newer** (right) vintage, or
- `left` / `right` with the same selectors and different `as_of` (no `periods` required).

`mode` may be omitted: the same fund on both sides infers `yoy`; different funds infer `fund_vs_fund`. A single-pair response also copies `left`, `right`, and `deltas` to the **top level** (diverging-bar sketch). Each side may override `holding_dollars` / `nav_per_share` / `shares`.

YoY AMCAP (defaults: 20% LTCG + 5% state → 2024 $20k / $5k tax vs 2025 $40k / $10k tax):

```bash
curl -s -X POST http://127.0.0.1:8000/illustrate/compare \
  -H 'Content-Type: application/json' \
  -d '{
    "holding_dollars": 1000000,
    "nav_per_share": null,
    "tax_rates": {},
    "combine_state_with_federal": true,
    "left": { "label": "2024", "selectors": { "fund_identifier": "amcap-fund", "as_of": "2024-12-15" } },
    "right": { "label": "2025", "selectors": { "fund_identifier": "amcap-fund", "as_of": "2025-09-19" } }
  }' | jq '{mode, left: .left.label, right: .right.label, deltas, notes}'
```

A missing side is **not** a 404. That illustration is empty (zeros, `matched: false`) and a note is appended so the chart still has a period row.

Top-level or per-side `nav_per_share` / `shares` apply the same way as single-holding illustrate.

**`summary` (React footer v1, always at $10,000)**

Dollar fields are scaled linearly from the request holding: `value_at_10k = value × (10000 / holding_dollars)`. Tax-drag rates are already fractions of the holding, so they are **not** rescaled. Estimate min/max ranges stay on `periods[].deltas` only — they are not on `summary`.

| Footer slot | Field |
| --- | --- |
| 1 — tax $ Δ | `summary.total_tax_difference` |
| 2 — annualized tax drag Δ | `summary.annualized_tax_drag_delta` |
| 3 — distribution $ Δ | `summary.distribution_dollars_difference` |
| 4 — upcoming taxable $ | `summary.upcoming_taxable_distribution` |

| Field | Meaning |
| --- | --- |
| `normalized_holding_dollars` | Always `10000` |
| `total_tax_difference` | Σ `periods[].deltas.estimated_tax` × scale (right − left) |
| `distribution_dollars_difference` | Σ `periods[].deltas.distribution_dollars` × scale |
| `annualized_tax_drag_delta` | Arithmetic mean of `periods[].deltas.effective_tax_on_holding` |
| `periods_compared` | Number of period rows in the response |
| `common_inception` | `from_year` / `from_as_of` → `to_year` / `to_as_of` of the compared window |
| `upcoming_taxable_distribution` | This calendar year’s upcoming taxable $ on $10k, or `null` |

`upcoming_taxable_distribution` (slot 4) looks up **current calendar year** rows for each side (selectors without the period `as_of` pin). Among `preliminary_estimate` and `updated_estimate`, it keeps the **latest `as_of`**. **Paid is ignored** — including midyear paid amounts — so a June ex-date does not masquerade as the year-end preliminary. `final` is used only when that year has no estimate. Same-day updated + preliminary prefers `updated_estimate`.

| Slot 4 field | Meaning |
| --- | --- |
| `left_dollars` / `right_dollars` | Upcoming taxable $ on $10k (`null` if that side has no current-year row) |
| `delta_dollars` | right − left (missing side treated as $0) |
| `left_as_of` / `right_as_of` | Publication `as_of` used |
| `left_publication_stage` / `right_publication_stage` | Stage used |

If neither side has current-year upcoming data the object is `null` and a note is added.

## Multi-year history and estimate → actual

The upsert key includes `as_of` and `ex_date`, so a September preliminary, a December update, and a January final are **separate rows**. Do not collapse them.

`GET /distributions` already supports `as_of_from` / `as_of_to`, `publication_stage`, and `fund_identifier` (exact slug or ticker identity).

**Compare estimate vs paid for one fund:**

1. `GET /distributions?fund_identifier=amcap-fund&publication_stage=preliminary_estimate` — % of NAV ranges (often `total_capital_gains`).
2. `GET /distributions?fund_identifier=amcap-fund&publication_stage=final` — year-end per-share LTCG/STCG.
3. `GET /distributions?fund_identifier=amcap-fund&as_of_from=2024-01-01&as_of_to=2024-12-31` — one tax year’s publication window.
4. Units differ (`percent_of_nav` vs `per_share`); convert with NAV before subtracting. Illustration uses `as_of` or `prefer_publication_stages` so you do not add estimate + final.

Fixture packs today (ranks 1–10 historical pass):

| Family | Years in fixtures | Live archive notes |
| --- | --- | --- |
| BlackRock / iShares | 2026 midyear paid + 2025 YE final | Live HTML https://www.ishares.com/us/capital-gains-distributions. 2023–2024 archives are 1099-style PDF tax kits (not an HTML CG grid) — skipped, not invented. 2024 kit: https://www.ishares.com/us/library/2024-tax-kit |
| Vanguard | 2022–2024 ICI December YE (VFIAX / VBIAX / VIGAX) + 2025 YE HTML | ICI Primary Layout PDFs on the advisor tax center (not SPA scrape). December-only / >$1B filter. 2025 ICI not double-ingested (existing YE fixture). |
| Fidelity | 2025 prior-year paid + 2026 estimate | Live HTML: current estimates `FIIS_SP52_DPL6` and prior-year `FIIS_SP10_DPL6` (FBGRX 2025 paid LT $5.07300 ex 2025-09-12; 2026 estimate LT $21.021 as of 2026-07-31). |
| State Street / SPDR | 2025 estimate (SPY/SPLG 0% NAV placeholder) | Angular live page. Historical XLSX is linked but not a stable public file URL — 2024 paid ST/LT not transcribed. ZZSSGA is a parser-layout sample, not official. |
| J.P. Morgan | 2025 Section 19a sample (SEEGX) | No confirmed official 2024 $/share 19a PDF/HTML. Third-party histories unused. |
| Goldman Sachs | 2025 sample (GLCGX) | Advisor tax center 403-walled; no public historical HTML. |
| American Funds | 2024 prelim + 2024 final, 2025 prelim + 2025 final, 2026 midyear paid | 2025 YE + 2026 midyear HTML are public. 2024 advisor YE URL 302s to login (transcribed fixture). Official 2024 YE lists CGHM with em-dash ST/LT (no CG — not stored as $0). Per-fund tool: https://www.capitalgroup.com/individual/investments/historicaldistributions/ |
| PIMCO | Layout sample only (ZZPIMI / ZZPIMB) | No public HTML estimate grid. No additional years invented. |
| Invesco | 2024 estimate + 2025 estimate | 2025 PDF + 2024 In Focus page (as of 2024-09-30; American Franchise LT $0.93). Live PDF/contentdetail is not HTML-parsed. |
| T. Rowe Price | 2022 prelim + 2022–2025 YE | 2023–2025 HTML (same path, year in the filename). 2022 YE + 2022 prelim are official PDFs (TRBCX LT $6.0394 final / $5.75 prelim). |

## Data model

Each stored row is one estimate **component** (a fund can have long-term and short-term rows).

| Field | Notes |
| --- | --- |
| `fund_family` | Manager name, e.g. `American Funds` |
| `fund_name` | Cleaned legal/marketing name |
| `ticker` / `cusip` / `share_class` | Optional; tickers are taken from `TICKER — Fund name` when present |
| `fund_identifier` | Ticker if known, otherwise a slug of the fund name (upsert identity) |
| `estimate_type` | `ordinary_income`, `short_term_capital_gains`, `long_term_capital_gains`, `total_capital_gains`, `total`, `qualified_dividend`, `qualified_short_term_gains`, `special_dividend`, `return_of_capital`, `other` |
| `amount` / `amount_min` / `amount_max` | Midpoint plus range when the source publishes a band |
| `amount_unit` | `per_share`, `percent_of_nav`, or `percent` (qualified-dividend %) |
| `record_date`, `ex_date`, `payable_date` | When published |
| `as_of` | Page publication date (Capital Group `meta name=date`) |
| `publication_stage` | `preliminary_estimate`, `updated_estimate`, `final`, `paid`. Midyear **estimate** books (Columbia `mid-year-cap-gain-estimates`) stay `preliminary_estimate` / `updated_estimate`. Midyear **paid** / special / interim / semi-annual amounts (Capital Group `midyear-cap-gains`, iShares mid-year table, Davis June rows) map to `paid`. Year-end HTML/PDF maps to `final` (or the matching estimate stage). |
| `source_url` | Page or partner URL |
| `raw_payload` | Original row/page context for audit (list endpoints omit it unless `include_raw=true`) |
| `ingested_at` | Server timestamp of last upsert |

Re-running the **same** source document updates the existing row. A new `as_of` (September preliminary vs December update vs January final) inserts a new snapshot.

## Coverage (portfolio review)

Sparse family coverage makes Aftertax-style portfolio analytics wrong: a book that is 40% Vanguard / iShares / Fidelity looks like it has no taxable distributions if those adapters are stubs. The registry is the **top 110 US-advisor-relevant firms** (AUM ranks 1–110). `GET /coverage` returns `implemented_pct` (today 110/110 fixture parsers) so the website can later compute *% of portfolio dollars covered*.

`GET /fund-families` includes `coverage_tier` (`implemented` | `stub`), `aum_rank` (1 = largest / highest priority), and `priority`.

When a holding’s ticker or family is not in the store, Website Engineering should call `POST /coverage/gaps` with `{ticker or fund_name, fund_family?, holding_dollars?}`. The API logs the gap in SQLite and returns:

| `suggested_next_step` | Meaning |
| --- | --- |
| `fetch_adapter` | A registered parser exists — run `POST /ingest/fetch` for that slug, then search. If the ticker is still missing, partner-ingest the row. |
| `queued` | Slug is registered but not implemented (none of the top 110 today). |
| `manual_ingest` | Unknown family — `POST /ingest/distributions` is the escape hatch. |

| Rank | Slug | Display name | Parser | Live HTML | Public source (verified 2026-09-07) |
| --- | --- | --- | --- | --- | --- |
| 1 | `blackrock` (alias `ishares`) | BlackRock / iShares | implemented | yes | https://www.ishares.com/us/capital-gains-distributions |
| 2 | `vanguard` | Vanguard | implemented | JS SPA + ICI PDF fixtures | YE SPA + ICI Primary Layout PDFs under `/content/dam/fas/pdfs/` |
| 3 | `fidelity` | Fidelity | implemented | yes (estimates + prior-year) | https://institutional.fidelity.com/app/tabbed/products/FIIS_SP52_DPL6.html?navId=324 ; prior-year `FIIS_SP10_DPL6` |
| 4 | `state_street` (aliases `spdr`, `ssga`) | State Street / SPDR | implemented | Angular — fixture fallback | https://www.ssga.com/us/en/individual/resources/documents/etf-capital-gain-distributions |
| 5 | `jpmorgan` (alias `jpm`) | J.P. Morgan AM | implemented | PDF / no HTML grid | Section 19a PDFs under am.jpmorgan.com `.../section-19-notices/` |
| 6 | `goldman_sachs` (aliases `gs`, `gsam`) | Goldman Sachs AM | implemented | 403 / PDF library | https://www.gsam.com/content/gsam/us/en/advisors/literature-and-forms/forms-and-tax-center.html |
| 7 | `american_funds` (alias `capital_group`) | American Funds | implemented | yes | Capital Group individual tax center (see below) |
| 8 | `pimco` | PIMCO | implemented | PDF / notices | https://www.pimco.com/us/en/resources/tax-center |
| 9 | `invesco` | Invesco | implemented | PDF + PR (2024–2025 fixtures) | 2025 PDF + 2024 In Focus `contentId=29096ee0-8ec4-4199-930f-645be9d07e64` |
| 10 | `t_rowe_price` (alias `trp`) | T. Rowe Price | implemented | yes (2023–2025 HTML; 2022 PDF) | https://www.troweprice.com/personal-investing/resources/planning/tax/dividend-distributions/mutual-funds/2025-year-end-distributions.html |
| 11 | `ubs` | UBS Asset Management | implemented | price-page HTML / PDF | https://www.ubs.com/us/en/assetmanagement/funds/mutual-fund-price.html (paid PWTAX); estimate PDF from the mutual-fund product hub |
| 12 | `franklin_templeton` (aliases `franklin`, `templeton`, `putnam`) | Franklin Templeton | implemented | JS SPA + 19(a) PDF | https://www.franklintempleton.com/tools-and-resources/tax-center ; CEF 19(a) e.g. `.../ft-section-19-notice-12-31-2025` |
| 13 | `bny_mellon` (aliases `bny`, `dreyfus`) | BNY Mellon / Dreyfus | implemented | PDF | https://www.bny.com/assets/investments/im/documents/manual/tax-forms/2025-Estimated-capital-gains.pdf |
| 14 | `nuveen` (alias `tiaa`) | Nuveen / TIAA | implemented | PDF viewer | https://documents.nuveen.com/Documents/Nuveen/Default.aspx?uniqueId=3c3be13d-d800-48e2-a537-c251162ab9f4 |
| 15 | `northern_trust` (aliases `nt`, `ntam`) | Northern Trust | implemented | PDF | https://ntam.northerntrust.com/content/dam/ntam/us/en/documents/account-resources/tax-center/all-investor/estimated-capital-gains-2025.pdf |
| 16 | `morgan_stanley` (aliases `msim`, `ms`) | Morgan Stanley IM | implemented | PDF (often Akamai-walled) | https://www.morganstanley.com/im/publication/forms/tax/2025_etf_year_end_distributions.pdf |
| 17 | `schwab` (alias `charles_schwab`) | Charles Schwab IM | implemented | JS family page; product HTML | https://www.schwabassetmanagement.com/resource/schwab-funds-actual-annual-distributions-2025 |
| 18 | `dimensional` (alias `dfa`) | Dimensional | implemented | PDF | https://www.dimensional.com/chmedia/440098/source/download/2025-capital-gain-distribution-estimates.pdf |
| 19 | `columbia_threadneedle` (aliases `columbia`, `ameriprise`) | Columbia Threadneedle | implemented | PDF | https://www.columbiathreadneedleus.com/binaries/content/assets/cti/public/2025-mid-year-cap-gain-estimates-all-funds.pdf |
| 20 | `amundi` (alias `pioneer`) | Amundi US / Pioneer | implemented | PDF | https://pioneerinvestments.com/content/dam/pioneer/en/documents/resources/tax-center/2025/10152025-mutual-funds-2025-capital-gain-estimates.pdf |
| 21 | `allspring` (aliases `wells_fargo`, `wfam`) | Allspring | implemented | product-page HTML / gated PDF | https://www.allspringglobal.com/resources/product-alerts/ ; paid history e.g. `.../special-mid-cap-value/` |
| 22 | `janus_henderson` (alias `janus`) | Janus Henderson | implemented | PDF | https://www.janushenderson.com/en-us/advisor/annual-distributions-supplemental-tax-documents-mutual-funds/ ; 2025 estimates on the rackcdn `distribution-tax` path |
| 23 | `american_century` | American Century | implemented | JS hub + PDF | https://res.americancentury.com/docs/estimated-distributions-november-retail.pdf |
| 24 | `dodge_cox` (aliases `dodge`, `dodgx`) | Dodge & Cox | implemented | PDF | https://www.dodgeandcox.com/content/dam/dc/us/en/pdf/dc-us-estimated-distributions-1Q2026.pdf (DODIX not listed). Paid 2025 DODIX income: `.../dc_us_supplemental_tax_letter.pdf` |
| 25 | `mfs` | MFS Investment Management | implemented | PDF | https://www.mfs.com/content/dam/mfs-enterprise/mfscom/backlot/mfs_cg_fly.pdf |
| 26 | `lord_abbett` (alias `lord`) | Lord Abbett | implemented | PDF (no-pay list) | https://www.lordabbett.com/content/dam/lordabbett-captivate/documents/TaxCenter/UnitedStates/Funds-with-Losses.pdf |
| 27 | `ab` (aliases `alliancebernstein`, `alliance_bernstein`) | AllianceBernstein | implemented | PDF | https://www.alliancebernstein.com/content/dam/alliancebernstein/us-retail/us-retail-pdfs/tax-center/Final_GEN-5796-1025.pdf |
| 28 | `federated_hermes` (alias `federated`) | Federated Hermes | implemented | JS tax center + 19(a) PDF | https://www.federatedhermes.com/siteassets/documents/regulatory/19a-notices/g85307-06.pdf |
| 29 | `virtus` | Virtus | implemented | PDF | https://www.virtus.com/assets/files/abi/cap_gains_estimate_6-26_8569.pdf |
| 30 | `eaton_vance` (alias `ev`) | Eaton Vance | implemented | CEF 19(b) PDF | https://www.eatonvance.com/content/dam/im/assets/publication/thought-leadership/press-release/combined19bpressreleasemarch2025.pdf |
| 31 | `john_hancock` (aliases `manulife`, `jh`) | John Hancock / Manulife | implemented | PDF | https://www.jhinvestments.com/content/dam/jhi-investments/JHINV/public/Corporate/News/CorporatePressReleases/estimated-capital-gain-and-income-distribution-press-release-2025-jhi.pdf |
| 32 | `principal` | Principal | implemented | product-page HTML / viewer PDF | https://www.principalam.com/us/fund/pqiax ; tax hub https://www.principal.com/help/help-individuals/tax-center/dividends-capital-gains-distributions |
| 33 | `thrivent` | Thrivent | implemented | yes | https://www.thriventfunds.com/support/tax-resource-center/capital-gains.html |
| 34 | `hartford` | Hartford Funds | implemented | PDF | https://www.hartfordfunds.com/dam/en/docs/pub/funddocuments/regulatorydocument/Tax%20Center/HMFCapitalGains_December2025EstimateMemo.pdf |
| 35 | `macquarie` (aliases `delaware`, `delaware_funds`) | Macquarie / Delaware Funds | implemented | PDF | https://mim.fgsfulfillment.com/download.aspx?sku=CGE-RET |
| 36 | `first_eagle` (alias `fei`) | First Eagle | implemented | PDF | https://www.firsteagle.com/sites/default/files/fei-documents/FEF_Ordinary_Income_Gains_Estimates.pdf |
| 37 | `gmo` | GMO | implemented | PDF | https://www.gmo.com/globalassets/documents---manually-loaded/documents/distribution-estimates-and-dates/gmo-trust-funds---july-2026-distribution-estimate.pdf |
| 38 | `artisan` (alias `artisan_partners`) | Artisan Partners | implemented | paid HTML / no estimate PDF | https://www.artisanpartners.com/individual-investors/resources/tax-center/distributions.html |
| 39 | `calamos` | Calamos | implemented | PDF | https://www.calamos.com/globalassets/media/documents/tax-center/2025-calamos-estimated-capital-gains.pdf |
| 40 | `wasatch` | Wasatch | implemented | PDF | https://wasatchglobal.com/wp-content/uploads/2025/11/WGI_2025_Yr_End_Dist_Estimates.pdf |
| 41 | `harbor` | Harbor | implemented | PDF | https://assets.harborcapital.com/docs/Distribution_Estimates_Mutual_Funds_2025.pdf |
| 42 | `nationwide` | Nationwide | implemented | PDF | https://nationwidefinancial.com/media/pdf/MFN-0435AO.pdf |
| 43 | `voya` (alias `allianzgi`) | Voya | implemented | PDF | https://individuals.voya.com/document/tax-center/2025-estimated-capital-gains.pdf |
| 44 | `oakmark` (aliases `harris`, `harris_associates`) | Oakmark / Harris Associates | implemented | yes — fixture fallback | https://oakmark.com/news-insights/2025-oakmark-year-end-fund-distributions/ |
| 45 | `tweedy` (alias `tweedy_browne`) | Tweedy, Browne | implemented | PDF | https://www.tweedyfunds.com/wp-content/uploads/sites/10/2025/10/2025-Estimated-Distributions-9-30-25-2.pdf |
| 46 | `gabelli` (alias `gamco`) | Gabelli | implemented | PDF | https://gabelli.com/wp-content/uploads/2025/12/Distribution-memo-12.29.2025.pdf |
| 47 | `royce` | Royce | implemented | yes — fixture fallback | https://www.royceinvest.com/news/2025/4Q25/open-end-funds-2025-year-end-distributions |
| 48 | `nylife` (aliases `mainstay`, `nyli`) | New York Life Investments / MainStay | implemented | PDF | https://www.nylim.com/assets/documents/tax/cap-gains-estimate.pdf |
| 49 | `touchstone` | Touchstone | implemented | PDF | https://www.westernsouthern.com/-/media/files/touchstone/tax-planning/capital-gains.pdf |
| 50 | `victory` (aliases `vcm`, `victory_capital`) | Victory Capital | implemented | PDF | https://investor.vcm.com/assets/resources-mutualfunddoc/Victory-Funds-2025-Estimated-Capital-Gains.pdf |
| 51 | `sei` (alias `seic`) | SEI | implemented | PDF | https://www.seic.com/sites/default/files/2025-11/SEI%20Capital%20gains%20distribution%20estimates_11.20.2025.pdf |
| 52 | `brown_advisory` (alias `brown`) | Brown Advisory | implemented | PDF | https://www.brownadvisory.com/sites/default/files/2025-10/2025-Capital-Gain-Distribution-Update.pdf |
| 53 | `william_blair` (aliases `blair`, `wbim`) | William Blair | implemented | PDF | https://media.im.williamblair.com/v1/media/edge/images/williamblaib9c8-wbim74f8-wbimprod42cd-8345/media/documents/resources/us/distributions/william-blair-funds---annual-distributions-2025---class-i-n-and-r6.pdf |
| 54 | `vaneck` (alias `van_eck`) | VanEck | implemented | PDF | https://www.vaneck.com/us/en/vaneck-funds-estimated-yearend-distributions-2025.pdf |
| 55 | `wisdomtree` (alias `wt`) | WisdomTree | implemented | PDF | https://www.wisdomtree.com/investments/-/media/us-media-files/documents/about/pdf/2025/wisdomtree-etfs-declare-final-capital-gains-distributions-2025.pdf |
| 56 | `aqr` | AQR | implemented | PDF | https://funds.aqr.com/-/media/Funds/Tax-Documents/2025/2025-AQR-Funds-Announces-Estimated-Distributions.pdf?sc_lang=en |
| 57 | `causeway` | Causeway | implemented | PDF | https://www.causewaycap.com/wp-content/uploads/2025_Causeway-Funds-Final-Distributions.pdf |
| 58 | `alger` (aliases `fred_alger`, `fredalger`) | Alger / Fred Alger | implemented | PDF | https://www.alger.com/AlgerDocuments/Distrib_FUNDS.pdf |
| 59 | `harding_loevner` (aliases `harding`, `hl`) | Harding Loevner | implemented | PDF | https://wealth.amg.com/pdf-library/harding-loevner-2025-year-end-distributions/ |
| 60 | `matthews_asia` (alias `matthews`) | Matthews Asia | implemented | yes — fixture fallback | https://www.matthewsasia.com/funds/mutual-funds/ |
| 61 | `tcw` | TCW | implemented | PDF | https://edge.sitecorecloud.io/thetcwgroupc320-tcwweb7bc3-prod0f26-25f9/media/Downloads/TCW/Products/US-Funds/TCW-Funds/Distribution-and-Tax-Information/TCW-FUND-Distributions-final.pdf?sc_lang=en |
| 62 | `bridgeway` | Bridgeway | implemented | PDF | https://bridgewayfunds.com/wp-content/uploads/sites/2/2025/11/2025-Distribution-Estimates-for-Website.pdf |
| 63 | `jensen` | Jensen | implemented | yes — fixture fallback | https://www.jenseninvestment.com/insights/2025-growth-mutual-fund-distributions/ |
| 64 | `diamond_hill` (alias `diamond`) | Diamond Hill | implemented | PDF | https://www.diamond-hill.com/sitefiles/live/documents/distributions/dhf-capital-gain-estimates-as-of-10-31-25.pdf |
| 65 | `champlain` (aliases `cip`, `cipvt`) | Champlain | implemented | PDF | https://cipvt.com/wp-content/uploads/2025/12/Champlain-Funds-2025-Year-End-Distributions-Final-12-16-25.pdf |
| 66 | `driehaus` | Driehaus | implemented | PDF | https://www.driehaus.com/system/uploads/fae/file/asset/419/DMF_Year_end_Distribution_2025.pdf |
| 67 | `hotchkis` (aliases `hw`, `hotchkis_wiley`) | Hotchkis & Wiley | implemented | PDF | https://www.hwcm.com/wp-content/uploads/2025/03/HW-Funds-Dec-2025-Div-Cap-Gain-Distributions.pdf |
| 68 | `marsico` | Marsico | implemented | yes — fixture fallback | https://www.marsicofunds.com/investor-resources/content/distributions.fs |
| 69 | `osterweis` (alias `ost`) | Osterweis | implemented | PDF | https://www.osterweis.com/files/Distribution-Estimates.pdf |
| 70 | `davis` (alias `davis_funds`) | Davis Funds | implemented | yes — fixture fallback | https://davisfunds.com/funds/distributions |
| 71 | `primecap` (aliases `odyssey`, `primecap_odyssey`) | PRIMECAP Odyssey | implemented | PDF | https://www.primecap.com/wp-content/uploads/2025/11/2025-Distribution-Estimates-as-of-10312025-PCF000287.pdf |
| 72 | `ariel` | Ariel | implemented | PDF | https://www.arielinvestments.com/wp-content/uploads/2025/12/Distributions_ArielFund_as-of-12.17.2025-Final.pdf |
| 73 | `baird` | Baird | implemented | PDF | https://www.bairdassetmanagement.com/siteassets/pdfs/distributions/2025-final-capital-gains.pdf |
| 74 | `longleaf` (alias `southeastern`) | Longleaf Partners | implemented | yes — fixture fallback | https://southeasternasset.com/investment-offerings/longleaf-partners-fund/ |
| 75 | `buffalo` | Buffalo | implemented | PDF | https://buffalofunds.com/wp-content/uploads/2025/11/Final-Cap-Gains-Estimates.pdf |
| 76 | `gqg` | GQG Partners | implemented | PDF | https://gqg.com/content/2025/10/2025-Estimated-Capital-Gain-Distributions-09.30.pdf |
| 77 | `third_avenue` (aliases `thirdave`, `tav`) | Third Avenue | implemented | yes — fixture fallback | https://www.thirdave.com/2025-income-capital-gain-distributions |
| 78 | `heartland` | Heartland | implemented | yes — fixture fallback | https://www.heartlandadvisors.com/Resources/Tax-Information |
| 79 | `fmi` (alias `fmimgt`) | FMI | implemented | PDF | https://www.fmimgt.com/fmi/funds/cs/CS_distribution_summary_2025.pdf |
| 80 | `impax` (aliases `pax`, `impaxam`) | Impax / Pax | implemented | gated HTML — fixture | https://impaxam.com/customer-service/distributions/ |
| 81 | `american_beacon` (alias `beacon`) | American Beacon | implemented | PDF | https://americanbeaconfunds.com/wp-content/uploads/2025/09/2025-Annual-Ordinary-Income-and-Capital-Gains-Mutual-Funds-updated.pdf |
| 82 | `baillie_gifford` (aliases `baillie`, `bg`) | Baillie Gifford | implemented | PDF | https://www.bailliegifford.com/literature-library/funds/mutual-funds/estimated-capital-gain-distribution/ |
| 83 | `brandes` | Brandes | implemented | PDF | https://www.brandes.com/docs/librariesprovider6/default-library/publication/handout/brandes-mutual-funds-capital-gains-distribution-estimates-mutual-funds.pdf?sfvrsn=1329da10_43 |
| 84 | `mairs_power` (aliases `mairs`, `mairsandpower`) | Mairs & Power | implemented | yes — fixture fallback | https://www.mairsandpower.com/about-us/company-news/290-2025-capital-gains-and-dividends |
| 85 | `boston_trust` (aliases `walden`, `boston_trust_walden`) | Boston Trust Walden | implemented | PDF | https://www.bostontrustwalden.com/wp-content/uploads/2025/12/Boston-Trust-Mutual-Funds-2025-Ex-Date-ending-NAV.pdf |
| 86 | `grandeur_peak` (alias `grandeur`) | Grandeur Peak | implemented | yes — fixture fallback | https://grandeurpeakglobal.com/distributions/ |
| 87 | `hennessy` | Hennessy | implemented | yes — fixture fallback | https://www.hennessyfunds.com/funds/distributions |
| 88 | `fam` (alias `fenimore`) | FAM / Fenimore | implemented | yes — fixture fallback | https://fenimoreasset.com/resources/fam-funds-tax-center/ |
| 89 | `meridian` (alias `arrowmark`) | Meridian | implemented | PDF | https://www.arrowmarkpartners.com/meridian/wp-content/uploads/sites/2/2025-Final-Distributions-Meridian-Funds-121925.pdf |
| 90 | `kinetics` (alias `horizon_kinetics`) | Kinetics | implemented | PDF | https://kineticsfunds.com/wp-content/uploads/2025/12/2025-Q4-Kinetics-Funds-Final-Distributions.pdf |
| 91 | `lazard` (alias `lam`) | Lazard | implemented | PDF | https://www.lazardassetmanagement.com/docs/1791/LazardFundsAnnualDistributionDeclarationEstimated.pdf |
| 92 | `manning_napier` (aliases `manning`, `manningandnapier`) | Manning & Napier | implemented | PDF | https://am.manning-napier.com/media/fund-documents/distributions/2025%20Distributions.pdf |
| 93 | `westwood` (alias `whg`) | Westwood | implemented | PDF | https://westwoodgroup.com/wp-content/uploads/2025/10/Fund-Distribution-2025-Cap-Estimate_STAMPED.pdf |
| 94 | `boston_partners` (aliases `bostonpartners`, `robeco`) | Boston Partners | implemented | PDF | https://www.bostonpartners.com/uploads/2025/11/b15ac374201c51486acab7203763117a/bp-funds-estimated-cap-gain-dist-10_31_2025.pdf |
| 95 | `homestead` (alias `nreca`) | Homestead | implemented | PDF | https://www.homesteadadvisers.com/wp-content/uploads/Year-End-Distributions.pdf |
| 96 | `madison` (alias `madison_funds`) | Madison | implemented | yes — fixture fallback | https://madisonfunds.com/resources/tax-center/ |
| 97 | `lsv` (alias `lsvasset`) | LSV | implemented | PDF | https://www.lsvasset.com/pdf/fund-docs/2025-Distributions-12-25.pdf |
| 98 | `lkcm` (alias `luther_king`) | LKCM | implemented | PDF | https://lkcmfunds.com/wp-content/uploads/2025-LKCM-Year-End-Mutual-Fund-Distribution-Estimates-11-3-25.pdf |
| 99 | `oberweis` (alias `oam`) | Oberweis | implemented | PDF | https://oberweisfunds.com/wp-content/uploads/2026/03/2025-Final-Distributions-Sheet.pdf |
| 100 | `riverpark` (alias `rp`) | RiverPark | implemented | PDF | https://riverparkfunds.com/assets/pdfs/news/Distribution_Info_2025_Website_RFT_FINAL_CAP_GAINS_FINAL_INCOME.pdf |
| 101 | `amg` (aliases `amg_funds`, `amgfunds`) | AMG | implemented | PDF | https://wealth.amg.com/pdf-library/amg-funds-2025-year-end-distributions/ |
| 102 | `guidestone` (alias `guide_stone`) | GuideStone | implemented | yes — fixture fallback | https://www.guidestonefunds.com/Tax-Information/Capital-Gains |
| 103 | `value_line` (aliases `valueline`, `vl`) | Value Line | implemented | yes — fixture fallback | https://vlfunds.com/gains |
| 104 | `permanent_portfolio` (alias `prpfx`) | Permanent Portfolio | implemented | PDF | https://www.permanentportfoliofunds.com/pdf/2025%20Supplemental%20Tax%20Information_FINAL.pdf |
| 105 | `conestoga` | Conestoga | implemented | yes — fixture fallback | https://conestogacapital.com/capital-gains-information/ |
| 106 | `kopernik` | Kopernik | implemented | PDF | https://www.kopernikglobal.com/wp-content/uploads/2025/12/KGI-CG-MEMO-December-2025-FINAL-1.pdf |
| 107 | `locorr` | LoCorr | implemented | PDF | https://locorrfunds.com/wp-content/uploads/2021/04/LoCorr-Funds-Annual-CapitalGains-Dividends.pdf |
| 108 | `timothy_plan` (alias `timothy`) | Timothy Plan | implemented | PDF | https://timothyplan.com/download/Capital_Gains_Distribution.pdf |
| 109 | `hodges` | Hodges | implemented | PDF | https://www.hodgescapital.com/hubfs/Mutual_Funds/Documents/Year_End_Distribution_Estimates.pdf |
| 110 | `tocqueville` | Tocqueville | implemented | PDF | https://www.tocquevillefunds.com/wp-content/uploads/2025/12/2025-FINAL-Distributions-December-9-2025.pdf |

**Wellington:** skipped. Wellington Management is primarily a subadvisor / institutional manager and does not publish public US retail distribution-estimate pages that we can register as a `FundSource`. Holdings in Wellington-subadvised sleeves should use the **distributing** family’s slug (or `POST /ingest/distributions`).

**Geode:** skipped. Geode Capital is the Fidelity index subadvisor and does not publish a separate US retail mutual-fund/ETF capital-gains estimate book. Use the `fidelity` adapter.

**Legal & General:** skipped. LGIM America is institutional / SMA-oriented; no public US open-end mutual-fund capital-gains estimate HTML or PDF was found on 2026-09-07.

**PGIM / Prudential:** skipped for this tier. The individual tax center (`https://www.pgim.com/us/en/individual/resources/account-services/tax-center`) links a preliminary-estimate PDF through an AEM viewer (`pidoc?pdfId=8912A02F28CF4802A2CA39479A521E39`). Automated GETs receive the attestation/viewer shell, not the table, and no second public HTML grid or direct DAM PDF was found. Use `POST /ingest/distributions` until a partner file or scrapeable reprint exists.

**Eaton Vance vs Morgan Stanley:** MSIM open-end/ETF year-end PDFs stay on `morgan_stanley`. `eaton_vance` is registered separately because Eaton Vance still publishes distinct public CEF Section 19(b) estimated-source notices.

**Putnam:** skipped as a distinct `FundSource`. Putnam.com now redirects to Franklin Templeton; the remaining Putnam tax-center pages are 1099 samples and per-fund distribution calendars, not a Putnam-branded family estimate book. Use the `franklin_templeton` adapter (alias `putnam`). `wasatch` is the rank-40 replacement.

**Baron:** skipped. The public tax center (`https://www.baroncapitalgroup.com/tax-center`) publishes a 2026 distribution *calendar* only — no per-share capital-gains estimate or paid-amount table.

**Transamerica:** skipped. The individual tax center (`https://www.transamerica.com/individual/investments/tax-center`) publishes a 2026 distribution *schedule* and a document-download shell. No public family-level US open-end estimate or paid-amount PDF/HTML with per-share figures was recovered on 2026-09-07.

**Neuberger Berman:** skipped. The US tax library (`https://www.nb.com/en/us/tax-information-etf`) lists 2025 distribution *actuals* behind `documents.ashx` handlers. No public family-level mutual-fund capital-gains *estimate* PDF or scrapeable HTML grid URL was recovered. CEF/ETF Section 19(a) notices are per-fund, not a retail estimate book.

**Cohen & Steers:** skipped for this tier. The tax center (`https://www.cohenandsteers.com/tax-center/`) lists “Open-end Funds 2025 Distributions Estimate October 31” (and a September 30 reprint cited at `https://assets-prod.cohenandsteers.com/wp-content/uploads/2025/10/09145741/Open-end-Funds-2025-Distributions-Estimate-September-30.pdf`). Automated GETs receive a Cloudflare challenge, not the table, and no second public HTML grid was found. Use `POST /ingest/distributions` until a scrapeable reprint exists. `touchstone` is the rank-49 replacement; `victory` is rank 50.

**Victory vs Pioneer / Amundi:** Pioneer open-end estimates stay on `amundi` (aliases `pioneer`, `victory_pioneer`). `victory` is Victory Portfolios I/II (Integrity / Sycamore / Multi-Cap). USAA (Portfolios III) and RS books have separate public vcm.com PDFs not yet ingested.

**Clearbridge / Western Asset:** skipped as distinct `FundSource`s. Both are Franklin / Legg Mason brands. Use `franklin_templeton` (aliases `franklin`, `templeton`).

**Brandywine:** skipped. US retail books overlap Franklin / Macquarie; no distinct public 2025 estimate or paid family table was found.

**DoubleLine:** skipped for this tier. The public 12/4/2025 final capital-gains PDF (`https://doubleline.com/wp-content/uploads/12-4-2025-DoubleLine-Funds-Final-Capital-Gains.pdf`) lists $0.00 for every fund — no scrapeable non-zero estimate book. Use `POST /ingest/distributions` if an advisor notice has amounts.

**Guggenheim:** skipped. Public materials are CEF monthly distributions / Section 19(a) notices, not an open-end family capital-gains estimate book.

**First Trust:** skipped. Paid ETF press PDFs exist on `ftportfolios.com`, but there is no clean family-level open-end/ETF estimate HTML or PDF to register as a `FundSource`.

**Pacer / Innovator / Global X:** skipped for this wave. Public 2025 family-level MF/ETF capital-gains estimate tables with scrapeable per-share amounts were not verified.

**FPA:** skipped for this tier. The public estimate (`https://fpa.com`) publishes **% of NAV ranges** (e.g. FPACX 6.5–6.9% LT), not per-share amounts. Do not invent per-share figures. Use `POST /ingest/distributions` if an advisor notice has $ / share.

**Pzena / Aristotle:** skipped. No public family-level US open-end estimate or paid-amount table was found.

**Parnassus:** skipped. Annual financial statements publish dollar totals, not a per-share capital-gains estimate book. Third-party dividend sites are not enough.

**Polen:** skipped for this tier. Re-checked 2026-09-07. The public estimate PDF (`https://www.polencapital.com/sites/default/files/2025_Capital_Gains_Estimates.pdf`) is still image-only (`pypdf` extracts 0 characters). The perspectives page links the PDF and has no per-share table. Do not invent per-share amounts. Use `POST /ingest/distributions` until a scrapeable reprint exists.

**WCM:** skipped. No family-level 2025 estimate or paid table was recovered.

**Akre:** skipped. No public 2025 family capital-gains book was found.

**Yacktman:** skipped as a distinct `FundSource`. The AMG family year-end PDF includes YACKX (Class I LT $2.8135). Use the `amg` adapter.

**Weitz:** skipped for this tier. The public indications page (`https://weitzinvestments.com/funds/distributions.fs`) publishes **% of NAV** only (e.g. WVALX LT 17.93%). Do not invent per-share figures. Use `POST /ingest/distributions` if an advisor notice has $ / share.

**Eventide:** skipped for this tier. The public 10/31/2025 preliminary PDF publishes estimate **percentages of net assets** with no scrapeable per-share dollar amounts.

**Ave Maria:** skipped for this wave. `https://avemariafunds.com/distributions.php` is a JS-injected table shell; static GET has no per-share amounts.

**Amana / Saturna:** skipped. 2025 financial statements show no capital-gain distributions for the year (income-only history). No separate family estimate book with 2025 per-share CG was recovered.

**Cambiar:** skipped. `https://cambiar.com/capital-gains-2025/` names Opportunity / Small Cap / SMID funds but publishes no per-share dollar amounts.

**Sound Shore:** skipped. The public portfolio page lists combined 2025 capital gains of $5.02 (SSHFX / SSHVX) with no short-term / long-term split. Do not invent a characterization.

**Sequoia:** skipped as a distinct `FundSource` this wave. Public materials are a single-fund paid history (SEQUX November 2025 LT $10.92), not a multi-fund family estimate book.

**Needham:** skipped. No public family-level 2025 estimate or paid per-share capital-gains table was recovered (annual financials only).

**Pear Tree:** skipped for this wave. Paid ST/LT amounts appear on per-fund product HTML (e.g. Quality Ordinary 2025 ST $0.0907 / LT $5.6608) rather than a family-level estimate or paid book. Use `POST /ingest/distributions` until a family reprint exists.

**Sanderson:** skipped. No public US retail estimate or paid family table was investigated to a usable URL.

**AllianzGI:** skipped as a distinct `FundSource`. AllianzGI’s US retail teams and assets transferred to Voya in 2022. Use the `voya` adapter (alias `allianzgi`). PIMCO remains a separate Allianz affiliate on `pimco`.

**Insurance variable wrappers (Brighthouse, Lincoln, Pacific Life, Jackson):** skipped. Public materials are variable-annuity / life subaccount performance PDFs, not US open-end mutual-fund or ETF family capital-gains estimate books.

**Thornburg:** skipped for this tier. Public ETF capital-gain estimates are $0.00 per share. The mutual-fund dividends page is a JS shell with no scrapeable non-zero family $ table. Use `POST /ingest/distributions` until a mutual-fund reprint exists.

**RiverNorth:** skipped. The public annual-gains page states registered funds are not expected to pay capital gains in December 2025 — no non-zero open-end $ book.

**Congress Asset Management:** skipped. No public family-level 2025/2026 estimate or paid per-share table was recovered.

**Segall Bryant & Hamill / CI SBH:** skipped. Public materials are fund product pages and prospectuses, not a family capital-gains $ book.

**Aegis:** skipped as a distinct `FundSource` this wave. Public materials are a single-fund history / annual financials without a family ST/LT $ table.

**Hussman:** skipped. No public family-level 2025 estimate or paid per-share capital-gains table was recovered.

**Olstein:** skipped. No public family estimate or paid ST/LT book; third-party totals only.

**Smead:** skipped. Forms library lists fact sheets and shareholder reports; no family-level 2025 capital-gains PDF or HTML $ table was recovered.

**Payden:** skipped. Public page is a 2025 payment *schedule* (record/ex/pay dates), not per-share amounts.

**Leuthold:** skipped for this wave. The family estimate PDF cited on third-party lists (`latest-news/613/download.pdf`) 404s; remaining materials are per-fund historical-distribution PDFs. Use `POST /ingest/distributions` until a family reprint exists.

**Praxis:** skipped. Tax-resources HTML is geo-gated; no public family $ table was recovered from this environment.

**AMG vs Harding Loevner / Tweedy:** Harding Loevner and Tweedy stay on `harding_loevner` and `tweedy`. `amg` is the AMG Distributors year-end book (GW&K, River Road, TimesSquare, Yacktman, and other AMG-distributed open-end funds).

**Live honesty:** Vanguard and State Street pages are still client-rendered as of 2026-09-07 (static GET parses 0 rows → fixture fallback). JPM, Goldman, PIMCO, and Invesco still publish estimates as PDFs or login-walled docs — no new scrapeable HTML grids were found on re-check. Ranks 11–20 are the same pattern: BNY, Nuveen, Northern Trust, Dimensional, Columbia, and Pioneer/Amundi are public PDFs; Franklin’s family estimate tool is a JS SPA (fixture uses a public CEF 19(a)); UBS and Schwab have some public HTML but fund-name/class layout or SPA shells keep live parse unreliable. Ranks 21–30 continue that pattern: Janus, American Century, Dodge & Cox, MFS, AB, and Virtus are public PDFs; Lord Abbett’s only public 2025 estimate document is a no-pay list; Federated’s family tax-center grids are JS (fixture uses a public 19(a)); Allspring’s family estimate PDF is gated/image-based (fixture uses public product-page paid rows); Eaton Vance open-end HTML was not found (fixture uses a public CEF 19(b)). Ranks 31–40: John Hancock, Hartford, Macquarie/Delaware, First Eagle, GMO, Calamos, and Wasatch are public PDFs; Thrivent’s paid capital-gains table is public HTML (live parse works after recognizing the “Thrivent Mutual Fund” header; no ticker column); Principal’s family estimate PDF is a GetFile viewer (fixture uses public product-page paid rows); Artisan’s tax-center HTML is paid YTD income (live page is a year-selector shell — fixture fallback; no family estimate PDF). Ranks 41–50: Harbor, Nationwide, Voya, Tweedy, Gabelli, NYLI/MainStay, Touchstone, and Victory Integrity/Sycamore are public PDFs (Nationwide GET is sometimes Akamai-denied); Oakmark and Royce publish public paid HTML (class-section / header layout still returns 0 live rows → fixture fallback). Ranks 51–60: SEI, Brown Advisory, William Blair, VanEck, WisdomTree, AQR, Causeway, Alger, and Harding Loevner are public PDFs (Harding Loevner fixture uses the AMG year-end reprint that includes tickers); Matthews Asia publishes paid amounts on the mutual-fund product HTML (nested accordion tables still return 0 live rows → fixture fallback). Ranks 61–70: TCW, Bridgeway, Diamond Hill, Champlain, Driehaus, Hotchkis & Wiley, and Osterweis are public PDFs (TCW and Diamond Hill PDFs are fund-level — fixtures attach public Class I / Investor tickers); Jensen, Marsico, and Davis publish public HTML (prose lists / multi-class tables still return 0 live rows → fixture fallback). Ranks 71–80: PRIMECAP, Ariel, Baird, Buffalo, GQG, and FMI are public PDFs (PRIMECAP and Buffalo PDFs are fund/class-level — fixtures attach public Investor tickers); Longleaf, Third Avenue, and Heartland publish public HTML (product-page / tax-center layout still returns 0 live rows → fixture fallback); Impax’s distributions hub is geo/investor-type gated (fixture transcribes the public December 2025 table crawled from that URL). Ranks 81–90: American Beacon, Baillie Gifford, Brandes, Boston Trust Walden, Meridian, and Kinetics are public PDFs (Baillie Gifford and Brandes PDFs are fund-level — fixtures attach public Institutional / Class I / Class K tickers); Mairs & Power, Grandeur Peak, Hennessy, and FAM publish public HTML (fund-name-only / multi-year / expandable tables still return 0 live rows or omit tickers → fixture fallback). Ranks 91–100: Lazard, Manning & Napier, Westwood, Boston Partners, Homestead, LSV, LKCM, Oberweis, and RiverPark are public PDFs (Lazard, Manning & Napier, Westwood, Boston Partners, Homestead, and LSV PDFs are fund- or CUSIP-level — fixtures attach public Institutional / Class I / Class S / no-load tickers); Madison publishes paid HTML (fund-name / ST / LT only, no ticker column → fixture fallback). Ranks 101–110: AMG, Permanent Portfolio, Kopernik, LoCorr, Timothy Plan, Hodges, and Tocqueville are public PDFs (GuideStone, Conestoga, Timothy Plan, and Hodges pages/PDFs are fund-level — fixtures attach public Investor / Institutional / Class I / Class A / Retail tickers); GuideStone, Value Line, and Conestoga publish public HTML (fund-name-only or mashed headers may still return 0 live rows → fixture fallback). Do not treat fixture rows as a complete live book. `POST /ingest/distributions` is always valid for an advisor-uploaded notice.

## Source adapters

`FundSource.fetch(mode=...)` returns normalized records. Register new families in `app/sources/registry.py`. Coverage metadata lives on `FundSource` (`coverage_tier`, `aum_rank`, `priority`).

### American Funds / Capital Group (implemented)

Verified public URLs (checked 2026-09-07):

| Page | URL |
| --- | --- |
| 2026 midyear capital gains (paid per-share amounts) | https://www.capitalgroup.com/individual/service-and-support/tax-center/midyear-cap-gains.html |
| 2025 year-end distributions (final LTCG/STCG, special dividends, QDI %) | https://www.capitalgroup.com/individual/service-and-support/tax-center/2025-year-end-distributions.html |
| Tax Center hub | https://www.capitalgroup.com/individual/service-and-support/tax-center.html |
| Year-end calendar (when estimates are posted) | https://www.capitalgroup.com/individual/news/distribution-dates.html |

The parser is built against **real AEM table markup**: multi-row headers, continuation tables with no header row (portfolio series / ETFs), `—` empty cells, `6/16/26` and `12/12` dates, `$3.5365` amounts, and `CGHM — Fund name` tickers.

**Limitations**

- Capital Group publishes *preliminary / updated year-end estimates* (percentage-of-NAV ranges) on a seasonal calendar (historically mid-September and early December). Those estimate HTML pages were **not** on the public individual tax center on 2026-09-07; advisor copies 302 to login. Fixture mode includes `fixtures/american_funds/year_end_estimates_sample.html` that uses the same table structure and the column language from the calendar page.
- Mutual-fund **tickers and share classes** are usually omitted on these family-level tables; they are stored when present (ETFs).
- Live HTML can change. Prefer fixture mode for demos/CI; treat live fetch as best-effort.
- Respect Capital Group terms of use and be polite with `User-Agent` + timeouts (`app/config.py`).

Captured markup used in tests lives under `fixtures/american_funds/`.

### Other registered families (ranks 1–110 except American Funds)

Each family has a `HtmlTableSource` (except American Funds, which keeps its original adapter) plus fixtures under `fixtures/<slug>/`. The shared HTML table parser understands Fidelity Symbol/Cusip cells, iShares `(TICKER)` suffixes, Vanguard “distribution type” rows, T. Rowe two-row headers, `% of NAV` vs NAV price, and per-row as-of dates.

## Adding a fund-family adapter

1. Add `app/sources/my_family.py`:

```python
from app.sources.base import FundSource, FetchResult
from app.sources.parser import NormalizedRecord  # or your own HTML/JSON parser

class VanguardSource(FundSource):
    slug = "vanguard"
    display_name = "Vanguard"
    implemented = True

    def fetch(self, *, mode: str = "fixture") -> FetchResult:
        html = ...  # fixture file or httpx.get
        records = [...]  # list[NormalizedRecord]
        return FetchResult(records=records, source_urls=["https://..."])
```

2. Drop a sample HTML/JSON file in `fixtures/<slug>/`.
3. Register the class in `app/sources/registry.py` (and add aliases if useful). Prefer subclassing `HtmlTableSource` when the source is an HTML table.
4. Add a parser test that reads the fixture.
5. `POST /ingest/fetch` with that family's slug.

Keep normalization in the adapter: the ingest API only accepts the shared `DistributionIn` shape.

## Postgres

SQLAlchemy models are dialect-neutral (JSON, Numeric, timezone-aware DateTime).

```bash
pip install 'psycopg[binary]'
export DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/distributions
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Tables are created on startup (`Base.metadata.create_all`). For production, swap that for Alembic migrations.

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

Coverage includes HTML normalization (American Funds plus top-110 family fixtures), multi-year history filters, upsert idempotency, search filters, tax illustration math, portfolio coverage, Current vs Proposed allocation compare, compare-chart deltas, and coverage-gap logging.

## Layout

```
app/
  main.py              FastAPI app
  api.py               HTTP routes
  models.py / schemas.py / crud.py
  sources/             FundSource adapters + HTML parser
  services/ingest.py   Fetch + upsert orchestration
  services/illustrate.py  Tax-impact illustration
  services/coverage.py Coverage snapshot + gap logging
  cli.py               seed / fetch / families
fixtures/<family>/     HTML fixtures (American Funds + top 110)
tests/
```
