# Aftertax

See the taxable impact in dollars — before the meeting ends.

**Open the homepage**

```bash
npm install
npm run dev
```

Then open [http://localhost:3000](http://localhost:3000). The homepage hero is **Growth of $X** stacked over year-aligned negative tax-drag bars (`GrowthAndTaxDragModule`, no preloaded funds — search or Add Fund to plot a series at $10,000). Search **AMCPX** (Capital Group / AMCAP) to seed that ticker into the stack and open the dollar illustration. Ledger Light, monogram, and locked GTM hero copy are on that page. No Stripe keys and no Data API are required for this demo.

**Fund-to-fund comparison** is a dedicated **Compare** tab at [http://localhost:3000/compare](http://localhost:3000/compare) (`/?tab=compare` and `/#fund-compare` redirect there). **Fund Comparison** opens that view — two fund pickers plus the existing `FundTaxDeltaCompare` card. Standalone module demo: [http://localhost:3000/fund-compare](http://localhost:3000/fund-compare). Import `FundTaxDeltaCompare` from `@/components/illustrate`.

**Portfolio comparison** is a dedicated **Portfolio** tab at [http://localhost:3000/portfolio](http://localhost:3000/portfolio) (`/?tab=portfolio` redirects there). **Import a portfolio** opens that view — Current vs Proposed books, tax impact, and holdings only. Standalone module demo: [http://localhost:3000/portfolio-compare](http://localhost:3000/portfolio-compare). Import `PortfolioCompare` from `@/components/illustrate`.

Stacked growth + tax-drag also has a standalone demo at [http://localhost:3000/growth-tax](http://localhost:3000/growth-tax). Import `GrowthAndTaxDragModule` from `@/components/illustrate`.

Aftertax is a search-first workspace for wholesalers and financial advisors. This repo slice is the **website UI**: fund search, highlights, holding size, adjustable tax rates, and results. The Data team owns ingest, `GET /distributions`, and production `POST /illustrate` math (see PR #2).

## Run locally

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). That is enough for a search + illustrate homepage.

- `npm run build` / `npm run lint` / `npm run typecheck`

## Hosts

Prefer **staging** until ads are green-lit.

| Env | Host |
| --- | --- |
| Local | [http://localhost:3000](http://localhost:3000) |
| Staging | [https://staging.getaftertax.com](https://staging.getaftertax.com) |
| Production | [https://getaftertax.com](https://getaftertax.com) (apex, not `www`) |

Set `AFTERTAX_PUBLIC_URL` to the host you are deploying. Default (no env) is **staging**. Chrome still shows `getaftertax.com` as the brand host.

## Deploy (Vercel)

Standard Next.js App Router at the **repo root** — no adapter, no `vercel.json` required. In Vercel: Import GitHub repo → framework **Next.js** → assign custom domain **`staging.getaftertax.com`**. Production follows `main`.

For first public staging:

- `AFTERTAX_PUBLIC_URL=https://staging.getaftertax.com`
- Optional: `NEXT_PUBLIC_DATA_API_URL` to point at the PR #2 Data API
- **Do not set** `STRIPE_SECRET_KEY`. Search + illustrate is enough; freemium/Checkout can stay stubbed.

Staging is `noindex`. Switch `AFTERTAX_PUBLIC_URL` to `https://getaftertax.com` when ads are green-lit.

## What you will see

- One-screen landing: hero (taxable impact in dollars) + **Search a fund** as the primary action. Header tabs: **Search** (`/`), **Portfolio** (`/portfolio`), and **Compare** (`/compare`). CTA order when present: **Search a fund** → **Fund Comparison** → **Import a portfolio**. Fund Comparison opens the Compare tab; Import opens the Portfolio tab — neither is a homepage scroll target and neither opens the paywall.
- Instant **dollar illustration** after a fund is selected ($1,000,000 holding default, editable federal/state rates, min/max when present).
- **Tax-delta compare** on `/compare` (and `/fund-compare`): Fund A / Fund B pickers plus `FundTaxDeltaCompare` (YoY tax drag + tax-impact delta). Defaults AMCPX vs VIGAX. `?left=` / `?right=` seed the pickers; the homepage CTA passes `?left=` when a fund is selected. The Compare tab does not show Growth of $X, fund-search hero, dollar illustration, portfolio books, or highlights.
- **Portfolio comparison** on `/portfolio` (and `/portfolio-compare`): Current vs Proposed Allocation, GTM history-covered smoke books (Current AGTHX / DODIX / AMCAP / DODGX and Proposed AMCPX / CGHM / AGTHX / AMCAP at 25% each) + $1M + state 0.05, Upcoming / announced (every fund; empty = undisclosed, not $0), ticker × calendar-year tax $ (2021–2025; unmatched / uncovered = N/A), tax drag %, more/less tax Δ. The Portfolio tab does not show Growth of $X, fund-search hero, dollar illustration, FundCompareRail, or highlights. Export calls `exportToPdf` (freemium gate stubbed).
- **Growth of $X + tax drag** is the homepage hero (`GrowthAndTaxDragModule`): cumulative growth vs one benchmark, then year-centered negative tax-drag bars for up to 6 funds. Tax panel toggles % of value / tax $. Starts empty; searching a fund or Add Fund seeds the list at $10,000. Standalone demo: `/growth-tax`.
- Soft counter is **temporarily unlocked for beta** (`NEXT_PUBLIC_FREEMIUM_DISABLED`, default on). Set that env to `false` to restore `3 of 3 free searches left` → paywall after 3 unique tickers.
- Highlights + estimates table sit below the fold as the sample universe — not a landing feature grid.
- Sample/demo data banner. Capital Group / American Funds is treated as live ingest; other families show a **coverage gap**.
- Checkout is stubbed (`POST /api/checkout` → 501) until Stripe test mode. Price id `price_1UD6C0RqA7bY5N5qVleZso0d`. Return URLs: `/?checkout=success` stays in this flow; `/?checkout=cancel` reopens the paywall. No onboarding tour.

## Disclaimer (QA-final unless Eric edits)

Shown next to every dollar result and on the paywall (do not paraphrase):

> Illustrative estimates only. Not tax, legal, or investment advice. Figures may omit state, local, AMT, wash-sale, holding-period, and other rules. Consult a qualified tax professional. Aftertax is not a broker-dealer or RIA.

Hero / footer keep the short trust line: “Illustrative estimates only. Not tax, legal, or investment advice.”

## Golden tests

**Capital Group live fixtures first** (`src/lib/golden.ts`). Start with **AMCPX** and **AGTHX**; the rest of the American Funds seed rows are the current live set. More hero tickers will be added later — do not treat other families as golden.

## Mock vs real Data API (PR #2)

The browser **does not** compute tax. Aftertax calls the Data API when `NEXT_PUBLIC_DATA_API_URL` is set, and falls back to local mocks only if that host is down (network / 5xx). 4xx from a running API is shown as an error.

| Mode | How |
| --- | --- |
| Demo (default) | Local mocks: `POST /api/illustrate`, `POST /api/illustrate/compare`, `GET /api/performance`, `POST /api/performance/growth`, `POST /api/illustrate/portfolio`, `POST /api/illustrate/portfolio/compare`, `GET /api/coverage`, `GET /api/fund-families`, `POST /api/request/ticker` |
| Data team FastAPI (PR #2) | `NEXT_PUBLIC_DATA_API_URL=http://localhost:8000` |

Wired endpoints:

- `POST /illustrate` — UI sends locked `selector: { fund_family, fund_identifier }`; the client also sends PR #2’s `selectors` alias. Response is normalized to `tax_rates_applied`, `estimated_tax_dollars`, `warnings`.
- `POST /illustrate/compare` — `mode: "fund_vs_fund"` with `left` / `right` selectors + `periods[]`. Deltas are **right − left**. The card maps them to Fund A (left) cost-to-holder prose (`costToA = −delta`). Chart field: `periods[].deltas.effective_tax_on_holding`. Footer uses `summary` at $10k. Clients send per-side `nav_per_share` when search/seed metadata has a NAV (`per_share` rows otherwise return `matched: false` / $0) and omit it for the `% of NAV` / holding_dollars-only path. Mixed upcoming coverage still shows YoY bars; the Upcoming tax cell is per side (`$185` or `—` / `Not announced`) and never blanks the card. Local mock returns the locked sketch fixture when the Data API is down. Product view: `/compare` (`HomepageFundCompare` → `FundTaxDeltaCompare`). Standalone demo: `/fund-compare`. Reusable historical chart: `YoYTaxChart` (calendar-year bars + optional descending YoY tax line) from `@/components/illustrate`. `mode: "yoy"` feeds calendar-year tax-drag bars in `GrowthAndTaxDragModule`.
- `POST /illustrate/portfolio/compare` — Current vs Proposed Allocation. Body: `current` / `proposed` `{ label?, holdings[], book_dollars }` with `ticker` + `weight_pct` (or `holding_dollars`), plus `periods: [{year:2021}…{year:2025}]` for the ticker × calendar-year tax $ table. Clients send per-holding `nav_per_share` when search/seed metadata has a NAV (`per_share` `paid_history` rows otherwise drop out) and never send `nav=0`. Deltas are **proposed − current** (`deltas.estimated_tax`, `effective_tax_on_holding`). Upcoming lists every Current/Proposed fund (est. dist $, tax to holder, record, ex-div with year); empty/null upcoming is **Not available / undisclosed**, not $0. Paid History is a list from additive `holdings[].paid_history[]` only (same row shape; newest-first; cap 12). Do not derive from `illustration.components`, `distributions`, or `upcoming`. Do not invent dates. Calendar-year tax is the existing `CalendarYearTaxTable` module — Website keeps it and will add 2025 / denser cells; do not replace or rebuild that matrix. Calendar-year cells read `periods[]` per ticker (`matched: false` / `covered: false` / `gap_reason` / null totals / missing → **N/A**, never $0). Search/seed `nav_per_share` also fills thin year cells (AGTHX/DODIX). Each column shows **Total tax impact** = Σ `upcoming.estimated_tax` above the chart. Current/Proposed tax drag cards read `totals.effective_tax_on_holding` / `totals.estimated_tax` and Δ is `deltas.estimated_tax` (proposed − current) — independent of empty Upcoming. Older payloads without `upcoming` still fall back to `illustration` + `publication_stage_used`. If compare is 404/down, the client double-calls `POST /illustrate/portfolio` and synthesizes deltas; localhost falls back to the sketch fixture. Print/PDF: `exportToPdf(toPortfolioCompareExportModel(result, bookDollars))` — Website wires the button + freemium gate. Product view: `/portfolio`. Standalone demo: `/portfolio-compare`. Import `PortfolioCompare`, `exportToPdf`, and `toPortfolioCompareExportModel` from `@/components/illustrate`.
- `GET /performance?ticker=AGTHX&mode=fixture` and `POST /performance/growth` — monthly fund + benchmark `growth_of_x` (default $10,000). Benchmarks SPY / AGG / VXUS by asset class. Fixtures AGTHX, FCNTX, AMCPX, FBGRX, VFIAX, DODIX. Local mock when the Data API is down. Homepage mounts `GrowthAndTaxDragModule`; standalone demo: `/growth-tax`.
- `POST /illustrate/portfolio` — coverage `dollars_covered` / `dollars_uncovered` / `coverage_pct` + `gaps[]` + `warnings` (shown on the illustrate panel). Also the fallback for portfolio compare.
- `GET /distributions` — aggregated into the search table (seed fills tickers the API does not yet return).
- `GET /coverage`, `GET /fund-families` — `coverage_tier`, `aum_rank`, `priority` (Live vs Gap in picker / results / illustrate).
- `POST /coverage/gaps` — logged when a gap ticker is selected.
- `POST /request/ticker` — beta ticker intake (no auth). Body `{ ticker, note?, source: "web" | "search_miss" | "portfolio" }`. Search auto-POSTs `search_miss` on an exact ticker with no match (toast, no invented fund data). Request a fund on Search sends `source: "web"`. Shared helper: `requestTicker` from `@/lib/data-api/request-ticker` (Portfolio / Compare can import later with `source: "portfolio"`). 201 queued / 200 already in universe / 422 invalid. Local mock: `POST /api/request/ticker`.

### Run UI + Data API side by side

PRs stay separate (this UI is PR #1; ingest/API is PR #2). Do not merge the branches. Checkout PR #2 in a second worktree or clone:

```bash
# Data API — PR #2 branch cursor/fund-distribution-ingest-api-85ed
git fetch origin cursor/fund-distribution-ingest-api-85ed
git worktree add /tmp/aftertax-data-api origin/cursor/fund-distribution-ingest-api-85ed
cd /tmp/aftertax-data-api
pip install -r requirements-dev.txt
python -m app.cli seed
uvicorn app.main:app --reload --port 8000

# UI — this PR, from the Aftertax repo root
NEXT_PUBLIC_DATA_API_URL=http://localhost:8000 npm run dev
```

Optional illustrate-only override: `NEXT_PUBLIC_ILLUSTRATE_URL=http://localhost:8000/illustrate`.
Optional compare-only override: `NEXT_PUBLIC_COMPARE_URL=http://localhost:8000/illustrate/compare`.
Optional portfolio-compare override: `NEXT_PUBLIC_PORTFOLIO_COMPARE_URL=http://localhost:8000/illustrate/portfolio/compare`.

Types live in `src/lib/illustrate/types.ts`. Mock `POST /api/illustrate` returns `tax_rates_applied`, `components[]`, `totals`, and `warnings[]`.

Request: `holding_dollars`, `distribution_ids` **or** `selector: { fund_family, fund_identifier }`, optional `nav_per_share`, `tax_rates`, `combine_state_with_federal`.

If `tax_rates` is omitted, the mock applies ordinary/STCG `0.37`, LTCG/QDI `0.20`, state `0.0`. The UI sends explicit advisor defaults (including state `0.05`) on every request.

`% of NAV` sends holding dollars and, when search/seed metadata has a NAV, `nav_per_share` so Data can derive shares for per_share snapshots. `$ / share` requires `nav_per_share` (422 `nav_required` / `needs_nav_or_shares` otherwise; UI maps that to “Need fund price to convert this holding.”).

### Rate mapping (locked)

- `ordinary_income`, `special_dividend`, `return_of_capital`, `other` → ordinary (+ state if combined)
- `long_term_capital_gains`, `total_capital_gains` → LTCG (+ state)
- `short_term_capital_gains`, `qualified_short_term_gains` → STCG (+ state)
- `qualified_dividend` → QDI (+ state)
- `total` → ordinary unless the row is skipped

Prefer one `publication_stage` / `as_of` snapshot in the panel so midyear paid + preliminary % NAV are not double-counted.

## Search data vs `GET /distributions`

When `NEXT_PUBLIC_DATA_API_URL` is set and PR #2 is running, search/highlights load `GET /distributions` (aggregated to one row per ticker) and keep seed funds for tickers the API does not return yet. If the Data API is down, the seed table is used alone.

## Coverage gaps

`GET /coverage` and `GET /fund-families` drive Live vs Gap badges (`coverage_tier`, `aum_rank`, `priority`). Fallback when the API is down: Capital Group / American Funds is treated as live. Selecting a gap ticker POSTs `POST /coverage/gaps`. The illustrate panel also POSTs `POST /illustrate/portfolio` for the current holding so `dollars_covered` / `dollars_uncovered` / `coverage_pct` and `gaps[]` are visible.

## Funnel (this UI)

1. Land → search a fund (primary). Fund Comparison opens the Compare tab (`/compare`). Import a portfolio opens the Portfolio tab (`/portfolio`).
2. Instant dollar illustration. Beta: searches are unlimited (soft-wall off).
3. After 3 unique fund searches → paywall (`$39 / user / month`) **only when** `NEXT_PUBLIC_FREEMIUM_DISABLED=false`.
4. Checkout stub returns to the same flow (`?checkout=success`) or paywall (`?checkout=cancel`). No onboarding tour. Beta unlock also suppresses the cancel paywall.

Highlights and the full estimates table sit below the illustration as the sample universe — not a landing feature grid.

## Freemium / Stripe (website owns Checkout)

The Aftertax **website** creates Stripe Checkout Sessions server-side (`POST /api/checkout` → `src/lib/stripe/checkout.ts`).

- Price `price_1UD6C0RqA7bY5N5qVleZso0d` (product `prod_VDXGeprN4QkxsM`, account `acct_1UD66TRqA7bY5N5q`)
- `success_url` / `cancel_url` default to **https://staging.getaftertax.com** until ads are green-lit (`AFTERTAX_PUBLIC_URL` overrides)
- **Test mode later. Do not block on live keys.** Without `STRIPE_SECRET_KEY`, Unlock Aftertax is stubbed (501) and search + illustrate still work.
- When test-mode keys exist: set `STRIPE_SECRET_KEY` and optional `STRIPE_PRICE_ID` / `AFTERTAX_PUBLIC_URL`.

Paywall copy is locked in `src/lib/copy.ts`. 3 free unique fund searches use client `localStorage` for this demo.

### Temporary beta unlock (revert before launch)

`NEXT_PUBLIC_FREEMIUM_DISABLED` short-circuits every free-tier check and the soft-wall overlay (`src/lib/freemium.ts`). **Default is on** when the env var is unset so production/staging do not need a Vercel setting for Eric’s beta. Stored `aftertax.freemium.v1` counters are ignored while unlocked.

| Value | Behavior |
| --- | --- |
| unset / `true` / `1` | Unlimited searches; Import never opens the paywall |
| `false` / `0` / `off` | Restore 3-search counter + Upgrade overlay |

Revert this default (or delete the bypass) before the freemium sprint / public launch. Do not treat this as the long-term billing path. Stripe Checkout is still stubbed.

## Code structure

```
src/
  app/                 App Router + mock API routes
  components/          Search, highlights, illustrate, landing, paywall
  data/                Seed + query helpers for the estimates table
  lib/illustrate/      Typed client, locked contract, mock engine (server)
```

Auth is not implemented. Billing is stubbed only.
