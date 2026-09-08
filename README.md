# Fund Distribution Estimates API

Backend service that ingests **taxable distribution estimates** published by fund managers and stores them in a searchable database for an Asset Management / Financial Advisor website.

The default demo uses **SQLite** and bundled Capital Group HTML fixtures so the pipeline runs offline. The same SQLAlchemy models work with **Postgres** by changing `DATABASE_URL`.

**Build, not buy.** This service ingests public manager ICI layout files, PDF archives, and HTML. It does not license CapGainsValet, YCharts, or other paid distribution feeds.

**Source preference (historical + ongoing):**

1. **ICI Primary Layout** when the family publishes a filled file (not the blank template on ici.org).
2. **PDF / HTML archives** when no public ICI download exists.
3. Skip JavaScript SPA pages when an ICI or PDF book is available.

Vanguard is the first-choice ICI book: official Primary Layout PDFs on the advisor tax center cover the full fund list. 2021–2025 December rows are a column-safe full-book extract (31-token layout; wrap/DAILY bleed skipped). Other top-AUM families are checked for ICI downloads in rank order; Invesco *lists* ICI Primary files on its open-end tax guide, but no stable public file URL was fetchable (JS / 406), so Invesco stays on PDF/HTML archives. Northern Trust publishes filled ICI Primary Reports (2022–2025) on its tax center; PDF text extraction merges income/CG and includes quarterly lines, so December YE ST/LT are transcribed from the companion capital-gains PDFs (same hub).

**Full-book vs flagship history.** Current-year / published-table fixtures now ingest **every fund listed on that family’s public book** (skip synthetic `ZZ*` parser samples; skip Amundi / Pioneer). The ≥$1B allowlist in `app/sources/aum.py` still applies to **older multi-year archives** when those packs were transcribed as flagships only. It is not a live AUM feed. Illustrate / compare / performance contracts are unchanged.

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
- `GET /performance` / `POST /performance/growth` — Growth of $X fund vs ETF-benchmark monthly series (not tax)
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

## Public HTTPS URL (Website `NEXT_PUBLIC_DATA_API_URL`)

This FastAPI service is **not** the Aftertax Next.js app on `main`. The existing Vercel project (`aftertax/testing`, previews like `testing-*-aftertax.vercel.app`) deploys **Website** from `main` and currently has **Vercel Authentication / Deployment Protection** (unauthenticated `GET /health` 302s to `vercel.com/login`). There is no Railway / Render / Fly token in this environment, and the Vercel MCP integration is not authenticated — **do not invent credentials**.

**Do not** change that Website project’s framework to FastAPI. It would break production `main`.

### Eric — create a dedicated API host (pick one)

**Option A — new Vercel project (Eric already has Aftertax on Vercel)**

1. [Vercel → Add New → Project](https://vercel.com/new) → import `gr8k9y5n2p-png/testing`.
2. Name it `aftertax-data-api` (not `testing`).
3. Set **Production Branch** to `cursor/fund-distribution-ingest-api-85ed` (this API branch) until the API lives in its own repo.
4. Framework: Other / FastAPI. In that **new** project only, add a root `vercel.json` with `"framework": null` and `[tool.vercel] entrypoint = "app.main:app"` in `pyproject.toml`. Do **not** commit those onto this GitHub repo’s shared Website project — that is what broke the `aftertax/testing` preview CI.
5. Environment variables:
   - `FETCH_MODE` = `fixture`
   - `SEED_ON_START` = `true`
   - `DATABASE_URL` = `sqlite:////tmp/distributions.db` (Vercel serverless is ephemeral)
6. **Deployment Protection → Vercel Authentication → Off** (or “Only Preview”) so the Website can call the API without a SSO cookie.
7. Deploy. Copy the production URL, e.g. `https://aftertax-data-api.vercel.app` (no trailing slash).
8. Verify: `curl -sS https://<that-host>/health` → HTTP 200 `{"status":"ok",...}`.

**Option B — Render (Docker, better for SQLite + weekly refresh)**

1. [Render → New → Blueprint](https://dashboard.render.com/select-repo?type=blueprint) → this GitHub repo, this branch (`render.yaml`).
2. Service name `aftertax-data-api`, health path `/health`.
3. Blueprint attaches a 1 GB disk at `/var/data` (`plan: starter`) and sets
   `DATABASE_URL=sqlite:////var/data/distributions.db` so the SQLite book
   survives deploys. Free web services cannot attach a disk.
4. Copy `https://aftertax-data-api.onrender.com` (or the URL Render prints).
5. Verify `GET /health` 200 as above.

**Website env** (project that serves `testing-seven-umber-19.vercel.app`):

```
NEXT_PUBLIC_DATA_API_URL=https://<api-host>
```

No trailing slash. Redeploy Website after setting it. Local Next: `NEXT_PUBLIC_DATA_API_URL=http://127.0.0.1:8000`.

CORS already allows `https://testing-seven-umber-19.vercel.app`, `http://localhost:3000`, `http://127.0.0.1:3000`, and other `https://*.vercel.app` previews (`CORS_ORIGINS` / `CORS_ORIGIN_REGEX`). Tax / illustrate / performance contracts are unchanged.

### Weekly refresh on the public API

Fixture seed on boot (`SEED_ON_START=true`, also implied on Vercel) runs the **same full fixture ingest** as `POST /ingest/fetch {"fund_family":"all","mode":"fixture"}` — every registered family, including Dodge & Cox (`DODIX` / `DODGX`), Vanguard, Fidelity, MFS, First Eagle. Render Blueprint SQLite lives on `/var/data` (persistent disk); a thin American-Funds-only seed used to leave advisors without the book after each ephemeral-filesystem deploy.

The seed starts in a **background thread** after `init_db()` so `GET /health` stays 200 during ingest (`health.seed` is `running` then `complete`). Families commit one at a time; a mid-book failure does not roll back earlier families. Typical full fixture book is ~11k rows and finishes in tens of seconds. Manual ingest is no longer required after a cold start.

```bash
python -m app.cli refresh --mode fixture   # same offline all-family ingest (foreground)
# or
python -m app.cli refresh                  # REFRESH_MODE=auto: live then fixture
```

GitHub Action `.github/workflows/weekly-ingest.yml` (Monday 14:00 UTC + `workflow_dispatch`). For a durable book across restarts, set repo secret `DATABASE_URL` to the **same Postgres** the API uses (`postgresql+psycopg://…`) and install `psycopg[binary]`. Vercel `/tmp` SQLite is ephemeral. Render Blueprint uses `sqlite:////var/data/distributions.db` on a persistent disk (`plan: starter`) so the book survives deploys; `SEED_ON_START` still rebuilds from fixtures on boot.

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

# Growth of $X (AGTHX vs S&P 500 via SPY). Does not touch /illustrate.
curl -s 'http://127.0.0.1:8000/performance?ticker=AGTHX&mode=fixture' | jq '{fund_ticker,benchmark_id,benchmark_label,is_proxy,start_dollars,as_of,points:(.fund.points|length)}'
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
| `per_share` | `shares = shares` or `holding_dollars / nav_per_share`; `distribution_dollars = shares * amount`. **HTTP 422** `{ "code": "needs_nav_or_shares", "detail": "nav_per_share or shares is required when illustrating per_share distributions" }` if neither `nav_per_share` nor `shares` is provided. Same body on `POST /illustrate/compare` when a selected side cannot be priced. |
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

**Sparse history:** Vanguard has ICI December year-end rows for 2021–2025 (≥$1B Admiral / mega ETFs) plus the 2025 YE HTML fixture for VFIAX / VBIAX / VIGAX. Fidelity has the **full 2024–2025 paid DPL6 books** + 2026 estimate (FBGRX plus 349 other 2024 tickers). A YoY `periods[]` pin that misses that `as_of` / year is an explicit **gap** on that side, not a silent $0. American Funds (AMCAP 2024–2025) and T. Rowe Price (TRBCX 2022–2025) have multi-year fixture snapshots. Among ranks 11–20, Northern Trust (NOSIX 2022–2025), BNY (DGAGX 2022–2025), and Schwab (SWTSX 2022–2025) have multi-year paid books; UBS and Nuveen stay single-vintage. **Amundi / Pioneer is off the history ladder** (existing 2025 fixture only). History packs prefer **US-domiciled** managers.

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
- `left` / `right` with the same selectors and different `as_of` (no `periods` required), or
- `left` / `right` (or `selectors`) **without** `periods[]` and **without** `as_of` pins — the API expands vintages from stored `as_of` / `ex_date` calendar years and then pair-zips them (N years → N−1 bars, `year` = newer). Response shape is unchanged. A missing book still never emits `year: 0` (falls back to the current calendar year).

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

A missing side is **not** a 404. That illustration is empty (`matched: false`, tax/distribution totals **null** / N/A — not `"0.00"`) and a note is appended so the chart still has a period row. Period deltas are also null when either side is unmatched. A published `$0` / `0%` of NAV stays `"0.00"` with `matched: true`.

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

## Growth of $X (`GET /performance`, `POST /performance/growth`)

Interactive Modules can mount a **fund vs benchmark line chart** without calling tax endpoints. Tax YoY bars stay on `POST /illustrate/compare`. Weekly `python -m app.cli refresh` still ingests **distribution estimates only** — it does not refresh performance series.

**Hero seed (fixture + live Yahoo chart):** `AGTHX` vs **S&P 500 via SPY**. Same source also covers `AMCPX`, `FBGRX`, `VFIAX`, `DODIX`, and `VTIAX`. Default benchmarks are **ETFs only** (no licensed S&P / Bloomberg / MSCI index feeds):

| Asset class | Default ETF | Label (`benchmark_label` / `benchmark_tracks`) |
| --- | --- | --- |
| `equity` (default) | `SPY` | S&P 500 via SPY ETF total return |
| `fixed_income` | `AGG` | Bloomberg US Aggregate via AGG ETF total return |
| `international` | `VXUS` (not ACWX) | MSCI ACWI ex USA via VXUS ETF total return |

v1 is **ETF series only**. There is no licensed S&P / Bloomberg / MSCI index feed and no future index-license path. UI copy may say a line tracks the S&P 500, Agg, or ACWI ex USA; `benchmark_id` is still the ETF, and `is_proxy` is `true` for SPY / AGG / VXUS.

Pass `benchmark` to override, or send `asset_class` / `benchmark_hint` (`equity` | `fixed_income` | `international`) to pick the default. Response always includes `benchmark_id`, `benchmark_label`, `benchmark_tracks`, and `is_proxy`.

**Inputs:** `ticker` and/or `fund_identifier` (aliases: `the-growth-fund-of-america` → AGTHX; `amcap-fund` / `AMCAP` → AMCPX), optional `benchmark`, `start_dollars` (default **10000**), optional `start_date` / `end_date`, `mode` (`fixture` | `live` | `auto`; omit to use `FETCH_MODE`, which is `fixture` in CI).

**Units**

| Field | Unit |
| --- | --- |
| `fund.points[].adj_close` / `benchmark.points[].adj_close` | `usd_per_share_adjusted` (Yahoo split- and dividend-adjusted close) |
| `monthly_return` | `decimal` total return vs prior month (`0.01` = 1%). Null on the first point. |
| `growth_of_x` | `usd` — cumulative dollars if `start_dollars` was invested at the first overlapping month |
| `as_of` | Latest source date on the aligned series (ISO date) |
| `frequency` | `monthly` (aligned by year-month, not exact calendar day) |

Fixtures live in `fixtures/performance/*.json` (recorded Yahoo monthly chart). `mode=live` hits `query1.finance.yahoo.com` and falls back to fixtures when the public chart is unavailable. Returns are **not invented**.

```bash
# Locked hero: Growth of $10,000 — AGTHX vs S&P 500 (SPY proxy)
curl -s 'http://127.0.0.1:8000/performance?ticker=AGTHX&mode=fixture' \
  | jq '{fund_ticker,fund_name,benchmark_id,benchmark_label,is_proxy,start_dollars,start_date,end_date,as_of,disclaimers}'

# Same payload as JSON (date window + custom start)
curl -s -X POST http://127.0.0.1:8000/performance/growth \
  -H 'Content-Type: application/json' \
  -d '{
    "ticker": "AGTHX",
    "benchmark": "SPY",
    "start_dollars": 10000,
    "start_date": "2020-01-01",
    "end_date": "2025-12-31",
    "mode": "fixture"
  }' | jq '{as_of, fund: (.fund.points[-1]), benchmark: (.benchmark.points[-1])}'

# Asset-class defaults: DODIX → AGG, VTIAX → VXUS
curl -s 'http://127.0.0.1:8000/performance?ticker=DODIX&mode=fixture' | jq '{benchmark_id,benchmark_label,is_proxy}'
curl -s 'http://127.0.0.1:8000/performance?fund_identifier=the-growth-fund-of-america&mode=fixture' | jq .fund_ticker
```

`disclaimers[]` always states that performance is illustrative only, is **not tax advice**, and that default series are ETF total-return proxies rather than official index levels.

## Full-book fixture expansion (overnight wave)

Goal: for **existing US-domiciled adapters**, ingest every **mutual fund and ETF** on the published distribution / capital-gains book — not 1–2 sample tickers. **Skip SMAs / separate accounts / institutional SMA sleeves** (drop those rows when a table mixes products). **Skip Amundi / Pioneer.** Do not invent amounts. Synthetic `ZZ*` parser samples stay samples. Large families should clear **>50 MF/ETF funds** when the public book lists that many.

**Wave 1:** unique tickers **431 → 1,168**; funds **482 → 1,298**.

**Wave 2:** unique tickers **1,168 → 2,165**; funds **1,298 → 2,434**.

**Wave 3 (MF/ETF-only + large-family 50-fund bar):** unique tickers **2,165 → 2,174**; funds **2,434 → 2,519**. SMA rows dropped. Tax / illustrate / performance contracts and weekly refresh are unchanged.

**Wave 4 (same MF/ETF filter; keep pushing thin large books):** unique tickers **2,174 → 2,205**; funds **2,519 → 2,630**. BNY ETF $0.00 book, JPM MMKT 19a, MSIM ETF income table, plus ranks 31–35 paying-fund PDFs (JH / Hartford / Macquarie). Tax / illustrate / performance contracts and weekly refresh are unchanged.

**Wave 5 (ranks 1–40 only):** ranks 1–40 unique tickers **1,771 → 1,878**; funds **2,112 → 2,294**. Vanguard 2021–2023 ICI are column-safe full December books (239 → **297** tickers; wrap/DAILY name bleed dropped so `fund_name` stays ≤512). Artisan cleared 50 tickers via the 2025 Year-End Tax Reporting ICI PDF (2 → **51**). John Hancock cleared 50 funds (45 → **56**). First Eagle open-end estimate book expanded (3 → **11**). Thrivent / Calamos / Wasatch / GMO Trust paying books expanded. No new work on ranks 41–110. Capital Group / BlackRock OEF / Invesco MF ticker enrichment was not possible — official books are name-only. SSGA / GS / PIMCO / UBS / Franklin / Schwab remain SPA or 403.

**Wave 6 (ranks 1–40 only):** ranks 1–40 unique tickers **1,878 → 1,924**; funds **2,294 → 2,505**. Highest-impact unlocks: MFS 2025 % of NAV fly PDF is now the full published book (2 → **175** funds; cleared 50). First Eagle 2024 official paid PDF is the full share-class book (3 → **40** tickers). Northern Trust recovered NOMIX / NSGRX / NSCKX CG plus December ICI income-only equity rows where the CG book is em-dash (13 → **22**). ICI totals for CG-paying NT tickers (NOSIX) were not stored as income (would double-count). No new work on ranks 41–110. Amundi skipped. SMAs / interval / CEF omitted.

**Wave 7 (year-depth, ranks 1–40 only):** Fidelity 2024 DPL6 is now the **full 350-ticker** Wayback book (was FBGRX-only). American Century gained the official **2022** retail estimate book (TWCGX LT $0.7247; 266 non-zero share classes). MFS unlocked official 10-year Excel December YE **2021–2024** for MIGHX / MITTX. Principal product pages added **2023–2024** paid YE (PQIAX / PEMGX). Artisan 2021–2023 ICI PDFs remain public but transposed / not column-safe. CGHM left as-is (inception 6/25/24; 2024–2025 official tables em-dash).

**Wave 8 (year-depth, ranks 1–40 only):** MFS 10-year Excel expanded beyond MIGHX / MITTX to official Class A product pages (MEIAX / MFEGX / MFRFX / OTCAX / MVCAX / MSFRX / MGRAX / MGIAX / MNDAX / MTCAX / MMUFX). Northern Trust added the official **2021** equity CG book (NOSIX LT $0.985777). Macquarie added the official **2023** CGE-RET-ACT paying book (WSTAX LT $5.331; 20 Class A tickers). Fidelity 2021–2023 still HPDY SPA / no CDX prior-year HTML. ACI 2021/2024 siblings 404 (unversioned September PDF is the 2023 book). Artisan 2021–2023 ICI public but token order / Box 1a breakdown not column-safe. First Eagle 2022 skipped (prior 403). Invesco ICI still 406. CGHM / YoY / render.yaml disk left as-is.

**Year-depth before → after (fixture ingest; calendar year on `as_of` or `ex_date`; ranks 1–40 movers):**

| Family | Before (tickers / year) | After |
| --- | --- | --- |
| MFS | 2021–2024:2 / 2025:175 / 2026:2 | **2021:13** / **2022:12** / **2023:11** / **2024:12** / **2025:180** / **2026:3** |
| Northern Trust | 2022–2024:3 / 2025:22 | **2021:19** / 2022–2024:3 / 2025:22 (24 unique tickers) |
| Macquarie | 2024:3 / 2025:21 | **2023:20** / 2024:3 / 2025:21 (26 unique tickers) |
| Fidelity | 2024:350 / 2025:349 / 2026:15 | unchanged (2021–2023 HPDY SPA) |
| American Century | 2022:266 / 2023:350 / 2025:389 | unchanged (2021/2024 siblings 404) |
| Artisan | 2024:46 / 2025:51 / 2026:2 | unchanged (2021–2023 ICI not column-safe) |

**Advisor-visible N/A gaps (smoke heroes; YoY `matched=false`, totals null — not invented $0):**

| Hero | Years present | Advisor-visible N/A | Why |
| --- | --- | --- | --- |
| VFIAX / VBIAX / VIGAX | 2021–2025 | none in 2021–2025 | ICI December + YE HTML |
| TRBCX | 2021–2025 | none in 2021–2025 | YE HTML + 2021–2022 PDFs |
| DODIX | 2021–2025 | none in 2021–2025 | Tax letter + product API |
| FBGRX | 2024–2026 | **2021–2023** | HPDY SPA; no CDX prior-year HTML |
| AMCPX / AGTHX | 2021–2025 (name-keyed) | ticker-only score looks empty | Aliases still resolve AMCAP / Growth Fund of America |
| CGHM | 2026 midyear only | **2021–2025** | Inception 6/25/24; official 2024–2025 YE em-dash (no CG — not stored as $0) |

| Rank | Family | Before (tickers / funds) | After | Book used | Full-book vs flagship history |
| --- | --- | --- | --- | --- | --- |
| 1 | BlackRock / iShares | 12 / 12 | **44 / 121** | iShares ETF CG HTML + BlackRock 2025 open-end MF book | 44 ETF payers + 77 OEF funds (Investor A when listed). SMAs skipped. |
| 2 | Vanguard | 26 / 26 | **297 / 297** | Column-safe full ICI December 2021–2025 (31-token layout) | **2021–2025 full December.** Wrap/DAILY rows omitted. 2025 omits VFIAX/VBIAX/VIGAX (YE HTML). YE page is SPA. |
| 3 | Fidelity | 15 / 15 | **350 / 350** | Live prior-year paid table `FIIS_SP10_DPL6` + estimate `FIIS_SP52_DPL6` | Estimate table is still “funds expecting CG” (15). Prior-year paid is the full book. |
| 5 | J.P. Morgan | 2 / 2 | 2 / **38** | Full 2025 Section 19a Appendix A (open-end + ETF + 4 MMKT LT) | Notices are unsplit CG $/share except MMKT LT. SEEGX / JLGMX keep the Large Cap Growth LT mapping. No 2024 19a. |
| 7 | American Funds | 3 / 46 | **22 / 84** | Live 2025 YE HTML | 2025 YE is the public table. 2024 YE + estimate samples unchanged (name-heavy). |
| 9 | Invesco | 2 / 5 | **11 / 53** | Full 2025 MF estimate PDF + full 20 Nov 2025 ETF press-release table | SMA High Yield Bond skipped. PDF has no MF tickers. 2024 estimate still thin. |
| 10 | T. Rowe Price | 18 / 18 | **232 / 232** | Live 2023–2025 YE HTML | **2023–2025 full-book.** 2022 YE + prelim remain PDF flagship transcriptions. |
| 13 | BNY Mellon | 3 / 3 | 2 / **42** | Full 2025 MF paying-fund PDF + 12-ETF $0.00 book | Tickers only for DGAGX / PEOPX. Paid YE product pages still flagship. ETF PDF prints published $0.00 (stored). |
| 15 | Northern Trust | 5 / 5 | **22 / 22** | 2025 equity CG PDF + ICI Dec income-only | NOMIX / NSGRX / NSCKX recovered. ICI totals stored as income only when CG book is em-dash. FI daily lines omitted. |
| 18 | Dimensional | 3 / 3 | **140 / 140** | Full 2025 CG PDF (published $0.000 kept) | 2025 full-book. 2024 paid PDF still flagship-only. |
| 20 | Amundi / Pioneer | 4 / 4 | 4 / 4 | **Skipped** | Off the expansion ladder. |
| 22 | Janus Henderson | 3 / 3 | **222 / 222** + **149–191 ICI tickers / year** | **2021–2025 ICI Primary paid YE** (full share-class) + 2025 final estimate PDF | ICI is the paid book (JDCAX LT $4.95363 / $0.02107 / $3.88875 / $5.46939 / $6.96694). Forty Fund is on 2021 ICI (absent from the 2021 FINAL PDF). 2023–2024 estimate PDFs still A-share flagships. |
| 23 | American Century | 3 / 3 | **389 / 389** + **350 / 350 (2023)** + **266 / 266 (2022)** | Full 2025 + 2023 Wayback + official 2022 retail estimate PDFs | Paid TWCGX product page still flagship. 2022 TWCGX LT $0.7247. 2024 unversioned PDF is the 2025 book. 2021 sibling 404. |
| 27 | AllianceBernstein | 3 / 3 | 3 / **19** | Full 2025 paying-fund estimate PDF | Class A tickers only for AGRFX / APGAX / ABASX. 2023 book still flagship. |
| 29 | Virtus | 3 / 3 | 3 / **4** | Full listed June 2026 estimate PDF (4 funds) | 2025 paid / 2024 19(a) still flagship. |
| 41 | Harbor | 3 / 3 | 3 / **9** | 2025 estimate PDF Institutional rows | Tickers only where already identified (HACAX / HASCX / HAIDX). |
| 43 | Voya | 3 / 3 | 3 / **17** | 2025 estimate PDF paying funds | Class A tickers only for NLCAX / VYCAX / NMCAX; other rows are PDF names. |
| 51 | SEI | 0 / 3 | 1 / **51** | Full 2025 paying-fund estimate PDF | Fund-level (QALT ticker when printed). All-dash rows omitted. |
| 52 | Brown Advisory | 4 / 4 | 4 / **17** | Full 2025 Inst/Inv/Adv estimate PDF | Tickers only for BAFFX / BAFGX / BAFWX / BVALX. All-dash funds omitted. |
| 54 | VanEck | 3 / 3 | **13 / 13** | Full 2025 mutual-fund estimate PDF | Printed `None` CG omitted. CM Commodity ‡ estimates-to-come omitted. |
| 55 | WisdomTree | 4 / 4 | **7 / 7** | Full 2025 final CG PDF (payers only) | Dashed no-CG rows omitted, not stored as $0. |
| 56 | AQR | 4 / 4 | **75 / 75** | Full 2025 I/N/R6 estimate PDF | Diversifying Strategies uses the later 12/19–12/23 dates. |
| 57 | Causeway | 3 / 3 | **10 / 10** | Full 2025 Institutional + Investor final PDF | — |
| 58 | Alger | 3 / 3 | **84 / 84** | Full 2025 share-class PDF | International Small Cap ALCZX collision omitted. Published $0.00 stored. |
| 16 | Morgan Stanley | 3 / 3 | **16 / 16** | Full listed 2025 ETF YE income table | CG columns were em-dash / 0.00% (omitted as $0 CG). Open-end YE PDF still Akamai-blocked. |
| 31 | John Hancock | 3 / 3 | 3 / **56** | Full 2025 CG + income-only MF/ETF rows from the same PDF | Closed-end rows skipped. All-dash omitted. 2022–2024 still A-share flagships. |
| 34 | Hartford | 3 / 3 | 3 / **25** | Full 2025 paying-fund estimate + equity/FI finals | No-pay list omitted. Tickers only for HFMCX / HAIAX / IHGIX. 2024 final still flagship. |
| 35 | Macquarie | 3 / 3 | **21 / 21** | Full 2025 paying-fund estimate PDF (Class A) | No-pay list omitted. 2024 paid still flagship. |
| 33 | Thrivent | 3 / 3 | 3 / **13** | Full 2025 paying-fund HTML table | Tickers only for TMSIX / IILGX / THLCX. Unlisted funds paid no CG. |
| 36 | First Eagle | 3 / 3 | **40 / 40** | 2025 open-end estimate + full 2024 share-class paid PDF | Class A tickers from official 2024 PDF. Interval/CEF omitted. Footnote-b income omitted. |
| 37 | GMO | 3 / 3 | 3 / **29** | Full GMO Trust July 2026 estimate PDF | Published $0.000 stored. Notes C/D omitted. Australia trusts skipped. |
| 38 | Artisan | 2 / 2 | **51 / 51** | Column-safe 2024–2025 Year-End Tax Reporting ICI PDFs | December income + any-month ST/LT. 2024 LT at token 11. 2021–2023 ICI public but transposed (not column-safe). YTD HTML keeps ARTKX 2026 income. |
| 39 | Calamos | 3 / 3 | 3 / **13** | Full 2025 paying-fund estimate PDF | All-dash omitted. Class A tickers only where previously identified. |
| 40 | Wasatch | 3 / 3 | 3 / **13** | Full 2025 listed-fund estimate PDF | Investor tickers only for WGROX / WAIGX / WMCVX. |

**Still thin (public book not column-safe / SPA / 403):** State Street (Angular; `ZZSSGA` sample), Goldman / PIMCO (samples), UBS (403 / unparseable price page), Franklin (SPA + CEF 19a only), Schwab (SPA family grid), Dodge (Q1 2026 PDF is 2 funds; December tax-letter URL returned the foreign-source booklet), Nuveen (document viewer is JS; no fetchable PDF), Columbia 2025 mid-year all-funds PDF (wrap-unsafe), William Blair 2025 PDF (text extract reverses columns). MFS 2025 fly PDF is the full %NAV book (name-keyed; official Class A tickers where product pages identify them).

**Large families still under 50 MF/ETF funds, and why**

| Rank | Family | Funds now | Why under 50 |
| --- | --- | --- | --- |
| 4 | State Street / SPDR | 3 | Angular SPA; no stable public XLSX/HTML book |
| 5 | J.P. Morgan | 38 | Full 2025 19a Appendix A exhausted (open-end + ETF + 4 MMKT LT). No broader YE HTML |
| 6 | Goldman Sachs | 2 | Advisor tax center 403; sample only |
| 8 | PIMCO | 2 | No public HTML estimate grid; `ZZ*` sample |
| 11 | UBS | 4 | Estimate PDF 403 / rotating JCR; price page unparseable |
| 12 | Franklin Templeton | 1 | Open-end grid is SPA; CEF 19a only |
| 13 | BNY Mellon | 42 | Full 2025 MF paying-fund PDF (30) + ETF $0.00 book (12) exhausted |
| 14 | Nuveen | 4 | Document viewer is JS; no fetchable PDF |
| 15 | Northern Trust | 22 | Equity CG + ICI income-only exhausted; FI is daily/monthly (not stored as YE income) |
| 16 | Morgan Stanley | 16 | 2025 ETF YE income table exhausted; open-end YE PDF Akamai-blocked |
| 17 | Schwab | 3 | Family annual grid is JS SPA |
| 19 | Columbia Threadneedle | 4 | 2025 mid-year all-funds PDF wrap-unsafe |
| 20 | Amundi / Pioneer | 4 | **Skipped** (non-US parent) |
| 21 | Allspring | 2 | Family estimate PDFs gated |
| 24 | Dodge & Cox | 4 | Public Q1/tax-letter books are small; no full YE CG grid |
| 26 | Lord Abbett | 3 | Public PDF is $0 no-pay list only |
| 27 | AllianceBernstein | 19 | Full 2025 paying-fund PDF exhausted (19 listed) |
| 28 | Federated Hermes | 1 | Family tax-center JS; 19a sample |
| 29 | Virtus | 4 | June 2026 estimate PDF lists 4 funds |
| 30 | Eaton Vance | 1 | CEF 19(b) sample; open-end on MSIM |

**Cleared the 50-fund bar:** BlackRock / iShares (121), Vanguard (**297**), Fidelity (350), American Funds (84), Invesco (53), T. Rowe (232), DFA (140), Janus (222), American Century (389), MFS (**175**), John Hancock (**56**), Artisan (**51**). Closest remaining large-family public books: BNY (42), JPM (38).

**Large families still under 50 MF/ETF tickers (name-heavy books or gated):** BlackRock 44 (OEF book has no ticker column), American Funds 22, Invesco 11, plus every under-50-fund family above. Official books are fund-level — tickers were not invented.

**Ranks 31–40 still under 50 (public book lists fewer than 50, or gated):** Principal 2 (GetFile cover only; 2023–2025 product-page paid YE), Thrivent 13 (full paying HTML), Hartford 25 (full paying PDF), Macquarie **26** (2025 Class A paying PDF + 2023 CGE-RET-ACT full paying book), First Eagle **40** (full 2024 share-class paid + 2025 estimate; book lists ~13 strategies / 40 classes, not 50+), GMO 29 (full Trust PDF), Calamos 13, Wasatch 13.

**Handoff (ranks 1–40 only):** remaining unlocks are gated (SSGA XLSX, JPM broader YE, GS/PIMCO/UBS/Franklin/Schwab HTML, MSIM open-end PDF, Capital Group ticker column, Fidelity 2021–2023 HPDY SPA, ACI 2021/2024 PDFs). Artisan 2021–2023 ICI PDFs exist but token order / Box 1a breakdown is not column-safe. MFS fly PDFs remain current-year only (10-year Excel now covers additional official Class A pages). Do not expand ranks 41–110. Do not expand Amundi. SMAs / CEFs stay out of the 50-fund bar.

## Multi-year history and estimate → actual

History packs focus on **US-domiciled** fund firms. Prefer US managers when choosing which gaps to fill. **Skip Amundi / Pioneer** on the history ladder — do not add prior years; leave the existing 2025 fixture as-is. Ranks 21–40 in this pass are US books (John Hancock / Manulife US Investments; Macquarie Delaware Funds US book; GMO US Trust only — skip GMO Australia).

The upsert key includes `as_of` and `ex_date`, so a September preliminary, a December update, and a January final are **separate rows**. Do not collapse them.

`GET /distributions` already supports `as_of_from` / `as_of_to`, `publication_stage`, and `fund_identifier` (exact slug or ticker identity).

**Compare estimate vs paid for one fund:**

1. `GET /distributions?fund_identifier=amcap-fund&publication_stage=preliminary_estimate` — % of NAV ranges (often `total_capital_gains`).
2. `GET /distributions?fund_identifier=amcap-fund&publication_stage=final` — year-end per-share LTCG/STCG.
3. `GET /distributions?fund_identifier=amcap-fund&as_of_from=2024-01-01&as_of_to=2024-12-31` — one tax year’s publication window.
4. Units differ (`percent_of_nav` vs `per_share`); convert with NAV before subtracting. Illustration uses `as_of` or `prefer_publication_stages` so you do not add estimate + final.

Fixture packs today (ranks 1–40 historical pass):

| Family | Years in fixtures | Live archive notes |
| --- | --- | --- |
| BlackRock / iShares | 2026 midyear paid + 2025 YE ETF + 2021–2025 open-end MF | Live ETF HTML https://www.ishares.com/us/capital-gains-distributions. Open-end HTML books https://www.blackrock.com/us/individual/resources/tax-information/2025-distributions (2024 / 2023 / 2022 / 2021 siblings). Live OEF pages are per-fund share-class tables — fixtures flatten November–December YE Investor A rows (Equity Dividend LT $1.089256 / $0.740291 / $0.481929 / $0.728360 / $0.999925). iShares 2023–2024 tax kits remain 1099-style PDFs, not an ETF HTML CG grid. |
| Vanguard | 2021–2025 ICI **full December** + 2025 YE HTML for VFIAX / VBIAX / VIGAX | **ICI first.** Official Primary Layout PDFs. 2021–2025 December rows are column-safe full-book (31-token layout; wrap/DAILY bleed skipped). 2025 ICI skips VFIAX / VBIAX / VIGAX so the YE HTML fixture is not double-counted. |
| Fidelity | **2024–2025 full prior-year paid** + 2026 estimate | Live HTML: current estimates `FIIS_SP52_DPL6` and prior-year `FIIS_SP10_DPL6` (FBGRX 2025 paid LT $5.07300 ex 2025-09-12; 2026 estimate LT $21.021 as of 2026-07-31). **2024 is the full DPL6 book** from Wayback `20250321032441id_` (350 tickers; FBGRX Dec LT $1.66900 / Sep LT $11.08100; FCNTX Dec LT $0.85500). 2021–2023 prior-year HTML not in CDX (HPDY SPA). |
| State Street / SPDR | 2025 estimate (SPY/SPLG 0% NAV placeholder) | Angular live page. Historical XLSX is linked but not a stable public file URL — 2024 paid ST/LT not transcribed. ZZSSGA is a parser-layout sample, not official. |
| J.P. Morgan | 2025 Section 19a full Appendix A (open-end + ETF) | Unsplit estimated CG $/share. SEEGX / JLGMX keep Large Cap Growth LT $9.32525. No confirmed official 2024 $/share 19a. |
| Goldman Sachs | 2025 sample (GLCGX) | Advisor tax center 403-walled; no public historical HTML. |
| American Funds | 2021–2025 paid tax-year history (AMCAP / Growth Fund of America) + 2024 prelim + 2024 final reprint, 2025 prelim + 2025 final reprint, 2026 midyear paid | 2025 YE + 2026 midyear HTML are public. 2024 advisor YE URL 302s to login (transcribed fixture). **CGHM** inception 6/25/24 — no 2021–2023 rows exist. Official 2024 and 2025 YE tables list CGHM with em-dash ST/LT (no CG — not stored as $0). Only published CG today is 2026 midyear LT $0.0030 / ST $0.0169. Monthly income is on the JS historical-distributions tool (SPA — skipped after one honest GET). Product-page `historicalDistributions` JSON supplies paid as_of in the tax year for AMCAP / Growth Fund of America (AMCAP Dec 2021 LT $1.1710; no Dec 2022 row — June 2022 LT $2.2668; Dec 2023 LT $1.0270; Dec 2024 LT $2.5220; Dec 2025 LT $2.1509). Name-keyed so AMCPX/AGTHX aliases still resolve. |
| PIMCO | Layout sample only (ZZPIMI / ZZPIMB) | No public HTML estimate grid. No additional years invented. |
| Invesco | 2024 estimate + 2025 estimate | ICI Primary files are *listed* on the open-end tax guide (2023–2025) but no stable public download URL was fetchable (JS / 406) — PDF/HTML archives used instead. 2025 PDF + 2024 In Focus (American Franchise LT $0.93). |
| T. Rowe Price | 2021–2025 YE + 2022 prelim | 2023–2025 HTML (same path, year in the filename). 2021–2022 YE PDFs are the full mutual-fund/ETF books (TRBCX LT $16.03 / $6.0394 final; 2022 prelim $5.75). Em-dash / Paid monthly omitted. |
| UBS | 2025 estimate + 2025 paid (PWTAX) | No public filled ICI. Estimate PDF is rotating AEM/JCR and often 403. 2023–2024 paid archives not fetchable — skipped. |
| Franklin Templeton | 2024 + 2025 CEF 19(a) (FT) | ICI hub is a JS SPA (no filled Primary download). Open-end estimate tool is SPA. ≥$1B open-end (FKINX) not on a scrapeable grid — skipped. |
| BNY Mellon | 2022–2025 paid YE (DGAGX) + 2025 full estimate book | No public filled ICI. 2024 family estimate PDF URL was empty. 2025 estimate is every paying fund (tickers only DGAGX / PEOPX). Paid YE from the public Appreciation product page (2025 LT $6.4552 coexists with 10/31 estimate LT $6.29). |
| Nuveen | 2025 estimate sample (TIIRX) | No public filled ICI. Document-viewer URL is a JS shell (no fetchable PDF here). 2024 posted files are tax-character letters (not ST/LT $/share) — skipped. |
| Northern Trust | **2021–2025** YE (2021 full equity CG + 2022–2024 flagship + 2025 full equity CG + ICI Dec income-only) | **ICI listed.** Filled Primary Reports 2022–2025 are public PDFs. First amount is Total Distribution — CG-paying tickers not ingested as income. December ICI totals stored as ordinary income only when the CG book is em-dash. **2021** `capital-gains-2021.pdf` is the full equity CG book (NOSIX ST $0.096491 / LT $0.985777). |
| Morgan Stanley | 2024 + 2025 ETF YE (CVLC income; 0% CG) | No public filled ICI. Live ETF PDFs often Akamai 403; fixtures transcribe official document text. 2025 open-end PDF blocked. |
| Schwab | 2022–2025 annual (SWTSX / SWPPX income; 2025 also SWLVX) | No public filled ICI. Family annual page is a JS SPA — skip. Product-page HTML history used (2022–2024 CG $0, income stored). |
| Dimensional | 2024 paid + 2025 estimate (DISVX / DFELX / DFQTX) | No public filled ICI. 2024 December book `2024-distributions.pdf` (DISVX LT $0.184). |
| Columbia Threadneedle | 2024 YE paid + 2025 midyear sample | No public filled ICI. 2025 mid-year all-funds PDF is wrap-unsafe (not a column-safe full extract). 2024 YE PDF (LBSAX LT $1.38581; ELGAX LT $4.05105). IEVAX 2024 $0 CG not stored. 2023 YE PDF 404. |
| Amundi / Pioneer | 2025 estimate (PIODX) only | **Off the history ladder** (non-US parent). Existing 2025 fixture left as-is; do not expand. 2024 Pioneer siblings 404 after the Victory transfer. |
| Allspring | 2022–2025 paid YE (WFMIX / SGRNX) | No public filled ICI. Family estimate PDFs are gated login HTML. Product-page paid history used (WFMIX 2025 LT $4.26857; 2024 $2.93497; 2023 $1.7935; 2022 $3.13277). |
| Janus Henderson | **2021–2025 ICI Primary paid YE** + 2021–2022 FINAL paid companions + 2023–2025 estimates | **ICI first** for 2021–2025 (JDCAX LT $4.95363 / $0.02107 / $3.88875 / $5.46939 / $6.96694). Estimate PDFs coexist (JDCAX $3.87 / $5.42 / $6.92). 2021 FINAL paid PDF remains (Forty Fund not on that list — JDBAX 2021 LT $1.50790). Daily ICI income lines skipped. |
| American Century | **2022 + 2023 + 2025** full retail estimates + 2025 paid (TWCGX) | No public filled ICI. 2025 retail estimate PDF is every share class (TWCGX LT $10.4978) plus product-page paid Total $9.7631 (no ST/LT split). 2023 book from Wayback `estimated-distributions-september-aci-retail.pdf` (TWCGX ST $0.0349 / LT $2.4201 / 5.58% of NAV). **2022 official book** `2022-Estimated-Distributions_ACI-MFs-and-ETFs_final` (TWCGX income $0.0037 / LT $0.7247 / 2.00% of NAV; daily bond income skipped). 2024 unversioned retail PDF serves 2025. 2021 sibling 404. |
| Dodge & Cox | 2021–2025 Dec YE paid + Q1 2026 estimate | No public filled ICI. Supplemental tax letters (DODGX Dec 2025 LT $1.1999 / 2024 LT $12.036). 2023–2021 letter PDF siblings 404; Dec YE transcribed from the public product-page API `https://api-v1.dodgeandcox.com/api/funds-distribution` (DODIX Dec income $0.0570 / $0.1010 / $0.1290 / $0.1300 / $0.1347). Quarters omitted so one as_of is not summed. |
| MFS | **2021–2025 YE paid** (13 / 12 / 11 / 12 Class A tickers) + 2025 full %NAV estimate + 2026 midyear paid | No public filled ICI. 2025 fly PDF is every published share-class / all-classes row (MIGHX LT 8%–9%; published 0% stored). Official Class A tickers on product-page identifiers (MIGHX / MITTX / MFEGX / MGIAX / OTCAX / MFRFX / MTCAX). Official 10-year Excel on additional Class A pages supplies December YE 2021–2025 (MEIAX LT $1.01429 / $2.67110 / $3.13988 / $3.57266 / $3.86919; MFEGX LT $4.65025 / $1.39190 / $7.90687 / $25.50349 / $25.35332). OTCAX has no 2022–2023 YE row; MNDAX has no 2023–2025 YE row. 2024 fly PDF 404. |
| Lord Abbett | 2025 $0 no-pay list | No public filled ICI. Public PDF lists funds not expected to pay 2025 CG. 2024 sibling 404. No paying-fund ST/LT grid. |
| AllianceBernstein | 2023 flagship + 2025 full paying-fund estimate | No public filled ICI. 2025 Final_GEN-5796-1025.pdf is every listed payer (AGRFX LT $16.36; Class A tickers only AGRFX / APGAX / ABASX). Unversioned FINAL_GEN-5796.pdf now serves 2025; 2024 overwritten. 2023 book from the public Wayback snapshot of that path (AGRFX LT $6.95). |
| Federated Hermes | 2025 PAYR 19(a) | ICI Primary/Secondary listed on token URLs (not a stable public download; some books are monthly muni lines). Family tax-center grids are JS. Kaufmann pages have no scrapeable ST/LT history. |
| Virtus | 2024 19(a) + 2025 paid + 2026 June full listed estimate | No public filled ICI. 2026 June PDF lists 4 funds (STVTX LT $0.1767); 2025 calyr paid Dec (STVTX LT $0.427834); 2024 19(a) income + combined CG $1.907616. |
| Eaton Vance | 2025 CEF 19(b) (EOI) | No public filled ICI. March 2025 19(b) (EOI $0.1338 LT). 2024 sibling PDFs 403. Open-end YE stays on `morgan_stanley`. |
| John Hancock | 2022–2025 estimate ranges (TAGRX / JBGAX; USGLX 2024–2025) | No public filled ICI. Press-release PDFs still posted. USGLX 2022–2023 em-dash (no CG — omitted). Manulife parent; US JH Investments book. |
| Principal | **2023–2025 paid YE** (PQIAX / PEMGX) | No public filled ICI. GetFile estimate is a viewer shell. Product-page December YE (PQIAX 2024 LT $3.6805 / 2023 LT $0.2649; PEMGX 2024 LT $1.3963 / 2023 LT $0.9475). Quarterly income omitted. |
| Hartford | 2024 final + 2025 estimate + 2025 final (HFMCX) | No public filled ICI. Final equity PDFs (HFMCX LT $1.67 / $5.44). 10/31/2025 estimate LT $5.36 coexists (estimate→actual). |
| Macquarie / Delaware | **2023** full paid + 2024 paid + 2025 estimate (WSTAX) | No public filled ICI. US Delaware/Macquarie Funds book only. **2023** CGE-RET-ACT-2023 is the full paying-fund table (WSTAX LT $5.331; 20 Class A tickers). 2024 paid still flagship (WSTAX ST $1.108 / LT $8.135). 2025 estimate LT $10.051. Non-US Macquarie trusts skipped. |
| First Eagle | 2023–2025 paid YE + 2025 full open-end estimate + 2024 full share-class paid | No public filled ICI. 2025 estimate PDF is every listed open-end fund (SGENX LT $4.12–$4.17; FEVAX LT $1.77–$1.82) with Class A tickers from the official 2024 paid PDF. 2024 paid PDF is every open-end share class (40 tickers; Credit Opportunities omitted). Product-page 2025/2023 flagships remain. |
| GMO | 2026 July estimate (GQETX) only | No public filled ICI. US Trust July/Dec 2025 sibling filenames 404. **Skip GMO Australia** unit-trust estimates. |
| Artisan | **2024–2025 ICI YE** (full share-class) + 2026 YTD paid (ARTKX) | **ICI-style Year-End Tax Reporting PDFs.** 2025 is 30-token (ARTIX LT $5.017255; ARTKX Nov LT $2.725068). 2024 is column-safe with LT at token 11 (ARTIX ST $0.456695 / LT $2.067175). 2021–2023 siblings are public but transposed ICI (funds as columns) — not column-safe. YTD HTML keeps ARTKX 2026 income $0.338342. |
| Calamos | 2024 + 2025 estimates (CVGRX) | No public filled ICI. 2024 estimate PDF (CVGRX ST $1.24 / LT $1.84). 2023 sibling 404. |
| Wasatch | 2022 + 2024–2025 paid YE + 2025 estimate (WGROX) | No public filled ICI. 2024 estimate sibling 404. Product-page paid (WGROX 2025 LT $6.345749 / 2024 $8.282696 / 2022 $0.457965). **2023 gap** — no YE row on the product page. |
| Harbor | 2025 estimate (HACAX) only | No public filled ICI. 2024 sibling PDF 404. Third-party combined dividend totals unused. |
| Nationwide | 2025 paid (NWHOX) only | US-domiciled. No public filled ICI. 2024 MFN-0434AO is not a CG book. Hub PDF is unversioned. |

**ICI Primary Layout inventory (top AUM, verified 2026-09-07):**

| Rank | Family | Public filled ICI file? | Notes |
| --- | --- | --- | --- |
| 1 | BlackRock / iShares | no | Open-end 2021–2025 tax-information HTML (flattened Nov–Dec YE). iShares tax kits are 1099-style PDFs, not ICI Primary Layout. |
| 2 | Vanguard | **yes** | Advisor tax center PDFs 2021–2025 (and earlier). Preferred source. |
| 3 | Fidelity | no | Institutional HTML estimates + prior-year paid table. |
| 4 | State Street / SPDR | no | Angular estimate page; historical XLSX has no stable URL. |
| 5 | J.P. Morgan | no | Section 19a PDFs. |
| 6 | Goldman Sachs | no | Advisor tax center 403-walled. |
| 7 | American Funds | no | Public HTML YE + historical-distributions tool. |
| 8 | PIMCO | no | Notices / PDF hub; no ICI download. |
| 9 | Invesco | listed, not fetchable | Open-end tax guide names ICI Primary files; no stable public URL (JS / 406). |
| 10 | T. Rowe Price | no | Public YE HTML (2023–2025) + 2021–2022 YE PDFs. |
| 11 | UBS | no | Estimate PDF is rotating AEM/JCR; price-page HTML for 2025 paid. |
| 12 | Franklin Templeton | listed, not fetchable | Tax-center ICI reports page is a JS SPA; no stable filled-file URL. |
| 13 | BNY Mellon | no | Estimate PDFs + product-page paid history. |
| 14 | Nuveen | no | Document-viewer estimate PDFs; 2024 letters are tax character only. |
| 15 | Northern Trust | **yes (income-only subset)** | Public `nf-ici-primary-*.pdf` 2022–2025. First amount is total (income+CG). December ICI stored as income only when the CG book is em-dash; CG-paying tickers stay on the companion CG PDF. 2021 equity CG PDF is public. |
| 16 | Morgan Stanley | no | ETF/open-end tax PDFs under `/im/publication/forms/tax/`. |
| 17 | Schwab | no | SPA family grids; product-page HTML history. |
| 18 | Dimensional | no | Public chmedia distribution PDFs. |
| 19 | Columbia Threadneedle | no | Public midyear estimate + YE cap-gains PDFs. |
| 20 | Amundi / Pioneer | no | Pioneer/Victory tax-center PDFs. **Off the history ladder** — 2025 fixture only. |
| 21 | Allspring | no | Product-alert estimate PDFs gated; product-page paid HTML used. |
| 22 | Janus Henderson | **yes (2021–2025)** | Official ICI Primary Layout PDFs on the advisor tax hub. 2021 file is `Janus Henderson ICI Primary Layout 2021.pdf` (JDCAX on ICI; absent from the 2021 FINAL PDF). 2024 ICI Primary is `Janus-Henderson-2024-ICI-Primary-Layout.pdf` (hyphenated). |
| 23 | American Century | no | JS hub + 2025 retail PDF; 2023 Wayback + official 2022 `2022-Estimated-Distributions_ACI-MFs-and-ETFs_final`. 2024 unversioned path is the 2025 file. 2021 404. |
| 24 | Dodge & Cox | no | Supplemental tax letters + Q1 estimate PDFs. |
| 25 | MFS | no | 2025 full %NAV fly PDF (175 rows) + official 10-year Excel YE 2021–2025 on additional Class A pages + product-page 2025/2026 paid. |
| 26 | Lord Abbett | no | JS hub; public file is a 2025 no-pay list. |
| 27 | AllianceBernstein | no | Versioned 2025 estimate PDF; unversioned path overwritten (2023 via Wayback). |
| 28 | Federated Hermes | listed, not fetchable | Token-walled ICI Primary/Secondary on services.federatedhermes.com; some books are monthly lines. |
| 29 | Virtus | no | Public estimate + calendar-year + 19(a) PDFs. |
| 30 | Eaton Vance | no | CEF 19(b) press-release PDFs; 2024 siblings 403. |
| 31 | John Hancock / Manulife | no | Press-release estimate PDFs 2022–2025 (US JH book). |
| 32 | Principal | no | GetFile viewer estimate; product-page paid HTML YE 2023–2025 (PQIAX / PEMGX). |
| 33 | Thrivent | no | Public paid HTML. Not in this history wave. |
| 34 | Hartford | no | Public estimate + final equity PDFs 2024–2025. |
| 35 | Macquarie / Delaware | no | US fulfillment CGE-RET estimate + CGE-RET-ACT-2024 paid + CGE-RET-ACT-2023 full paying book. |
| 36 | First Eagle | no | Estimate PDF + full 2024 share-class paid PDF + product-page history. |
| 37 | GMO | no | US Trust July 2026 estimate PDF; 2025 siblings 404. Skip Australia. |
| 38 | Artisan | **yes (2024–2025)** | Year-End Tax Reporting Information 2024–2025.pdf are ICI-style and column-safe. 2021–2023 siblings are transposed ICI (not column-safe). |
| 39 | Calamos | no | Public estimate PDFs 2024–2025; 2023 sibling 404. |
| 40 | Wasatch | no | 2025 estimate PDF + product-page paid history (2023 gap). |
| 41 | Harbor | no | 2025 estimate PDF; 2024 sibling 404. |
| 42 | Nationwide | no | 2025 MFN-0435AO; 2024 sibling is not a CG book. |

Blank ICI templates on https://www.ici.org/year-end-tax-reporting are instructions, not a manager feed.

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

Sparse family coverage makes Aftertax-style portfolio analytics wrong: a book that is 40% Vanguard / iShares / Fidelity looks like it has no taxable distributions if those adapters are stubs. The registry is the **top 110 US-advisor-relevant firms** (AUM ranks 1–110). Multi-year history packs prefer **US-domiciled** managers; **Amundi / Pioneer is skipped on the history ladder** (parser stays implemented; 2025 fixture unchanged). `GET /coverage` returns `implemented_pct` (today 110/110 fixture parsers) so the website can later compute *% of portfolio dollars covered*.

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
| 2 | `vanguard` | Vanguard | implemented | JS SPA + ICI PDF fixtures | **ICI first:** Primary Layout PDFs 2021–2025 under `/content/dam/fas/pdfs/`. 2021–2025 December rows are full-book (wrap/DAILY bleed skipped). YE SPA is fallback for 2025 VFIAX / VBIAX / VIGAX only. |
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
| 13 | `bny_mellon` (aliases `bny`, `dreyfus`) | BNY Mellon / Dreyfus | implemented | PDF + product HTML | 2025 estimate PDF + DGAGX paid YE 2022–2025 on the Appreciation product page |
| 14 | `nuveen` (alias `tiaa`) | Nuveen / TIAA | implemented | PDF viewer | https://documents.nuveen.com/Documents/Nuveen/Default.aspx?uniqueId=3c3be13d-d800-48e2-a537-c251162ab9f4 |
| 15 | `northern_trust` (aliases `nt`, `ntam`) | Northern Trust | implemented | PDF + ICI-derived HTML | 2021 full equity CG + 2022–2024 flagship + 2025 equity CG + ICI Dec income-only; FI daily omitted |
| 16 | `morgan_stanley` (aliases `msim`, `ms`) | Morgan Stanley IM | implemented | PDF (often Akamai-walled) | 2024 + 2025 ETF YE under `/im/publication/forms/tax/` |
| 17 | `schwab` (alias `charles_schwab`) | Charles Schwab IM | implemented | JS family page; product HTML | Product pages `swtsx` / `swppx` (2022–2025); 2025 family SPA fallback |
| 18 | `dimensional` (alias `dfa`) | Dimensional | implemented | PDF | 2025 estimates + 2024 `2024-distributions.pdf` |
| 19 | `columbia_threadneedle` (aliases `columbia`, `ameriprise`) | Columbia Threadneedle | implemented | PDF | 2025 midyear estimates + 2024 YE `2024-cap-gains---mutual-funds.pdf` |
| 20 | `amundi` (alias `pioneer`) | Amundi US / Pioneer | implemented | PDF | 2025 estimate PDF only. **Off the history ladder** (US-domiciled preference). Existing fixture unchanged. |
| 21 | `allspring` (aliases `wells_fargo`, `wfam`) | Allspring | implemented | product-page HTML / gated PDF | Paid YE 2022–2025 on `.../special-mid-cap-value/` and `.../growth/i/` (WFMIX / SGRNX). Family estimate PDFs gated. |
| 22 | `janus_henderson` (alias `janus`) | Janus Henderson | implemented | ICI PDF + estimate/final PDF | 2021–2025 ICI Primary paid YE (JDCAX LT $4.95363 / $0.02107 / $3.88875 / $5.46939 / $6.96694) plus estimate PDFs and 2021–2022 FINAL paid companions. |
| 23 | `american_century` | American Century | implemented | JS hub + PDF + product HTML | 2025 retail estimate PDF + 2023 Wayback + official 2022 retail estimate (TWCGX LT $0.7247 / $2.4201 / $10.4978) + TWCGX product-page paid Total $9.7631. |
| 24 | `dodge_cox` (aliases `dodge`, `dodgx`) | Dodge & Cox | implemented | PDF | Q1 2026 estimate + 2024/2025 supplemental tax letters (DODGX Dec YE). 2023 letter 404. |
| 25 | `mfs` | MFS Investment Management | implemented | PDF + product HTML + 10-year Excel | 2025 full %NAV fly PDF (175 rows; official Class A tickers) + 10-year Excel YE 2021–2025 on additional Class A pages + paid YE 2025 / midyear 2026. 2024 fly 404. |
| 26 | `lord_abbett` (alias `lord`) | Lord Abbett | implemented | PDF (no-pay list) | 2025 Funds-with-Losses.pdf. 2024 sibling 404. No paying-fund ST/LT grid. |
| 27 | `ab` (aliases `alliancebernstein`, `alliance_bernstein`) | AllianceBernstein | implemented | PDF | 2025 Final_GEN-5796-1025.pdf; 2023 via Wayback of FINAL_GEN-5796.pdf. 2024 overwritten. |
| 28 | `federated_hermes` (alias `federated`) | Federated Hermes | implemented | JS tax center + 19(a) PDF | PAYR 19(a) 2025. ICI token-walled. Kaufmann pages have no ST/LT grid. |
| 29 | `virtus` | Virtus | implemented | PDF | 2026 June estimate + 2025 calyr paid + 2024 19(a) (STVTX). |
| 30 | `eaton_vance` (alias `ev`) | Eaton Vance | implemented | CEF 19(b) PDF | March 2025 combined 19(b) (EOI). 2024 siblings 403. |
| 31 | `john_hancock` (aliases `manulife`, `jh`) | John Hancock / Manulife | implemented | PDF | Press-release estimate PDFs 2022–2025 (TAGRX). US JH Investments book. |
| 32 | `principal` | Principal | implemented | product-page HTML / viewer PDF | PQIAX / PEMGX product-page paid YE 2023–2025. Tax hub GetFile estimate PDF is a viewer shell. |
| 33 | `thrivent` | Thrivent | implemented | yes | https://www.thriventfunds.com/support/tax-resource-center/capital-gains.html |
| 34 | `hartford` | Hartford Funds | implemented | PDF | 2025 estimate memo + 2024/2025 final equity PDFs under `.../capgainsdistributions/` (HFMCX) |
| 35 | `macquarie` (aliases `delaware`, `delaware_funds`) | Macquarie / Delaware Funds | implemented | PDF | US CGE-RET 2025 estimate + CGE-RET-ACT-2024 paid + CGE-RET-ACT-2023 full paying book (WSTAX). Non-US Macquarie trusts skipped. |
| 36 | `first_eagle` (alias `fei`) | First Eagle | implemented | PDF + product HTML | 2025 full open-end estimate + 2024 full share-class paid PDF (40 tickers) + product-page YE (SGENX) |
| 37 | `gmo` | GMO | implemented | PDF | US Trust July 2026 estimate. 2025 siblings 404. Skip GMO Australia. |
| 38 | `artisan` (alias `artisan_partners`) | Artisan Partners | implemented | ICI PDF + YTD HTML | 2024–2025 Year-End Tax Reporting ICI. YTD HTML for 2026 ARTKX income. 2021–2023 ICI public but transposed / not column-safe. |
| 39 | `calamos` | Calamos | implemented | PDF | 2024 + 2025 estimate PDFs (CVGRX). 2023 sibling 404. |
| 40 | `wasatch` | Wasatch | implemented | PDF + product HTML | 2025 estimate PDF + WGROX product-page paid 2022/2024/2025 (2023 gap). |
| 41 | `harbor` | Harbor | implemented | PDF | 2025 estimate PDF (HACAX). 2024 sibling 404. |
| 42 | `nationwide` | Nationwide | implemented | PDF | 2025 MFN-0435AO (NWHOX). US-domiciled. 2024 sibling is not a CG book. |
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

**Victory vs Pioneer / Amundi:** Pioneer open-end estimates stay on `amundi` (aliases `pioneer`, `victory_pioneer`). `victory` is Victory Portfolios I/II (Integrity / Sycamore / Multi-Cap). USAA (Portfolios III) and RS books have separate public vcm.com PDFs not yet ingested. Amundi / Pioneer is **off the history ladder**; prefer US-domiciled Victory books if those gaps are filled later.

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

**Live honesty:** Vanguard and State Street pages are still client-rendered as of 2026-09-07 (static GET parses 0 rows → fixture fallback). JPM, Goldman, PIMCO, and Invesco still publish estimates as PDFs or login-walled docs — no new scrapeable HTML grids were found on re-check. Ranks 11–20 are the same pattern: BNY, Nuveen, Northern Trust, Dimensional, Columbia, and Pioneer/Amundi are public PDFs; Franklin’s family estimate tool is a JS SPA (fixture uses a public CEF 19(a)); UBS and Schwab have some public HTML but fund-name/class layout or SPA shells keep live parse unreliable. Ranks 21–30 continue that pattern: Janus, American Century, Dodge & Cox, MFS, AB, and Virtus are public PDFs; Lord Abbett’s only public 2025 estimate document is a no-pay list; Federated’s family tax-center grids are JS (fixture uses a public 19(a)); Allspring’s family estimate PDF is gated/image-based (fixture uses public product-page paid rows); Eaton Vance open-end HTML was not found (fixture uses a public CEF 19(b)). Ranks 31–40: John Hancock, Hartford, Macquarie/Delaware (US book), GMO US Trust, and Calamos are public PDFs (JH 2022–2025 estimates; Hartford 2024/2025 finals; Macquarie 2024 paid + 2025 estimate; Calamos 2024–2025 estimates; GMO 2025 siblings 404 — skip Australia); First Eagle and Wasatch add public product-page paid YE (SGENX 2023–2025; WGROX 2022/2024/2025, 2023 gap); Thrivent’s paid capital-gains table is public HTML (live parse works after recognizing the “Thrivent Mutual Fund” header; no ticker column); Principal’s family estimate PDF is a GetFile viewer (fixture uses public product-page paid rows; not in this history wave); Artisan’s tax-center HTML is paid YTD income (year-selector SPA — skip; NRA is tax-character, not ingested). Ranks 41–50: Harbor, Nationwide, Voya, Tweedy, Gabelli, NYLI/MainStay, Touchstone, and Victory Integrity/Sycamore are public PDFs (Nationwide GET is sometimes Akamai-denied); Oakmark and Royce publish public paid HTML (class-section / header layout still returns 0 live rows → fixture fallback). Ranks 51–60: SEI, Brown Advisory, William Blair, VanEck, WisdomTree, AQR, Causeway, Alger, and Harding Loevner are public PDFs (Harding Loevner fixture uses the AMG year-end reprint that includes tickers); Matthews Asia publishes paid amounts on the mutual-fund product HTML (nested accordion tables still return 0 live rows → fixture fallback). Ranks 61–70: TCW, Bridgeway, Diamond Hill, Champlain, Driehaus, Hotchkis & Wiley, and Osterweis are public PDFs (TCW and Diamond Hill PDFs are fund-level — fixtures attach public Class I / Investor tickers); Jensen, Marsico, and Davis publish public HTML (prose lists / multi-class tables still return 0 live rows → fixture fallback). Ranks 71–80: PRIMECAP, Ariel, Baird, Buffalo, GQG, and FMI are public PDFs (PRIMECAP and Buffalo PDFs are fund/class-level — fixtures attach public Investor tickers); Longleaf, Third Avenue, and Heartland publish public HTML (product-page / tax-center layout still returns 0 live rows → fixture fallback); Impax’s distributions hub is geo/investor-type gated (fixture transcribes the public December 2025 table crawled from that URL). Ranks 81–90: American Beacon, Baillie Gifford, Brandes, Boston Trust Walden, Meridian, and Kinetics are public PDFs (Baillie Gifford and Brandes PDFs are fund-level — fixtures attach public Institutional / Class I / Class K tickers); Mairs & Power, Grandeur Peak, Hennessy, and FAM publish public HTML (fund-name-only / multi-year / expandable tables still return 0 live rows or omit tickers → fixture fallback). Ranks 91–100: Lazard, Manning & Napier, Westwood, Boston Partners, Homestead, LSV, LKCM, Oberweis, and RiverPark are public PDFs (Lazard, Manning & Napier, Westwood, Boston Partners, Homestead, and LSV PDFs are fund- or CUSIP-level — fixtures attach public Institutional / Class I / Class S / no-load tickers); Madison publishes paid HTML (fund-name / ST / LT only, no ticker column → fixture fallback). Ranks 101–110: AMG, Permanent Portfolio, Kopernik, LoCorr, Timothy Plan, Hodges, and Tocqueville are public PDFs (GuideStone, Conestoga, Timothy Plan, and Hodges pages/PDFs are fund-level — fixtures attach public Investor / Institutional / Class I / Class A / Retail tickers); GuideStone, Value Line, and Conestoga publish public HTML (fund-name-only or mashed headers may still return 0 live rows → fixture fallback). Do not treat fixture rows as a complete live book. `POST /ingest/distributions` is always valid for an advisor-uploaded notice.

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

Coverage includes HTML normalization (American Funds plus top-110 family fixtures), multi-year history filters, upsert idempotency, search filters, tax illustration math, portfolio coverage, Current vs Proposed allocation compare, compare-chart deltas, Growth of $X performance series, and coverage-gap logging.

## Layout

```
app/
  main.py              FastAPI app
  api.py               HTTP routes
  models.py / schemas.py / crud.py
  sources/             FundSource adapters + HTML parser
  services/ingest.py   Fetch + upsert orchestration
  services/illustrate.py  Tax-impact illustration
  services/performance.py Growth of $X (Yahoo adj-close; not weekly refresh)
  services/coverage.py Coverage snapshot + gap logging
  cli.py               seed / fetch / families
fixtures/<family>/     HTML fixtures (American Funds + top 110)
fixtures/performance/  Monthly adj-close fixtures (AGTHX, SPY, AGG, VXUS, …)
tests/
```
