# Estimated Taxable Distributions

Searchable template for **fund-manager estimated taxable distributions**, aimed at asset management teams and financial advisors.

Fund complexes (for example American Funds) publish year-end estimates on their websites. This first slice uses **seeded sample data** so the product can be reviewed as a stakeholder template. Live ingest, authentication, and billing are intentionally out of scope.

## Run locally

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

Useful scripts:

- `npm run build` — production build
- `npm run lint` — ESLint
- `npm run typecheck` — `tsc --noEmit`

## What you will see

- Global search across fund name, ticker, CUSIP, family, category, and distribution year
- Filters for family, category, and year
- Results table with estimated distribution ($/share and **% of NAV**), as-of / published dates, and vs category average
- Three highlight modules: **most recent**, **largest (% of NAV)**, and **well above / below category average**
- A persistent **Sample / demo data** banner

JSON endpoints (same seed, same queries):

- `GET /api/funds?q=&family=&category=&year=`
- `GET /api/highlights`

## Sample data vs future ingest

| Now | Later |
| --- | --- |
| `src/data/seed.ts` — ~50 illustrative 2026 estimates | Manager-site / API ingest into a database |
| `SeedDistributionRepository` in `src/data/repository.ts` | Postgres (or similar) adapter implementing the same interface |
| Category averages computed in `src/data/queries.ts` | Stored or materialized peer stats refreshed with ingest |
| No auth | Subscription SaaS auth + entitlements |

Tickers are real. Dollar amounts, dates, and CUSIPs are **illustrative** and must not be used for tax, trading, or client reporting.

## Code structure

```
src/
  app/                 App Router pages and API routes
  components/          Search, table, highlights, chrome
  data/
    types.ts           Typed domain model + repository contract
    seed.ts            Sample funds
    queries.ts         Search, facets, highlight queries
    repository.ts      Swappable data-access implementation
  lib/format.ts        Display helpers
```

Auth and billing are not implemented; modules are kept separate so those can be added without rewriting the data or query layer.
