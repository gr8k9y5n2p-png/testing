# Aftertax

See the taxable impact in dollars — before the meeting ends.

Aftertax is a search-first workspace for wholesalers and financial advisors. This repo slice is the **website UI**: fund search, highlights, holding size, adjustable tax rates, and results. The Data team owns ingest, `GET /distributions`, and production `POST /illustrate` math (see PR #2).

## Run locally

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Canonical host: **https://getaftertax.com**.

- `npm run build` / `npm run lint` / `npm run typecheck`

## What you will see

- One-screen landing: hero (taxable impact in dollars) + **Search a fund** as the primary action. **Import a portfolio** is secondary and opens the paywall.
- Instant **dollar illustration** after a fund is selected ($1,000,000 holding default, editable federal/state rates, min/max when present).
- Soft counter (`3 of 3 free searches left` → `2 of 3…` → `0 free searches left`). After 3 unique tickers, the next search opens the paywall.
- Highlights + estimates table sit below the fold as the sample universe — not a landing feature grid.
- Sample/demo data banner. Capital Group / American Funds is treated as live ingest; other families show a **coverage gap**.
- Checkout is stubbed (`POST /api/checkout` → 501). Price id `price_1UD6C0RqA7bY5N5qVleZso0d`. Return URLs: `/?checkout=success` stays in this flow; `/?checkout=cancel` reopens the paywall. No onboarding tour.

## Mock vs real Data API (PR #2)

The browser **does not** compute tax. Clients in `src/lib/illustrate/` POST the locked contract.

| Mode | How |
| --- | --- |
| Demo (default) | Local mocks: `POST /api/illustrate`, `POST /api/illustrate/portfolio` |
| Data team FastAPI | `NEXT_PUBLIC_DATA_API_URL=http://localhost:8000` |

With the Data API base set, Aftertax calls:

- `POST /illustrate` (selector by ticker/family; response normalized to the locked UI shape)
- `POST /illustrate/portfolio`
- `GET /distributions`, `GET /coverage`, `GET /fund-families`
- `POST /coverage/gaps`

If the Data API is not running, illustrate falls back to the local mock.

Run both PRs side by side:

```bash
# Data API (PR #2), typically port 8000
# UI (this PR)
NEXT_PUBLIC_DATA_API_URL=http://localhost:8000 npm run dev
```

Optional override for illustrate only: `NEXT_PUBLIC_ILLUSTRATE_URL=http://localhost:8000/illustrate`.

Types live in `src/lib/illustrate/types.ts` and must not drift. The client POSTs that JSON as-is (`selector`, not `selectors`). Mock `POST /api/illustrate` returns `tax_rates_applied`, `components[]`, `totals`, and `warnings[]`.

Request: `holding_dollars`, `distribution_ids` **or** `selector: { fund_family, fund_identifier }`, optional `nav_per_share`, `tax_rates`, `combine_state_with_federal`.

If `tax_rates` is omitted, the mock applies ordinary/STCG `0.37`, LTCG/QDI `0.20`, state `0.0`. The UI sends explicit advisor defaults (including state `0.05`) on every request.

`% of NAV` works with holding dollars alone. `$ / share` requires `nav_per_share` (422 `nav_required` otherwise).

### Rate mapping (locked)

- `ordinary_income`, `special_dividend`, `return_of_capital`, `other` → ordinary (+ state if combined)
- `long_term_capital_gains`, `total_capital_gains` → LTCG (+ state)
- `short_term_capital_gains`, `qualified_short_term_gains` → STCG (+ state)
- `qualified_dividend` → QDI (+ state)
- `total` → ordinary unless the row is skipped

Prefer one `publication_stage` / `as_of` snapshot in the panel so midyear paid + preliminary % NAV are not double-counted.

## Search data vs `GET /distributions`

Search and highlights currently use `src/data/seed.ts`. When the Data API is up, set `NEXT_PUBLIC_DATA_API_URL` (see `.env.example`). Prefer `GET /distributions` once those rows can be aggregated into the table model; until then the seed remains.

## Coverage gaps

Live ingest today: **Capital Group / American Funds**. Planned top-10 families (with `coverage_tier` / `priority` stubs in `src/lib/coverage.ts` and `GET /api/fund-families`): BlackRock/iShares, Vanguard, Fidelity, State Street/SPDR, J.P. Morgan AM, Goldman Sachs AM, PIMCO, Invesco, and T. Rowe Price.

Uncovered holdings are flagged in the fund picker (Gap vs Live) and the illustrate panel so tax impact is not silently understated. Selecting a gap ticker POSTs `POST /api/coverage/gaps` (or Data team `POST /coverage/gaps` when `NEXT_PUBLIC_DATA_API_URL` is set).

## Funnel (this UI)

1. Land → search a fund (primary). Import a portfolio is a paywall tease.
2. Instant dollar illustration. Counter: `2 of 3 free searches left`.
3. After 3 unique fund searches → paywall (`$39 / user / month`).
4. Checkout stub returns to the same flow (`?checkout=success`) or paywall (`?checkout=cancel`). No onboarding tour.

Highlights and the full estimates table sit below the illustration as the sample universe — not a landing feature grid.

## Freemium / Stripe (website owns Checkout)

The Aftertax **website** creates Stripe Checkout Sessions server-side (`POST /api/checkout` → `src/lib/stripe/checkout.ts`).

- Price `price_1UD6C0RqA7bY5N5qVleZso0d` (product `prod_VDXGeprN4QkxsM`, account `acct_1UD66TRqA7bY5N5q`)
- `success_url` → `https://getaftertax.com/?checkout=success` (same search/portfolio flow)
- `cancel_url` → `https://getaftertax.com/?checkout=cancel` (reopens paywall)
- **Mocked demo does not need live keys.** Without `STRIPE_SECRET_KEY`, Unlock Aftertax is stubbed (501) and the funnel still works.
- When keys are available: set `STRIPE_SECRET_KEY` and optional `STRIPE_PRICE_ID` / `AFTERTAX_PUBLIC_URL`. The same route creates a live Checkout Session and redirects.

Paywall copy is locked in `src/lib/copy.ts`. 3 free unique fund searches use client `localStorage` for this demo.

## Code structure

```
src/
  app/                 App Router + mock API routes
  components/          Search, highlights, illustrate, landing, paywall
  data/                Seed + query helpers for the estimates table
  lib/illustrate/      Typed client, locked contract, mock engine (server)
```

Auth is not implemented. Billing is stubbed only.
