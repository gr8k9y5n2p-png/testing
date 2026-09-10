# Aftertax

See the taxable impact in dollars — before the meeting ends.

**Open the homepage**

```bash
npm install
npm run dev
```

Then open [http://localhost:3000](http://localhost:3000). The **Search** homepage is fund-manager announced estimates plus data tables — not Growth & tax drag. Search **AMCPX** (Capital Group / AMCAP) when `GET /distributions` has that ticker to open Upcoming / announced (unpaid only / Undisclosed — never invented from history) and a dollar illustration. Historical paid distributions live on Compare / Portfolio Growth & Tax. Ledger Light, monogram, and locked GTM hero copy are on that page. No Stripe keys are required. Search / Sample Estimates need `NEXT_PUBLIC_DATA_API_URL` (empty, N/A, or Undisclosed if the API is down).

**Fund comparison** is a dedicated **Compare** tab at [http://localhost:3000/compare](http://localhost:3000/compare) (`/?tab=compare` and `/#fund-compare` redirect there; ticker query is preserved). Search-page ticker and fund-name clicks (Highlights, Sample Estimates) select that fund into **Search a fund** and hydrate the same modules as a typed selection — they do not open `/compare?tickers=`. **Fund Comparison** opens the Compare tab — six ticker slots, then `GrowthAndTaxDragModule`, a calendar-year tax/distribution table, then Upcoming / announced. Standalone tax-delta demo: [http://localhost:3000/fund-compare](http://localhost:3000/fund-compare). Import `CompareWorkspace` from `@/components/illustrate`.

**Portfolio comparison** is a dedicated **Portfolios** tab at [http://localhost:3000/portfolio](http://localhost:3000/portfolio) (`/?tab=portfolio` redirects there). **Import a portfolio** opens that view — Current vs Proposed books, tax impact, and holdings only. Standalone module demo: [http://localhost:3000/portfolio-compare](http://localhost:3000/portfolio-compare). Import `PortfolioCompare` from `@/components/illustrate`.

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
- Friends beta: set `FRIENDS_BETA_PASSWORD` (see below). Do not buy Vercel Pro Password Protection.

Staging is `noindex`. Switch `AFTERTAX_PUBLIC_URL` to `https://getaftertax.com` when ads are green-lit.

## What you will see

- One-screen landing: **Search a fund** as the primary action, then Fund Manager announced estimates + data tables. Header tabs: **Search** (`/`), **Compare** (`/compare`), and **Portfolios** (`/portfolio`). Search does not show Fund Comparison / Import a portfolio shortcuts — those tabs are AppNav only.
- Instant **dollar illustration** after a fund is selected ($1,000,000 holding default, editable federal/state rates, min/max when present), including **Upcoming / announced** (unpaid only; empty = Not available / undisclosed). Search does not mount **Paid history** — historical paid distributions live on Compare / Portfolio Growth & Tax.
- **Compare** on `/compare`: six empty ticker slots (user-added; **one ticker is enough** — empty slots ignored) plus one shared **Dollars invested** input (default $10,000) that scales Growth starting dollars, tax-drag $ / taxable amounts, calendar-year tax $ / dist $, delta-strip $ metrics, and upcoming taxable $. A compact **delta strip** (Total tax $ Δ, Annualized tax-drag Δ %, Distribution $ Δ, Upcoming taxable / Undisclosed) mounts without blocking the page. Filled tickers then flow through `GrowthAndTaxDragModule`, a ticker × calendar-year tax $ / dist $ table from live `POST /illustrate/compare` `mode: "yoy"` (unmatched = N/A, never fake $0), then Upcoming / announced (unpaid announced only; empty = Undisclosed / Not available — never invented from paid history). `?tickers=AGTHX` (comma-separated or repeated) still prefills Compare slots; `?left=` / `?right=` / `?ticker=` still work. Search-page ticker clicks no longer navigate here. A plain `/compare` visit starts empty. The Compare tab does not show FundTaxDeltaCompare as the main layout, the fund-search hero, dollar illustration, portfolio books, or highlights. Historical tax drag and Upcoming stay separate. The `/fund-compare` demo still mounts the reusable `FundTaxDeltaCompare` card.
- **Portfolio comparison** on `/portfolio` (and `/portfolio-compare`): Current vs Proposed Allocation start empty — add tickers with **+ Add holding**. Book default $1M + state 0.05. Upcoming / announced (every fund; empty = undisclosed, not $0), ticker × calendar-year tax $ (2021–2025; unmatched / uncovered = N/A), tax drag %, more/less tax Δ. The Portfolios tab does not show Growth of $X, fund-search hero, dollar illustration, FundCompareRail, or highlights. Export calls `exportToPdf` (freemium gate stubbed).
- **Growth of $X + tax drag** (`GrowthAndTaxDragModule`) is not mounted on Search. The component stays exported for Compare and the standalone demo at `/growth-tax`.
- Soft counter is **temporarily unlocked for beta** (`NEXT_PUBLIC_FREEMIUM_DISABLED`, default on). Set that env to `false` to restore `3 of 3 free searches left` → paywall after 3 unique tickers.
- Highlights + estimates table sit below the fold as the live Data API universe — not a landing feature grid.
- Live Data API banner. Search / Sample Estimates never merge `seed.ts`. Uncovered or missing values stay empty, N/A, or Undisclosed. Capital Group / American Funds is treated as live ingest; other families show a **coverage gap**.
- Checkout is stubbed (`POST /api/checkout` → 501) until Stripe test mode. Price id `price_1UD6C0RqA7bY5N5qVleZso0d`. Return URLs: `/?checkout=success` stays in this flow; `/?checkout=cancel` reopens the paywall. No onboarding tour.

## Disclaimer (QA-final unless Eric edits)

Shown next to every dollar result and on the paywall (do not paraphrase):

> Illustrative estimates only. Not tax, legal, or investment advice. Figures may omit state, local, AMT, wash-sale, holding-period, and other rules. Consult a qualified tax professional. Aftertax is not a broker-dealer or RIA.

Hero / footer keep the short trust line: “Illustrative estimates only. Not tax, legal, or investment advice.”

## Golden tests

**Capital Group live fixtures first** (`src/lib/golden.ts`). Start with **AMCPX** and **AGTHX**; the rest of the American Funds seed rows are the current live set. More hero tickers will be added later — do not treat other families as golden.

## Mock vs real Data API (PR #2)

The browser **does not** compute tax. Aftertax calls the Data API when `NEXT_PUBLIC_DATA_API_URL` is set. Production does not fall back to local `/api/*` mocks (those responses carry MOCK / seed-math chrome). 4xx / 5xx from a running API is shown as an error.

| Mode | How |
| --- | --- |
| Demo (default) | Local mocks: `POST /api/illustrate`, `POST /api/illustrate/compare`, `GET /api/performance`, `POST /api/performance/growth`, `POST /api/illustrate/portfolio`, `POST /api/illustrate/portfolio/compare`, `GET /api/coverage`, `GET /api/fund-families`, `POST /api/request/ticker` |
| Data team FastAPI (PR #2) | `NEXT_PUBLIC_DATA_API_URL=http://localhost:8000` |

Wired endpoints:

- `POST /illustrate` — UI sends locked `selector: { fund_family, fund_identifier }`; the client also sends PR #2’s `selectors` alias. Response is normalized to `tax_rates_applied`, `estimated_tax_dollars`, `warnings`.
- `POST /illustrate/compare` — `mode: "fund_vs_fund"` with `left` / `right` selectors + `periods[]`. Deltas are **right − left**. The card maps them to Fund A (left) cost-to-holder prose (`costToA = −delta`). Chart field: `periods[].deltas.effective_tax_on_holding`. Footer uses `summary` at $10k. Clients send per-side `nav_per_share` when search/seed metadata has a NAV (`per_share` rows otherwise return `matched: false` / $0) and omit it for the `% of NAV` / holding_dollars-only path. Mixed upcoming coverage still shows YoY bars; the Upcoming tax cell is per side (`$185` or `—` / `Not announced`) and never blanks the card. Local mock returns the locked sketch fixture when the Data API is down. Product view: `/compare` (`HomepageFundCompare` → `FundTaxDeltaCompare`). Standalone demo: `/fund-compare`. Reusable historical chart: `YoYTaxChart` (calendar-year bars + optional descending YoY tax line) from `@/components/illustrate`. `mode: "yoy"` feeds calendar-year tax-drag bars in `GrowthAndTaxDragModule`.
- `POST /illustrate/portfolio/compare` — Current vs Proposed Allocation. Body: `current` / `proposed` `{ label?, holdings[], book_dollars }` with `ticker` + `weight_pct` (or `holding_dollars`), plus `periods: [{year:2021}…{year:2025}]` for the ticker × calendar-year tax $ table. Clients send per-holding `nav_per_share` when search/seed metadata has a NAV (`per_share` `paid_history` rows otherwise drop out) and never send `nav=0`. Deltas are **proposed − current** (`deltas.estimated_tax`, `effective_tax_on_holding`). Upcoming lists every Current/Proposed fund (est. dist $, tax to holder, record, ex-div with year); empty/null upcoming is **Not available / undisclosed**, not $0. Paid History is a list from additive `holdings[].paid_history[]` only (same row shape; newest-first; cap 12). Do not derive from `illustration.components`, `distributions`, or `upcoming`. Do not invent dates. Calendar-year tax is the existing `CalendarYearTaxTable` module — Website keeps it and will add 2025 / denser cells; do not replace or rebuild that matrix. Calendar-year cells read `periods[]` per ticker (`matched: false` / `covered: false` / `gap_reason` / null totals / missing → **N/A**, never $0). Search/seed `nav_per_share` also fills thin year cells (AGTHX/DODIX). Each column shows **Total tax impact** = Σ `upcoming.estimated_tax` above the chart. Current/Proposed tax drag cards read `totals.effective_tax_on_holding` / `totals.estimated_tax` and Δ is `deltas.estimated_tax` (proposed − current) — independent of empty Upcoming. Older payloads without `upcoming` still fall back to `illustration` + `publication_stage_used`. If compare is 404/down, the client double-calls `POST /illustrate/portfolio` and synthesizes deltas; localhost falls back to the sketch fixture. Print/PDF: `exportToPdf(toPortfolioCompareExportModel(result, bookDollars))` — Website wires the button + freemium gate. Product view: `/portfolio`. Standalone demo: `/portfolio-compare`. Import `PortfolioCompare`, `exportToPdf`, and `toPortfolioCompareExportModel` from `@/components/illustrate`.
- `GET /performance?ticker=AGTHX&mode=fixture` and `POST /performance/growth` — monthly fund + benchmark `growth_of_x` (default $10,000). Benchmarks SPY / AGG / VXUS by asset class. Fixtures AGTHX, FCNTX, AMCPX, FBGRX, VFIAX, DODIX. Local mock when the Data API is down. `GrowthAndTaxDragModule` is not mounted on Search; `/compare` mounts it for filled ticker slots; standalone demo: `/growth-tax`.
- `POST /illustrate/portfolio` — coverage `dollars_covered` / `dollars_uncovered` / `coverage_pct` + `gaps[]` + `warnings` (shown on the illustrate panel). Also the fallback for portfolio compare.
- `GET /distributions` — aggregated into Search / Sample Estimates / highlights. Empty or missing tickers stay empty — `seed.ts` is not merged in.
- `GET /coverage`, `GET /fund-families` — `coverage_tier`, `aum_rank`, `priority` (Live vs Gap in picker / results / illustrate).
- `POST /coverage/gaps` — logged when a gap ticker is selected.
- `POST /request/ticker` — beta ticker intake (no auth). Body `{ ticker, note?, source }`. One client: `requestTicker({ ticker, note?, source })` from `@/lib/request-ticker` (also `@/components/illustrate`). Do not duplicate the fetch. 201 queued / 200 already in universe / 422 invalid. Local mock: `POST /api/request/ticker`.

### `requestTicker` source enum (locked)

```ts
import { requestTicker, TICKER_REQUEST_SOURCES } from "@/lib/request-ticker";
// or: import { requestTicker } from "@/components/illustrate";

await requestTicker({ ticker: "ABCDX", note: "optional", source: "portfolio" });
```

| `source` | Who sends it |
| --- | --- |
| `web` | Request a fund form on Search |
| `search_miss` | Search typed an exact ticker with no match |
| `portfolio` | Portfolio import / Compare slot miss (Modules) |

`TICKER_REQUEST_SOURCES` is `["web", "search_miss", "portfolio"]`. Search uses `web` and `search_miss`. Portfolio import and Compare slots call `requestTickerOnPortfolioMiss` / `notifyPortfolioTickerMiss` (`source: "portfolio"`) — never invent fund data while queued. Toast copy matches Search miss: “We’ll work on ingesting this.”

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

Search, Sample Estimates, and homepage highlights load `GET /distributions` only (aggregated to one row per ticker). If the Data API is down or returns no rows, those UI paths stay empty (N/A / Undisclosed) — they do not fall back to `seed.ts` sample math. `seed.ts` remains for tests and illustrate mocks only.

## Coverage gaps

`GET /coverage` and `GET /fund-families` drive Live vs Gap badges (`coverage_tier`, `aum_rank`, `priority`). Fallback when the API is down: Capital Group / American Funds is treated as live. Selecting a gap ticker POSTs `POST /coverage/gaps`. The illustrate panel also POSTs `POST /illustrate/portfolio` for the current holding so `dollars_covered` / `dollars_uncovered` / `coverage_pct` and `gaps[]` are visible.

## Funnel (this UI)

1. Land → search a fund (primary). Compare and Portfolios are AppNav tabs (`/compare`, `/portfolio`) — not Search-page shortcut buttons.
2. Instant dollar illustration. Beta: searches are unlimited (soft-wall off).
3. After 3 unique fund searches → paywall (`$39 / user / month`) **only when** `NEXT_PUBLIC_FREEMIUM_DISABLED=false`.
4. Checkout stub returns to the same flow (`?checkout=success`) or paywall (`?checkout=cancel`). No onboarding tour. Beta unlock also suppresses the cancel paywall.

Highlights and the full estimates table sit below the illustration as the live Data API universe — not a landing feature grid.

## Freemium / Stripe (website owns Checkout)

The Aftertax **website** creates Stripe Checkout Sessions server-side (`POST /api/checkout` → `src/lib/stripe/checkout.ts`).

- Price `price_1UD6C0RqA7bY5N5qVleZso0d` (product `prod_VDXGeprN4QkxsM`, account `acct_1UD66TRqA7bY5N5q`)
- `success_url` / `cancel_url` default to **https://staging.getaftertax.com** until ads are green-lit (`AFTERTAX_PUBLIC_URL` overrides)
- **Test mode later. Do not block on live keys.** Without `STRIPE_SECRET_KEY`, Unlock Aftertax is stubbed (501) and search + illustrate still work.
- When test-mode keys exist: set `STRIPE_SECRET_KEY` and optional `STRIPE_PRICE_ID` / `AFTERTAX_PUBLIC_URL`.

Paywall copy is locked in `src/lib/copy.ts`. 3 free unique fund searches use client `localStorage` for this demo.

### Friends-beta password gate

In-app shared password so Production can stay off Vercel Pro Deployment Protection ($150/mo). Set **`FRIENDS_BETA_PASSWORD`** in Vercel → Project → Settings → Environment Variables for Production (and Preview if you want the same lock). `BETA_PASSWORD` is an alias. Unset the var to take the gate off when going public. Do not use a `NEXT_PUBLIC_` prefix.

| Value | Behavior |
| --- | --- |
| set | Visiting `/`, `/portfolio`, `/compare`, and other app pages shows `/beta`. Correct password sets an httpOnly cookie (14 days). Refresh stays unlocked. |
| unset | Gate is off. Site works as today. |

`/terms` and `/privacy` stay public. Same-origin `/api/*` mocks and Render `NEXT_PUBLIC_DATA_API_URL` calls are not gated. Contact remains `operations@getaftertax.com`.

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
  data/                Data API repository + query helpers (seed.ts is test/mock only)
  lib/illustrate/      Typed client, locked contract, mock engine (server)
```

Auth is not implemented. Billing is stubbed only.
