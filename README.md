# Aftertax

See the taxable impact in dollars — before the meeting ends.

**Open the homepage**

```bash
npm install
npm run dev
```

Then open [http://localhost:3000](http://localhost:3000). The **Search** homepage is fund-manager announced estimates plus data tables — not Growth & tax drag. Search **FBGRX** when `GET /distributions` has a still-future unpaid prelim to open Upcoming / announced (ticker · Dist $/sh · % NAV · dates). Search **AMCPX** / **CGHM** to open Paid history for 2026 midyear paids from `/distributions` finals/paid only — never invented from Upcoming. Soft — / Undisclosed / empty only when truly none. Ledger Light, monogram, and locked GTM hero copy are on that page. No Stripe keys are required. Search / Sample Estimates need `NEXT_PUBLIC_DATA_API_URL` (empty, N/A, or Undisclosed if the API is down).

**Fund comparison** is a dedicated **Compare** tab at [http://localhost:3000/compare](http://localhost:3000/compare) (`/?tab=compare` and `/#fund-compare` redirect there; ticker query is preserved). Search-page ticker and fund-name clicks (Highlights, Sample Estimates) select that fund into **Search a fund** and hydrate the same modules as a typed selection — they do not open `/compare?tickers=`. **Fund Comparison** opens the Compare tab — four ticker slots, then `GrowthAndTaxDragModule`, a calendar-year tax/distribution table, then Upcoming / announced. Standalone tax-delta demo: [http://localhost:3000/fund-compare](http://localhost:3000/fund-compare). Import `CompareWorkspace` from `@/components/illustrate`.

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
- Stripe (optional until charge-ready): `STRIPE_SECRET_KEY`, `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`, `STRIPE_PRICE_ID`, `STRIPE_WEBHOOK_SECRET`. Without them, search + illustrate still work and the Unlock CTA says billing is not configured.
- Friends beta: set `FRIENDS_BETA_PASSWORD` (see below). Do not buy Vercel Pro Password Protection.
- **Account store (required for Production login):** connect a private **Vercel Blob** store (or set Upstash Redis REST URL + token). Do not use `/tmp` / `AFTERTAX_ACCOUNTS_PATH` on Vercel Functions — that is why login still said the password was wrong after #277.

Staging is `noindex`. Switch `AFTERTAX_PUBLIC_URL` to `https://getaftertax.com` when ads are green-lit.

## What you will see

- One-screen landing: **Search a fund** as the primary action, then Fund Manager announced estimates + data tables. Header tabs: **Search** (`/`), **Compare** (`/compare`), and **Portfolios** (`/portfolio`). Search does not show Fund Comparison / Import a portfolio shortcuts — those tabs are AppNav only.
- Instant **dollar illustration** after a fund is selected ($1,000,000 holding default, editable federal/state rates, min/max when present), including **Upcoming / announced** (unpaid still-future prelims; empty = Not available / undisclosed) and **Paid history** from `/distributions` finals/paid (year toggle). Highlights stay unpaid announced / same-calendar-year only.
- **Compare** on `/compare`: four empty ticker slots (user-added; **one ticker is enough** — empty slots ignored) plus one shared **Dollars invested** input (default $10,000) that scales Growth starting dollars, tax-drag $ / taxable amounts, calendar-year tax $ / dist $, and upcoming taxable $. Filled tickers then flow through `GrowthAndTaxDragModule`, a ticker × calendar-year tax $ / dist $ table from live `POST /illustrate/compare` `mode: "yoy"` (unmatched = N/A, never fake $0), then Upcoming / announced (unpaid announced only; in-universe empty = **Awaiting Estimate**, not-in-universe = **Add to universe** via `requestTicker` — never invented from paid history). `?tickers=AGTHX` (comma-separated or repeated) still prefills Compare slots; `?left=` / `?right=` / `?ticker=` still work. Search-page ticker clicks no longer navigate here. A plain `/compare` visit starts empty. The Compare tab does not show FundTaxDeltaCompare as the main layout, the fund-search hero, dollar illustration, portfolio books, or highlights. Historical tax drag and Upcoming stay separate. The `/fund-compare` demo still mounts the reusable `FundTaxDeltaCompare` card.
- **Portfolio comparison** on `/portfolio` (and `/portfolio-compare`): Current vs Proposed Allocation start empty — add tickers with **+ Add holding**. Book default $1M + state 0.05. Upcoming / announced (every fund; in-universe empty = **Awaiting Estimate**, not-in-universe = **Add to universe**, never $0), ticker × calendar-year tax $ (2021–2025; unmatched / uncovered = N/A), tax drag %, more/less tax Δ. The Portfolios tab does not show Growth of $X, fund-search hero, dollar illustration, FundCompareRail, or highlights. Export calls `exportToPdf` (freemium gate stubbed).
- **Growth of $X + tax drag** (`GrowthAndTaxDragModule`) is not mounted on Search. The component stays exported for Compare and the standalone demo at `/growth-tax`.
- Soft wall is **on** (10 searches / 3 compare reports / 3 portfolio reviews). Over-limit modules blur with an Unlock CTA; the search box, Request a fund, and ticker slots stay usable. `NEXT_PUBLIC_FREEMIUM_DISABLED=true` bypasses counters for an internal demo.
- Highlights + estimates table sit below the fold as the live Data API universe — not a landing feature grid.
- Live Data API banner. Search / Sample Estimates never merge `seed.ts`. Uncovered or missing values stay empty, N/A, or Undisclosed. Capital Group / American Funds is treated as live ingest; other families show a **coverage gap**.
- Checkout is live when Stripe env is set (`POST /api/checkout` → subscription Checkout Session). Price id `price_1UD6C0RqA7bY5N5qVleZso0d`. Return URLs: `/?checkout=success&session_id={CHECKOUT_SESSION_ID}` stays in this flow; `/?checkout=cancel` is a notice only (no homepage hard block). Manage / cancel is Customer Portal (`POST /api/billing/portal`) with cancel-at-period-end. Without keys the routes return 501.

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
- `POST /illustrate/portfolio/compare` — Current vs Proposed Allocation. Body: `current` / `proposed` `{ label?, holdings[], book_dollars }` with `ticker` + `weight_pct` (or `holding_dollars`), plus `periods: [{year:2021}…{year:2025}]` for the ticker × calendar-year tax $ table. Clients send per-holding `nav_per_share` when search/seed metadata has a NAV (`per_share` `paid_history` rows otherwise drop out) and never send `nav=0`. Deltas are **proposed − current** (`deltas.estimated_tax`, `effective_tax_on_holding`). Upcoming lists every Current/Proposed fund (est. dist $, tax to holder, record, ex-div with year); empty/null upcoming is **Awaiting Estimate** in-universe or **Add to universe** when the ticker is not in the catalog — never $0. Paid History is a list from additive `holdings[].paid_history[]` only (same row shape; newest-first; cap 12). Do not derive from `illustration.components`, `distributions`, or `upcoming`. Do not invent dates. Calendar-year tax is the existing `CalendarYearTaxTable` module — Website keeps it and will add 2025 / denser cells; do not replace or rebuild that matrix. Calendar-year cells read `periods[]` per ticker (`matched: false` / `covered: false` / `gap_reason` / null totals / missing → **N/A**, never $0). Search/seed `nav_per_share` also fills thin year cells (AGTHX/DODIX). Each column shows **Total tax impact** = Σ `upcoming.estimated_tax` above the chart. Current/Proposed tax drag cards read `totals.effective_tax_on_holding` / `totals.estimated_tax` and Δ is `deltas.estimated_tax` (proposed − current) — independent of empty Upcoming. Older payloads without `upcoming` still fall back to `illustration` + `publication_stage_used`. If compare is 404/down, the client double-calls `POST /illustrate/portfolio` and synthesizes deltas; localhost falls back to the sketch fixture. Print/PDF: `exportToPdf(toPortfolioCompareExportModel(result, bookDollars))` — Website wires the button + freemium gate. Product view: `/portfolio`. Standalone demo: `/portfolio-compare`. Import `PortfolioCompare`, `exportToPdf`, and `toPortfolioCompareExportModel` from `@/components/illustrate`.
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

`TICKER_REQUEST_SOURCES` is `["web", "search_miss", "portfolio"]`. Search uses `web` and `search_miss`. Portfolio import and Compare slots call `requestTickerOnPortfolioMiss` / `notifyPortfolioTickerMiss` (`source: "portfolio"`) — never invent fund data while queued. Slot miss empty copy is **Add to universe** (not “No funds match.”). Toast copy matches Search miss: “We’ll work on ingesting this.”

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
2. Instant dollar illustration. Each completed Search load counts toward 10 free searches.
3. After 10 searches / 3 compare reports / 3 portfolio reviews → soft blur + Unlock CTA (`$39 / user / month`). Homepage search box and Request a fund stay usable.
4. Checkout (signed-in Account) returns to the same flow (`?checkout=success`) or a cancel notice (`?checkout=cancel`). No onboarding tour. Cancel at period end from Account → Manage billing.

Highlights and the full estimates table sit below the illustration as the live Data API universe — not a landing feature grid.

## Freemium / Stripe (website owns Checkout)

The Aftertax **website** creates Stripe Checkout Sessions server-side (`POST /api/checkout` → `src/lib/stripe/checkout.ts`) and Customer Portal sessions (`POST /api/billing/portal`). Webhooks: `POST /api/stripe/webhook`.

- Price `price_1UD6C0RqA7bY5N5qVleZso0d` (product `prod_VDXGeprN4QkxsM`, account `acct_1UD66TRqA7bY5N5q`)
- `success_url` / `cancel_url` default to **https://staging.getaftertax.com** until ads are green-lit (`AFTERTAX_PUBLIC_URL` overrides)
- **Do not invent keys.** Without `STRIPE_SECRET_KEY`, Unlock full access is stubbed (501) and search + illustrate still work. The CTA says billing is not configured.
- When test-mode keys exist: set the Vercel env below.

### Vercel env (Production + Preview)

| Var | Required to charge | Notes |
| --- | --- | --- |
| `STRIPE_SECRET_KEY` | yes | Restricted key preferred (`rk_`). Never commit. Mark Sensitive in Vercel. |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | yes | `pk_test_…` / `pk_live_…` |
| `STRIPE_PRICE_ID` | no | Defaults to `price_1UD6C0RqA7bY5N5qVleZso0d` |
| `STRIPE_WEBHOOK_SECRET` | yes, for webhooks | Signing secret from the webhook endpoint |
| `STRIPE_PRODUCT_ID` | no | Defaults to `prod_VDXGeprN4QkxsM` |
| `AFTERTAX_PUBLIC_URL` | recommended | Checkout return origin |

Webhook URL: `https://<host>/api/stripe/webhook`. Events: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`, optional `invoice.paid`. In Stripe Dashboard → Customer portal, set cancellation to **at period end**.

### Smoke (test mode)

1. Set the Vercel env above with **test** keys. Deploy. Confirm `GET /api/billing/entitlement` returns `{ configured: true, subscribed: false }` (no crash when keys are missing — `configured: false` and Unlock says billing is not configured).
2. **Checkout:** Create an Account (homepage sign-in panel) → Unlock full access or Account → Unlock full access. Complete Stripe Checkout test card `4242…`. Land on `/?checkout=success`. Account shows Plan · $39 / user / month · active. Manage billing opens Customer Portal. Cancel there — status becomes cancel-at-period-end; access stays until period end.
3. **Soft wall (signed out or unsubscribed):** In DevTools set cookie `aftertax_freemium` **and** Local Storage `aftertax.freemium.v2` to `{"searches":10,"compareKeys":["A","B","C"],"portfolioKeys":["1","2","3"]}`, then reload. Layout reads the cookie so the first paint already shows `0 free searches left`. Search a fund — Dollar Ill / Upcoming / Paid History are blurred with Unlock; search box + Request a fund still work. `/compare` ticker slots stay editable; modules blur. `/portfolio` allocation slots stay editable; modules blur. Without Stripe env the CTA says billing is not configured (no crash).
4. Webhook: Stripe CLI `stripe listen --forward-to localhost:3000/api/stripe/webhook` or the Vercel URL. Trigger `checkout.session.completed` — `stripeCustomerId` appears on the account.

Paywall copy is locked in `src/lib/copy.ts`. Anonymous counters use `aftertax.freemium.v2` + cookie `aftertax_freemium`. Signed-in counters + subscription status live on the Account row and merge (max / union) on login.

### Friends-beta password gate

In-app shared password so Production can stay off Vercel Pro Deployment Protection ($150/mo). Set **`FRIENDS_BETA_PASSWORD`** in Vercel → Project → Settings → Environment Variables for Production (and Preview if you want the same lock). `BETA_PASSWORD` is an alias. Unset the var to take the gate off when going public. Do not use a `NEXT_PUBLIC_` prefix.

| Value | Behavior |
| --- | --- |
| set | Visiting `/`, `/portfolio`, `/compare`, and other app pages shows `/beta`. Correct password sets an httpOnly cookie (14 days). Refresh stays unlocked. |
| unset | Gate is off. Site works as today. |

`/terms` and `/privacy` stay public. Same-origin `/api/*` mocks and Render `NEXT_PUBLIC_DATA_API_URL` calls are not gated. Contact remains `operations@getaftertax.com`.

### Soft-wall bypass (internal only)

`NEXT_PUBLIC_FREEMIUM_DISABLED` short-circuits every free-tier check and the soft-wall overlay (`src/lib/freemium.ts` / `src/lib/billing/limits.ts`). **Default is off** (wall on).

| Value | Behavior |
| --- | --- |
| unset / `false` / `0` / `off` | 10 searches / 3 compares / 3 portfolio reviews, then blur + CTA |
| `true` / `1` / `on` | Unlimited; counters ignored |

## Saved lists and portfolios (account-scoped)

Lists (`/lists`) has **Save** and **Open** at the top. Save names the current ticker list for the signed-in account; Open loads a previously saved list. Existing paste / filter / sort behavior is unchanged.

Contract for Modules: [`docs/saved-assets.md`](docs/saved-assets.md) and `src/lib/saved-assets/contract.ts` (also re-exported from `@/components/illustrate`).

Shared backbone: `GET|POST /api/saved-assets` and `GET|PATCH|DELETE /api/saved-assets/:id`. Types:

| `type` | Payload | Who owns it |
| --- | --- | --- |
| `list` | `{ tickers: string[] }` | Website Lists |
| `portfolio` | `{ version: 1, books }` envelope — Current/Proposed books + holdings (opaque) | Modules |

Every row is scoped to `accountId`. User A cannot read user B.

**Account:** email/password sign-up and sign-in on the homepage right-hand panel (signed-out only), Account menu, and `/account`. Signed httpOnly `aftertax_account` cookie. Friends-beta shared password stays separate — the `/beta` field is `friends-beta-password` with `autocomplete=off` so it cannot steal Account login. Saved-assets without a session is **401**.

**Forgot password:** `/account/forgot` → hashed one-time token (1 hour, single use) → Resend transactional mail from **`noreply@getaftertax.com`** with `https://getaftertax.com/account/reset?token=…` → `POST /api/account/reset` sets the new scrypt hash, invalidates the token, and signs in. Not Gmail. `POST /api/account/forgot` always returns 200 for a valid email (no account-existence leak). The user-facing copy depends only on whether mail is configured — it does **not** say a message was sent when `RESEND_API_KEY` is unset. Non-prod logs the reset URL; production does not.

**Production email env (Vercel → Project → Settings → Environment Variables, Production + Preview):**

| Var | Required | Notes |
| --- | --- | --- |
| `RESEND_API_KEY` | **yes, to actually send** | Resend API key. Without it, Forgot Password still creates a hashed token but the UI says no email was sent. |
| `AFTERTAX_MAIL_FROM` | no | Defaults to `Aftertax <noreply@getaftertax.com>`. Change only after that address is verified on Resend. |
| `AFTERTAX_PUBLIC_URL` | recommended | Reset-link origin. Production: `https://getaftertax.com`. |

**DNS (getaftertax.com) — copy the exact records from Resend → Domains → Records.** Do not invent values.

1. Add domain `getaftertax.com` in the Resend dashboard (send from `noreply@getaftertax.com` once verified; no mailbox required).
2. Publish the **DKIM** record(s) Resend shows (`resend._domainkey` TXT, or the newer CNAME set).
3. Publish the **SPF** record(s) Resend shows (classic: SPF TXT + return-path MX, often on a `send` subdomain; newer domains may use CNAMEs). Merge with any existing SPF — one `v=spf1` TXT per host.
4. Optional but recommended: **DMARC** at `_dmarc.getaftertax.com` (`v=DMARC1; p=none; rua=mailto:operations@getaftertax.com` to start).
5. Wait for Resend status **verified** (often minutes, up to 72 hours). Then set `RESEND_API_KEY` on Vercel and redeploy.

Until DNS + `RESEND_API_KEY` are in place, Forgot Password is honest: same 200 for known/unknown emails, copy says mail is not configured, non-prod logs the reset URL.

**Auth root cause (login always “wrong password”):** Two separate bugs stacked.

1. **#277 (fixed, not enough):** Account rows lived in a process-local JSON snapshot. The file store now reloads on every read/write, and session cookies honor `x-forwarded-proto`. Friends-beta stays on `friends-beta-password`. scrypt + timing-safe equal is unchanged.
2. **Production after #277 (this fix):** Vercel serverless still defaulted to `/tmp/aftertax-accounts.json`. `/tmp` is ephemeral and **not shared across instances**. Sign-up on instance A wrote a hash; sign-in on instance B found no row and returned “Email or password is wrong.” Pinning `AFTERTAX_ACCOUNTS_PATH` was never done — there is no persistent disk on Vercel Functions.

Accounts now persist to a durable shared store:

| Priority | Backend | Env |
| --- | --- | --- |
| 1 | Upstash Redis / Vercel KV | `UPSTASH_REDIS_REST_URL` + `UPSTASH_REDIS_REST_TOKEN` (aliases `KV_REST_API_URL` / `KV_REST_API_TOKEN`) |
| 2 | Private Vercel Blob | `BLOB_READ_WRITE_TOKEN` or `BLOB_STORE_ID` (OIDC on Vercel). Optional `AFTERTAX_ACCOUNTS_BLOB_PATH` |
| 3 | JSON file | Local/CI. `AFTERTAX_ACCOUNTS_PATH` or `.data/accounts.json`. Force with `AFTERTAX_ACCOUNT_STORE=file` |

**Production setup (do this before relying on login):** Vercel → Storage → Create Database → **Blob** (Private) → connect to this project (Production + Preview). Redeploy so `BLOB_READ_WRITE_TOKEN` / `BLOB_STORE_ID` are present. The JSON document is private (`get(..., { useCache: false })`) and keeps existing scrypt hashes. Redis is used automatically if those REST vars are already present.

**Migration:** leftover file-store rows (including `/tmp` on the current instance) are merged into the durable store once when it is empty-of-that-email. Durable hashes win on email collision. Accounts that only existed on now-dead instances **cannot be recovered** — those users must Create account again (Forgot Password cannot find a missing row). We do not invent or reset passwords.

On Vercel without Blob or Redis, sign-up / sign-in / forgot / reset return **503** (`Account storage is not configured…`) instead of writing a `/tmp` row that other instances will treat as a wrong password.

Session cookies still honor `x-forwarded-proto`. Hash compare is still scrypt + timing-safe equal — no bypass. Plaintext passwords are not logged.

**Stripe Checkout:** create/link a Customer on the **same account email** and set `stripeCustomerId`. Subscription status updates from the webhook. Soft-wall still applies until the account is entitled (`active` / `trialing` / `past_due`, or canceled with time left). Save/Open is not gated on Checkout.

**Persistence:** JSON file via `SavedAssetStore` — local `.data/saved-assets.json`, Vercel `/tmp/aftertax-saved-assets.json` (ephemeral filesystem). Override with `SAVED_ASSETS_PATH`. No new cloud vendor. Swap the store for Neon/Postgres later without changing the HTTP contract.

**Modules:** Compare (`/compare`) and Portfolios (`/portfolio`) have **Open** + **Save** against the same session/API Lists uses. Import `listSavedAssets` / `saveSavedAsset` / `parsePortfolioBooksPayload` / `portfolioBooksAreSavable` from `@/components/illustrate`. `PortfolioCompare` exposes `booksApiRef` + `headerActions`; `PortfolioSaveOpenActions` is the shared toolbar. Do not invent holdings. Soft-wall / Checkout stay off.

## Code structure

```
src/
  app/                 App Router + mock API routes
  components/          Search, highlights, illustrate, landing, paywall
  data/                Data API repository + query helpers (seed.ts is test/mock only)
  lib/account/         Stub account session cookie (Stripe identity later)
  lib/saved-assets/    Account-scoped list + portfolio store + HTTP contract
  lib/illustrate/      Typed client, locked contract, mock engine (server)
```

Auth is email/password Account (`aftertax_account`). Billing is stubbed only. Do not implement Checkout here.
