# Fund Distribution Estimates API

Backend service that ingests **taxable distribution estimates** published by fund managers and stores them in a searchable database for an Asset Management / Financial Advisor website.

The default demo uses **SQLite** and bundled Capital Group HTML fixtures so the pipeline runs offline. The same SQLAlchemy models work with **Postgres** by changing `DATABASE_URL`.

**Build, not buy.** This service ingests public manager ICI layout files, PDF archives, and HTML. It does not license CapGainsValet, YCharts, or other paid distribution feeds.

**Source preference (historical + ongoing):**

1. **ICI Primary Layout** when the family publishes a filled file (not the blank template on ici.org).
2. **PDF / HTML archives** when no public ICI download exists.
3. Skip JavaScript SPA pages when an ICI or PDF book is available.

Vanguard is the first-choice ICI book: official Primary Layout PDFs on the advisor tax center cover the full fund list. 2021–2025 December rows are a column-safe full-book extract (31-token layout; wrap/DAILY bleed skipped). Other top-AUM families are checked for ICI downloads in rank order; Invesco *lists* ICI Primary files on its open-end tax guide. The public broker XLSX URLs on that page are now the 2023–2025 December YE book (Daily / $0 / QDI % omitted). 2021–2022 sibling XLSX URLs 404 — unmatched, not invented. Northern Trust publishes filled ICI Primary Reports (2022–2025) on its tax center; PDF text extraction merges income/CG and includes quarterly lines, so December YE ST/LT are transcribed from the companion capital-gains PDFs (same hub).

**Full-book vs flagship history.** Current-year / published-table fixtures now ingest **every fund listed on that family’s public book** (skip synthetic `ZZ*` parser samples). Amundi / Pioneer is included per Eric 2026-09-08 (Victory-hosted Pioneer tax center). The ≥$1B allowlist in `app/sources/aum.py` still applies to **older multi-year archives** when those packs were transcribed as flagships only. It is not a live AUM feed. Illustrate / compare / performance contracts are unchanged.

## What you get

- Normalized data model for distribution estimates (family, fund, ticker, share class, type, amount + unit, tax dates, source URL, raw JSON audit payload)
- `POST /ingest/distributions` for partner/manual feeds
- `POST /ingest/fetch` to run a pluggable `FundSource` adapter (`fixture` or `live`)
- `python -m app.cli refresh` for weekly all-family ingest (`REFRESH_MODE=auto`: live then fixture), including weekly NAV for every listed ticker
- `python -m app.cli refresh-nav` to refresh NAV / last liquid close only (Yahoo, fixture fallback)
- Idempotent upserts on `(fund_family, fund identifier, share class, estimate type, as_of, ex-date)`
- Search API with filters, text search, and pagination
- `GET /funds` — paginated **unique funds** from the stored book (`limit`/`offset`/`total`/`category` / `coverage_status`, plus weekly `nav_per_share` / `nav_as_of` / `nav_source`) for Website Search / Sample Estimates / Versus Category. Does not invent funds, categories, NAV, or estimates.
- `GET /funds/lookup?ticker=` — exact ticker lookup. In-book → `coverage_status` `awaiting_estimate` | `estimate_announced`. Miss → **404** `not_in_universe` (UI: Add to universe). Never conflate a miss with Awaiting Estimate.
- `GET /funds/categories` — distinct Morningstar-style categories with stored-fund counts (plus `uncategorized` / `coverage_pct`)
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

The API listens on port 8000. SQLite is stored in the `dist-data` volume (soft-beta path).

Local Postgres (optional; does not change production Render):

```bash
docker compose --profile postgres up --build
# API on :8001 uses postgresql+psycopg://distributions:distributions@postgres:5432/distributions
# From the host:
export DATABASE_URL=postgresql+psycopg://distributions:distributions@localhost:5432/distributions
alembic upgrade head
```

See `docs/CUTOVER.md` before any production flip.

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
3. Blueprint attaches a 1 GB disk at `/var/data` (`plan: starter`, 512 MB RAM)
   and sets `DATABASE_URL=sqlite:////var/data/distributions.db` so the SQLite
   book survives deploys. Free web services cannot attach a disk. Persistent
   disk also **disables zero-downtime deploys** — the old process is gone
   before the new one listens, so a blocking boot looks like 502s.
4. Recommended env (Blueprint already sets these):
   - `SEED_ON_START=true` — background seed; `/health` stays 200 (`health.seed`
     is `running` then `complete`). Warm disk densifies deltas only (missing
     families or changed fixture files). Does **not** wipe/rebuild the book
     on every Manual Deploy.
   - `SEED_FORCE_FULL=false` — set `true` only when you intentionally want
     every family re-parsed from fixtures (CPU/RAM spike; can OOM starter).
   - Memory: **starter (512 MB) is enough for delta boot**. A cold empty-disk
     seed or `SEED_FORCE_FULL=true` parses ~12 MB / 400 fixture files in-process
     and can exit 137 / 502. If that crash persists after the disk is warm,
     upgrade to **Standard (2 GB)** — that is infra, not a missing code path.
5. Copy `https://aftertax-data-api.onrender.com` (or the URL Render prints).
6. Verify `GET /health` 200 and `GET /funds?q=AGTHX` 200 (even while
   `health.seed` is `running` if the ticker is already on disk).

**Website env** (project that serves `testing-seven-umber-19.vercel.app`):

```
NEXT_PUBLIC_DATA_API_URL=https://<api-host>
```

No trailing slash. Redeploy Website after setting it. Local Next: `NEXT_PUBLIC_DATA_API_URL=http://127.0.0.1:8000`.

CORS already allows `https://testing-seven-umber-19.vercel.app`, `http://localhost:3000`, `http://127.0.0.1:3000`, and other `https://*.vercel.app` previews (`CORS_ORIGINS` / `CORS_ORIGIN_REGEX`). Tax / illustrate / performance contracts are unchanged.

### Weekly refresh on the public API

Fixture seed on boot (`SEED_ON_START=true`, also implied on Vercel) is **not** a wipe. Empty disk (or `SEED_FORCE_FULL=true`) runs the same fixture ingest as `POST /ingest/fetch {"fund_family":"all","mode":"fixture"}` — every registered family, including Dodge & Cox (`DODIX` / `DODGX`), Vanguard, Fidelity, MFS, First Eagle. When `/var/data/distributions.db` already has rows, boot records fixture fingerprints and **only ingests families with 0 rows or changed fixture files** (densify deltas). It does not invent amounts.

The seed starts in a **background thread** after `init_db()` so `GET /health` is liveness: HTTP 200 as soon as uvicorn is listening (`health.seed` is `running` then `complete`; `health.status` stays `ok` even if SQLite is briefly busy). SQLite uses WAL + NullPool (one connection per request; **one uvicorn worker**) so concurrent `/funds` searches do not hydrate the whole book or fight a QueuePool on `/var/data`. `GET /funds` scopes the live-estimate flag to the current page. Families commit one at a time; a mid-book failure does not roll back earlier families. A cold full book is ~11k rows. Manual ingest is not required after a cold start. Never set `SEED_FORCE_FULL` on a routine Manual Deploy.

```bash
python -m app.cli refresh --mode fixture   # same offline all-family ingest (foreground)
# or
python -m app.cli refresh                  # REFRESH_MODE=auto: live then fixture
```

GitHub Action `.github/workflows/weekly-ingest.yml` (Monday 14:00 UTC + `workflow_dispatch`). For a durable book across restarts, set repo secret `DATABASE_URL` to the **same Postgres** the API uses (`postgresql+psycopg://…`) and install `psycopg[binary]`. Vercel `/tmp` SQLite is ephemeral. Render Blueprint uses `sqlite:////var/data/distributions.db` on a persistent disk (`plan: starter`) so the book survives deploys; `SEED_ON_START=true` densifies fixture deltas on boot and does not rebuild a warm disk.

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

# Search — unique funds (Website Sample Estimates / Search table)
curl -s 'http://127.0.0.1:8000/funds?limit=50&offset=0' | jq
curl -s 'http://127.0.0.1:8000/funds?q=AMCAP&limit=50&offset=0' | jq
curl -s 'http://127.0.0.1:8000/funds/lookup?ticker=AGTHX' | jq '{ticker,has_estimate,coverage_status}'
curl -s 'http://127.0.0.1:8000/funds/lookup?ticker=ZZZZZ' | jq
curl -s 'http://127.0.0.1:8000/funds?fund_family=Vanguard&limit=50&offset=0' | jq
curl -s 'http://127.0.0.1:8000/funds?category=Large+Growth&limit=50&offset=0' | jq
curl -s 'http://127.0.0.1:8000/funds/categories' | jq '{coverage_pct,uncategorized,total_funds,items:[.items[:5]]}'

# Search — distribution rows (limit/offset aliases map to page_size/page)
curl -s 'http://127.0.0.1:8000/distributions?q=AMCAP&estimate_type=long_term_capital_gains' | jq
curl -s 'http://127.0.0.1:8000/distributions?ticker=CGHM' | jq
curl -s 'http://127.0.0.1:8000/distributions?limit=50&offset=0' | jq
curl -s 'http://127.0.0.1:8000/distributions?ex_date_from=2026-06-01&ex_date_to=2026-06-30' | jq
# Paid History — year window + category (same strings as GET /funds/categories)
curl -s 'http://127.0.0.1:8000/distributions?publication_stage=final&ex_date_from=2025-01-01&ex_date_to=2025-12-31&category=Large%20Blend&limit=50' | jq '{total,page,page_size,categories:[.items[].category]|unique}'
# Paid History — highest Dist $/Share in the filtered year book (sort after filters, before limit)
curl -s 'http://127.0.0.1:8000/distributions?publication_stage=final&ex_date_from=2025-01-01&ex_date_to=2025-12-31&sort=amount&order=desc&limit=50' | jq '{total,page,page_size,amounts:[.items[].amount]}'
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

The command is the `POST /ingest/fetch` `fund_family=all` path with per-family error isolation, then a **weekly NAV walk** of every listed ticker in the stored book. Upserts stay **idempotent**: the same document (`as_of` + ex-date + estimate type) updates the existing row; a new `as_of` inserts a new snapshot. Exit code is `0` on partial live fallbacks. Exit `1` only when **every** attempted family hard-fails (live and fixture both error). NAV misses stay **null** (never invented) and do not fail the job.

### Weekly NAV (Eric 2026-09-09)

`$/share` tax math needs NAV universe-wide:

- Dist $ (live estimate) = est $/share × (holding $ / **latest weekly NAV**)
- Historical % of NAV = est $/share ÷ **NAV on the distribution day**
- Live-estimate % of NAV = est $/share ÷ latest weekly NAV

**Distribution day** is `ex_date` when present, else `payable_date`. The print is the last regular close **on or before** that day (≤7 calendar days, for weekends / holidays). Never use today’s NAV for a past distribution. Null when unknown — never invent NAV or estimate amounts.

| Field | Where | Meaning |
| --- | --- | --- |
| `nav_per_share` | `GET /funds` items; `POST /illustrate` request/response | Latest liquid close / mutual-fund NAV (USD per share) for **live** estimate math. Null when unknown. |
| `nav_as_of` | `GET /funds` items | As-of date of that weekly print. |
| `nav_source` | `GET /funds` items | `yahoo_last_close` (preferred live daily **regular close**, not `adjclose`), `issuer`, `fixture` / `fixture_fallback`. |
| `nav_on_distribution_day` | `GET /distributions` items; illustrate `components[]` | NAV on the distribution day (ex, else payable). **Not** today’s weekly NAV. Null when unknown. |
| `nav_on_distribution_day_as_of` | same | Print date actually used (may be a few days before a weekend/holiday ex). |
| `nav_on_distribution_day_source` | same | Source of that historical print. |

`POST /illustrate` (and portfolio / compare) uses the stored weekly NAV when the request omits `nav_per_share` and `shares` so live Dist $ can run. A request-supplied NAV still wins for Dist $ / shares. Historical `percent_of_nav` on a component uses `nav_on_distribution_day` when the row is past-dated or `final`/`paid`; it stays **null** if that day’s print is missing (does **not** fall back to today). Live prelim/updated rows without a past distribution day still use latest weekly NAV for `% of NAV`.

```bash
python -m app.cli refresh-nav --mode fixture   # offline catalog + performance last close
python -m app.cli refresh-nav                  # Yahoo last close, fixture fallback
```

Sunday and Monday weekly jobs both run `refresh` (families + NAV) and an explicit `refresh-nav` step so the Sunday scrape always includes NAV.

**Coverage (measured 2026-09-09 on the full fixture book, 4,889 unique funds / 4,606 listed tickers):**

| Stage | Unique funds with NAV | Coverage |
| --- | ---: | ---: |
| Before this change | 0 / 4,889 | **0%** |
| Fixture catalog only (performance heroes) | 72 / 4,889 | **1.5%** |
| After live Yahoo last-close backfill | 4,544 / 4,889 | **92.9%** |

Listed-ticker hit rate after live backfill: **4,538 / 4,606 (98.5%)**. The remaining 68 listed tickers and name-only funds stay **null** (Yahoo had no print — never invented).

Sample prints from that walk (`nav_source=yahoo_last_close`):

| Ticker | `nav_per_share` | `nav_as_of` |
| --- | ---: | --- |
| ABALX | 40.849998 | 2026-09-08 |
| VFIAX | 709.409973 | 2026-09-08 |
| SPY | 762.400024 | 2026-09-09 |
| DBEF | 54.730000 | 2026-09-09 |

**NAV on the distribution day** (same book, Yahoo daily history, 2026-09-09):

| Stage | Distinct (ticker, ex/payable) pairs | Coverage |
| --- | ---: | ---: |
| Before | 0 / 10,100 | **0%** |
| After live Yahoo daily history | 9,550 / 10,100 | **94.6%** |

550 pairs stay **null** (Yahoo miss or no print within 7 days — never invented). Offline seed: `fixtures/nav/history.json`.

| Ticker | Distribution day | `nav_on_distribution_day` | Print as-of |
| --- | --- | ---: | --- |
| ABALX | 2025-12-15 (ex) | 37.090000 | 2025-12-15 |
| VFIAX | 2025-12-23 (ex) | 637.650024 | 2025-12-23 |
| SPY | 2025-12-19 (ex) | 680.590027 | 2025-12-19 |
| DBEF | 2025-12-19 (ex) | 47.990002 | 2025-12-19 |

The JSON / Markdown summary breaks out **midyear vs year-end** created/updated when a row is detectable from the source URL (`midyear`, `mid-year`, `interim`, `semi-annual`, `year-end`) or from `as_of` / `ex_date` month (May–August vs October–January). Unclassified months (for example September) are counted only in the overall created/updated totals.

Live pages often 403, challenge, or render as a JS/SPA shell and parse 0 rows. That is expected for a large share of the top 110 — fixture fallback is the documented recovery, not a job failure.

### GitHub Actions

`.github/workflows/weekly-ingest.yml`:

- Schedule: **Sundays and Mondays** at **14:00 UTC** (about 9am America/Chicago). Sunday scrape includes NAV.
- Manual: **Actions → Weekly ingest refresh → Run workflow** (`workflow_dispatch`), optional `refresh_mode`
- Installs `requirements-dev.txt` (includes `psycopg[binary]`). Uses SQLite unless a `DATABASE_URL` repo secret is set (then Postgres; app rewrites `postgres://` / `postgresql://` to `postgresql+psycopg://`). Cron is still Sun+Mon 14:00 UTC; Sunday 06:00 CT is a post-cutover follow-up.
- Runs `python -m app.cli refresh` (families + NAV) then `python -m app.cli refresh-nav` then ticker-request pickup
- Writes `refresh-summary.json` / `refresh-summary.md` and `nav-summary.json` / `nav-summary.md`, appends both Markdown files to the job summary, and uploads them as the `weekly-ingest-summary` artifact

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
| `per_share` | `shares = shares` or `holding_dollars / nav_per_share`; `distribution_dollars = shares * amount` (Eric: est $/share × holding $ / NAV). `percent_of_nav` on the component is est $/share ÷ NAV × 100 when NAV is known. Request `nav_per_share` / `shares` win; otherwise the stored weekly NAV is used. **HTTP 422** `{ "code": "needs_nav_or_shares", "detail": "nav_per_share or shares is required when illustrating per_share distributions" }` if neither the request nor a stored weekly NAV can price the row. Same body on `POST /illustrate/compare` when a selected side cannot be priced. |
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
  }' | jq '{coverage, gaps, totals, warnings, holdings: [.holdings[] | {ticker, fund_identifier, covered, publication_stage_used, upcoming, paid_history, gap_reason, warnings}]}'
```

On the American Funds fixtures: $1.25M covered / $150k uncovered → `coverage_pct` ≈ 89.3%. AMCAP uses the latest preliminary (3–5% NAV → $40,000 / $10,000 tax at 20%+5%). Covered holdings get `upcoming: {distribution_dollars, estimated_tax, as_of, publication_stage, record_date, ex_date, payable_date}` only when that illustration is still **before the record window** (today UTC strictly before `record_date`, else `ex_date`, else `payable_date`) and the stage is not final/paid. Past-dated prelims (AMCAP Dec 2025) and paid/final rows are `upcoming: null`. Those past events are instead listed on additive **`paid_history[]`** (same fields; `estimated_tax` null when not computable). Inclusion: `publication_stage` in `{final, paid}`, **or** prelim/updated whose gate date is past (`today >= record_date`, else `ex_date`, else `payable_date`) — the inverse of the upcoming unpaid gate. Same record/ex/payable window is collapsed (`paid` > `final` > `updated_estimate` > `preliminary_estimate`, then larger published dollars). Newest-first by payable/ex/record/as_of, **capped at 12**. Amounts and dates are never invented. `paid_history` is independent of `snapshot.prefer_publication_stages` so a current prelim snapshot still exposes prior paid years. Per-share paid rows need `nav_per_share` or `shares` to illustrate dollars; past `% of NAV` prelims still populate history without NAV. Dateless prelim/updated rows stay in `upcoming`, not `paid_history`. `XYZAX` is a gap (`paid_history: []`); CGHM without NAV has zero dollars so `upcoming` is also `null`.

**Sitrep example** — `$10,000` each, NAV from the Sep 2026 performance fixtures (`AMCPX` 45.70 / `AGTHX` 88.69), default snapshot (latest prelim). Both `upcoming` are null (2025 YE window is past). `paid_history` is newest-first:

```json
[
  {
    "ticker": "AMCPX",
    "fund_identifier": "amcap-fund",
    "upcoming": null,
    "paid_history": [
      {"distribution_dollars": "773.85", "estimated_tax": "193.46", "as_of": "2026-07-08", "publication_stage": "paid", "record_date": "2026-06-16", "ex_date": "2026-06-16", "payable_date": "2026-06-17"},
      {"distribution_dollars": "470.66", "estimated_tax": "117.67", "as_of": "2026-01-22", "publication_stage": "final", "record_date": "2025-12-12", "ex_date": "2025-12-12", "payable_date": "2025-12-15"},
      {"distribution_dollars": "587.97", "estimated_tax": "153.14", "as_of": "2024-12-17", "publication_stage": "final", "record_date": "2024-12-17", "ex_date": "2024-12-17", "payable_date": "2024-12-18"},
      {"distribution_dollars": "251.64", "estimated_tax": "67.48", "as_of": "2023-12-13", "publication_stage": "final", "record_date": "2023-12-13", "ex_date": "2023-12-13", "payable_date": "2023-12-14"},
      {"distribution_dollars": "496.02", "estimated_tax": "124.01", "as_of": "2022-06-15", "publication_stage": "paid", "record_date": "2022-06-15", "ex_date": "2022-06-15", "payable_date": "2022-06-16"},
      {"distribution_dollars": "256.24", "estimated_tax": "64.06", "as_of": "2021-12-15", "publication_stage": "final", "record_date": "2021-12-15", "ex_date": "2021-12-15", "payable_date": "2021-12-16"}
    ]
  },
  {
    "ticker": "AGTHX",
    "fund_identifier": "the-growth-fund-of-america",
    "upcoming": null,
    "paid_history": [
      {"distribution_dollars": "943.06", "estimated_tax": "235.77", "as_of": "2026-01-22", "publication_stage": "final", "record_date": "2025-12-17", "ex_date": "2025-12-17", "payable_date": "2025-12-18"},
      {"distribution_dollars": "970.12", "estimated_tax": "247.14", "as_of": "2025-12-17", "publication_stage": "final", "record_date": "2025-12-17", "ex_date": "2025-12-17", "payable_date": "2025-12-17"},
      {"distribution_dollars": "754.42", "estimated_tax": "194.55", "as_of": "2024-12-18", "publication_stage": "final", "record_date": "2024-12-18", "ex_date": "2024-12-18", "payable_date": "2024-12-18"},
      {"distribution_dollars": "526.67", "estimated_tax": "138.76", "as_of": "2023-12-15", "publication_stage": "final", "record_date": "2023-12-15", "ex_date": "2023-12-15", "payable_date": "2023-12-15"},
      {"distribution_dollars": "226.18", "estimated_tax": "59.71", "as_of": "2022-12-16", "publication_stage": "final", "record_date": "2022-12-16", "ex_date": "2022-12-16", "payable_date": "2022-12-16"},
      {"distribution_dollars": "685.37", "estimated_tax": "172.58", "as_of": "2021-12-17", "publication_stage": "final", "record_date": "2021-12-17", "ex_date": "2021-12-17", "payable_date": "2021-12-17"}
    ]
  }
]
```

AMCPX 2026 midyear is the June paid LT `$3.5365`/share. AGTHX keeps two 2025 rows because the YE reprint payable (`2025-12-18`) and the product-page payable (`2025-12-17`) are different published dates — not merged.

Holdings may send **`holding_dollars`** or **`weight_pct` + `book_dollars`**. `weight_pct` is Interactive Modules UI percent **0–100** (`25` = 25% of book; `1` = 1%). The server sets `holding_dollars = book_dollars × weight_pct / 100`.

### Current vs Proposed (`POST /illustrate/portfolio/compare`)

Interactive Modules **Current Allocation vs Proposed Allocation**. Same center-zero bars as fund compare, but each series is **Proposed − Current**.

**Single snapshot** (omit `periods`): one shared `snapshot` + `tax_rates`. **YoY** (send `periods[]`, e.g. `[{year:2024,as_of:…},{year:2025,as_of:…}]`): each period re-runs both books with that `as_of` pinned, or a calendar-year window when `as_of` is omitted (`snapshot.as_of_year`). Top-level `current` / `proposed` / `deltas` **copy the latest period** so the diverging-bar sketch still has one pair. `periods[]` is empty in single-snapshot mode.

Each holding sends `ticker` and/or `fund_identifier`, and **either** `holding_dollars` **or** `weight_pct` plus the side’s `book_dollars`. `weight_pct` is **0–100** (UI %). Capital Group HTML has no ticker column: Class A symbols in `app/aliases.py` resolve onto name slugs (`AMCPX` / `AMCAP` → `amcap-fund`, `AGTHX` → `the-growth-fund-of-america`, `ABALX` / CUSIP `024071102` → `american-balanced-fund`). Live ingest attaches those tickers/CUSIPs without changing the slug identity.

Each side is a full `/illustrate/portfolio` result plus `label` (defaults: `Current Allocation` / `Proposed Allocation`). Gaps stay on that side. Covered holdings include `upcoming` and `paid_history` (same convenience fields as `/illustrate/portfolio`).

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

**Sparse history:** Vanguard has ICI December year-end rows for 2021–2025 (≥$1B Admiral / mega ETFs) plus the 2025 YE HTML fixture for VFIAX / VBIAX / VIGAX. Fidelity has the **full 2024–2025 paid DPL6 books** + 2026 estimate (FBGRX plus 349 other 2024 tickers). A YoY `periods[]` pin that misses that `as_of` / year is an explicit **gap** on that side, not a silent $0. American Funds (AMCAP 2024–2025) and T. Rowe Price (TRBCX 2022–2025) have multi-year fixture snapshots. Among ranks 11–20, Northern Trust (NOSIX 2022–2025), BNY (DGAGX 2022–2025), and Schwab (SWTSX / SWSSX / SWISX / SWLGX 2021–2025; 2025 full annual PDF) have multi-year paid books; UBS and Nuveen stay single-vintage. State Street now has official XLSX paid YE 2021–2025 (SPY / SPYM / ALLW). **Amundi / Pioneer is included** (official 2023–2025 Pioneer/Victory tax-center books; PIODX / PIGFX performance). History packs prefer **US-domiciled** managers; Pioneer US retail is Victory-hosted after April 2025.

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

Interactive Modules can mount a **fund vs benchmark line chart** without calling tax endpoints. Tax YoY bars stay on `POST /illustrate/compare`. Weekly `python -m app.cli refresh` ingests **distribution estimates plus weekly NAV** (Yahoo last regular close). It does not refresh Growth of $X monthly performance series — those stay on `GET /performance`.

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

Goal: for **existing US-domiciled adapters**, ingest every **mutual fund and ETF** on the published distribution / capital-gains book — not 1–2 sample tickers. **Skip SMAs / separate accounts / institutional SMA sleeves** (drop those rows when a table mixes products). **Amundi / Pioneer is included** (Victory-hosted Pioneer tax center, Eric 2026-09-08). Do not invent amounts. Synthetic `ZZ*` parser samples stay samples. Large families should clear **>50 MF/ETF funds** when the public book lists that many.

**Wave 1:** unique tickers **431 → 1,168**; funds **482 → 1,298**.

**Wave 2:** unique tickers **1,168 → 2,165**; funds **1,298 → 2,434**.

**Wave 3 (MF/ETF-only + large-family 50-fund bar):** unique tickers **2,165 → 2,174**; funds **2,434 → 2,519**. SMA rows dropped. Tax / illustrate / performance contracts and weekly refresh are unchanged.

**Wave 4 (same MF/ETF filter; keep pushing thin large books):** unique tickers **2,174 → 2,205**; funds **2,519 → 2,630**. BNY ETF $0.00 book, JPM MMKT 19a, MSIM ETF income table, plus ranks 31–35 paying-fund PDFs (JH / Hartford / Macquarie). Tax / illustrate / performance contracts and weekly refresh are unchanged.

**Wave 5 (ranks 1–40 only):** ranks 1–40 unique tickers **1,771 → 1,878**; funds **2,112 → 2,294**. Vanguard 2021–2023 ICI are column-safe full December books (239 → **297** tickers; wrap/DAILY name bleed dropped so `fund_name` stays ≤512). Artisan cleared 50 tickers via the 2025 Year-End Tax Reporting ICI PDF (2 → **51**). John Hancock cleared 50 funds (45 → **56**). First Eagle open-end estimate book expanded (3 → **11**). Thrivent / Calamos / Wasatch / GMO Trust paying books expanded. No new work on ranks 41–110. Capital Group / BlackRock OEF / Invesco MF ticker enrichment was not possible — official books are name-only. SSGA / GS / PIMCO / UBS / Franklin / Schwab remain SPA or 403.

**Wave 6 (ranks 1–40 only):** ranks 1–40 unique tickers **1,878 → 1,924**; funds **2,294 → 2,505**. Highest-impact unlocks: MFS 2025 % of NAV fly PDF is now the full published book (2 → **175** funds; cleared 50). First Eagle 2024 official paid PDF is the full share-class book (3 → **40** tickers). Northern Trust recovered NOMIX / NSGRX / NSCKX CG plus December ICI income-only equity rows where the CG book is em-dash (13 → **22**). ICI totals for CG-paying NT tickers (NOSIX) were not stored as income (would double-count). No new work on ranks 41–110. Amundi skipped. SMAs / interval / CEF omitted.

**Wave 7 (year-depth, ranks 1–40 only):** Fidelity 2024 DPL6 is now the **full 350-ticker** Wayback book (was FBGRX-only). American Century gained the official **2022** retail estimate book (TWCGX LT $0.7247; 266 non-zero share classes). MFS unlocked official 10-year Excel December YE **2021–2024** for MIGHX / MITTX. Principal product pages added **2023–2024** paid YE (PQIAX / PEMGX). Artisan 2021–2023 ICI PDFs remain public but transposed / not column-safe. CGHM left as-is (inception 6/25/24; 2024–2025 official tables em-dash).

**Wave 8 (year-depth, ranks 1–40 only):** MFS 10-year Excel expanded beyond MIGHX / MITTX to official Class A product pages (MEIAX / MFEGX / MFRFX / OTCAX / MVCAX / MSFRX / MGRAX / MGIAX / MNDAX / MTCAX / MMUFX). Northern Trust added the official **2021** equity CG book (NOSIX LT $0.985777). Macquarie added the official **2023** CGE-RET-ACT paying book (WSTAX LT $5.331; 20 Class A tickers). Fidelity 2021–2023 still HPDY SPA / no CDX prior-year HTML. ACI 2021/2024 siblings 404 (unversioned September PDF is the 2023 book). Artisan 2021–2023 ICI public but token order / Box 1a breakdown not column-safe. First Eagle 2022 skipped (prior 403). Invesco ICI still 406. CGHM / YoY / render.yaml disk left as-is.

**Wave 9 (year-depth, ranks 1–40 only):** Northern Trust 2022–2024 equity CG PDFs are now the full paying-fund books (were NOSIX/NOLCX/NOMIX flagships). Schwab gained official 2021 YE product-page rows for SWTSX / SWPPX plus 2025 SWLSX LT $0.4957. Columbia 2024 YE PDF remains wrap-unsafe (not expanded). Fidelity 2021–2023 still HPDY SPA (Wayback DPL6 closest-match served the 2024 book). SSGA historical XLSX still no stable URL. GSAM advisor 403. PIMCO 2025 tax PDF is 1099 character, not ST/LT $/share. MSIM 2023 ETF PDF Akamai 403. Invesco ICI 406. DFA `.../2021-2023-distributions.pdf` aliases serve the 2024 file. Principal product-page CG history still starts 2023. Lord Abbett paying-fund PDF 404. Eaton Vance open-end still missing. Amundi skipped.

**Wave 10 (year-depth, ranks 1–40 only):** Dimensional 2024 paid December PDF is now the full MF/ETF book (was DISVX/DFELX/DFQTX flagships; 138 tickers; DISVX LT $0.184 unchanged). Macquarie 2024 CGE-RET-ACT-2024 is the full Class A paying-fund table (was WSTAX/WLGAX/DDVAX; 16 tickers; WSTAX ST $1.108 / LT $8.135 unchanged). Hartford 2024 final equity PDF is the full paying-fund table (was HFMCX/HAIAX/IHGIX; HFMCX LT $1.67 unchanged). AllianceBernstein 2023 Wayback GEN–5796–1023 is the full paying-fund table (was AGRFX/APGAX/ABASX; AGRFX LT $6.95 unchanged). John Hancock 2022–2024 sibling PDFs 403 from this client (leave flagship transcriptions). Fidelity 2021–2023 still HPDY SPA. SSGA / GSAM / PIMCO / MSIM open-end / Invesco ICI / Columbia wrap-unsafe / Amundi unchanged.

**Wave 11 (ranks 1–40 thin-family harvest):** State Street unlocked the official Historical Distributions XLSX (`/library-content/products/fund-data/etfs/us/spdr-etf-historical-distributions.xlsx`; 3 → **170** tickers). Schwab unlocked the official 2025 Actual Annual Distributions PDF (`schwab.bynder.com/m/3990d008e1558d0d/`; 4 → **79** tickers) plus SWSSX / SWISX / SWLGX 2021–2024 product-page history. Franklin added FTF / TEI / SMDLX Section 19(a) notices (1 → **4**). PIMCO open-end ST/LT PDF still missing (ZZPIM* remain samples). GSAM advisor tax center still 403. Amundi skipped.

**Wave 2 lookback (2021–2025 YE finals, $/share only, MF over ETF):** American Funds public YE CG books now have tax-year as_of for 2021–2025 (Wayback id_ for 2021–2024; live 2025 table). Class A product-page history adds December OI / special / published LT for ABALX (2022–2023 LTCG is published $0 — omitted) plus ICA / WMIF / New Perspective / EUPAC / New World / American Mutual / Capital Income Builder / Fundamental Investors / SMALLCAP World / Income Fund of America / Bond Fund of America / New Economy / High-Income Trust / Capital World Bond / U.S. Government Securities / International Growth and Income. Unpublished December years (e.g. SMCWX 2022) stay unmatched. Invesco ICI Primary broker XLSX is the 2023–2025 December book. Vanguard / T. Rowe already have full MF YE books. Fidelity 2022–2023 DPL6 still unpublished (FCNTX highlights only). BlackRock live 2025 h3 tables are not column-safe. JPMorgan 2021–2023 19a URLs still 404. `lookback_5y` splits MF vs ETF. Missing years stay unmatched / Undisclosed — never invented as $0 or ST/LT splits. Bare QDI % excluded.

**Wave 3 lookback (remaining thin MF families, 2021–2025 YE finals only):** Official books only — never invented. Full-fixture `lookback_5y` after Wave 2 deploy was **755 / 582 MF / 173 ETF**; after this wave **762 / 589 MF / 173 ETF** (`+7` five-year MFs, ETF unchanged). **Densified:** **BNY** product-page Distributions History for DGAGX / DAGVX / DREVX / DREQX / DNLDX / PGROX / DGLAX (December YE 2021–2025; OI = published NQ+Q dividends; ST = published NQ+Q ST; $0 omitted). Family YE coverage **0/1/1/1/1 → 7/7/7/7/7** with **7** funds at 5y (was 0). DGAGX 2021 LT $1.6171; DAGVX 2021 LT $6.7140. DMCVX / PEOPX product URLs 404; Research Growth page prints DREQX (not DWOAX Class A). **Columbia** 2022 + expanded 2024 YE PDFs (December Class A; Advisor when no Class A; June skipped; published $0 omitted). Family YE **0/0/0/2/0 → 0/38/0/42/0** — **0** new 5y funds (2021 estimates; 2023/2025 YE 404). LBSAX 2022 LT $0.56114 / 2024 LT $1.38581; CBLAX 2022 LT $1.55549; Large Cap Growth Class A is LEGAX LT $4.05105; ELGAX is Select Large Cap Growth Dec LT $0.72066. **Dimensional** official 2023 + 2025 Mutual Funds Tax Sheets (Paid in year; NII/ST/LT $/share; dashes omitted; QDI % skipped). Family YE **0/0/0/138/0 → 0/0/46/138/50** — **0** new 5y funds (no 2021–2022 tax sheet; `.../332797/.../2021|2022|2023-distributions.pdf` still alias 2024). DISVX 2023 LT $0.025620 / 2025 LT $1.059970. **Skipped (noted, not invented):** Fidelity 2022–2023 DPL6 still HPDY SPA / not in CDX; JPM 2021–2023 19a still 404 and 1099 character-% notices are not $/share; Invesco 2021–2022 ICI XLSX 404; Franklin open-end estimate hub remains a JS SPA; BlackRock live 2025 OEF HTML still not column-safe; GSAM 403; PIMCO no ST/LT $/share PDF. Missing years stay unmatched / Undisclosed.

**Wave 5 lookback (next harvestable official YE books after Wave 4):** Official books only — never invented. Full-fixture `lookback_5y` after Wave 4 was **785 / 612 MF / 173 ETF**; after this wave **800 / 627 MF / 173 ETF** (`+15` five-year MFs, ETF unchanged). **Densified:** **Causeway** official `YYYY_Causeway-Funds-Final-Distributions.pdf` 2021–2023 (CIVIX 2021 income $0.3170 / published $0.0000 ST/LT stored; 2022 income $0.2834; 2023 ST $0.1678 / LT $0.1748). Family YE **0/0/0/10/10 → 12/12/10/10/10** with **10** funds at 5y (was 0): CIVIX / CIVVX / CGVIX / CGVVX / CEMIX / CEMVX / CIISX / CVISX / CIOIX / CIOVX. Concentrated Equity CCENX / CCEVX is on 2021–2022 only — later years unmatched. **Matthews Asia** official Investor product-page December YE adds MAPIX / MSMLX / MCHFX / MASGX / MCSMX (MAPIX 2021 LT $2.31785 / 2025 income $0.26050; MSMLX 2021 ST $1.52123 / 2025 income $0.38648; MCHFX 2022 LT $1.09205). Family **3 → 8** funds at 5y. Quarterly MAPIX non-December income omitted so one as_of is not summed. MPACX has no 2025 YE row; MJFOX has no 2023 YE row; MATFX stops at 2023 — gaps, not invented. **Skipped (noted, not invented):** Macquarie CGE-RET-ACT-2021 still 404 (15 Class A remain near-4); Victory 2022 Final PDF is live but 2021/2023 siblings 404 (no 5y unlock); Fidelity DPL6 SPA; JPM 19a 404; Invesco 2021–22 XLSX; Franklin SPA; BlackRock unsafe HTML; GSAM 403; PIMCO no ST/LT; Principal product pages still truncate before 2021–2022; Virtus year-alias; Hartford 2021–23 sibling PDFs are HTML; Federated 2023/2024 0-byte; Schwab extra product pages 403; Oakmark 2021–23 news 404; Amundi 2021–22 finals 404; Jensen 2021–23 sibling PDFs 404; Royce year URLs are 404 SPA shells. Missing years stay unmatched / Undisclosed.

**Wave 6 lookback (highest-impact in-universe 5y gap after live inventory 2026-09-10):** Official books only — never invented. Live `lookback_5y` before this wave was **800 / 627 MF / 173 ETF** (19.8% of 4,046 book funds). Categories were 88.0% (675 uncategorized / 5,614) and weekly NAV 80.4% (4,514 / 5,614) — 5-year paid history is the beta-visible hole. **Densified:** **American Beacon** official tax-center YE PDFs 2021–2024 for the 110-ticker 2025 book that had finals in 2025 only (family YE **0/0/0/0/110 → 122/110/94/102/110**). **73** funds reach 5y (was 0), including AADEX / AVFIX / ABCIX / AHLIX. AADEX 2021 LT $2.2327 / 2022 published ST $0.0001 / LT $2.3936 / 2023 LT $0.8312 / 2024 LT $2.5614 / 2025 LT $2.3846. All-dash rows omitted (SFMIX 2023 has no printed amounts — unmatched, not invented). Expected live lift after Manual Deploy: **800 → ~873** five-year funds (`+73` MF; ETF unchanged). **Skipped (noted, not invented):** Invesco 2021–2022 ICI XLSX still unpublished on the open-end tax guide (580 tickers already have 2023–2025); Fidelity 2022–2023 DPL6 still HPDY SPA; Alger `Distrib_FUNDS_2024.pdf` 404; Victory 2021 final sibling still 404 (2023 final is now live but does not unlock 5y without 2021). Missing years stay unmatched / Undisclosed.

**Wave 7 lookback (highest-impact reachable YE after Beacon):** Official books only — never invented. Live `lookback_5y` after Beacon was **873 / 700 MF** (`seed` still running at probe time). **Preferred families blocked this session:** American Century paid-family 2021/2024 siblings 404 and product pages print 2025-only (TWCGX Total $9.7631); Invesco open-end ICI 2021–2022 still **406**; Alger MF `Distrib_FUNDS_2024.pdf` / 2023 / 2021 siblings 404. **Densified:** **Victory** official 2022 hyphenated I/II final + 2023 space-encoded I/II / RS / Portfolios III finals + 2024 RS / III companions (MMEAX 2022 LT $2.389672 / 2023 LT $0.390522 / 2024 LT $3.015874 / 2025 LT $3.922505; VETAX 2022 LT $2.782434 / 2023 LT $2.095967; RSGRX 2023 LT $0.036599 / 2024 LT $2.023191; USSPX 2023 LT $0.515883 / 2024 LT $1.855318). VIP / variable-insurance series omitted. Family I/II+RS+III YE moves from 2024–2025-only toward **2022–2025** (4y, not 5y — 2021 sibling still 404). **Alger** official unversioned `Distrib_FUNDS.pdf` Wayback `20230330013818` is the 2022 paid MF book (ACAAX LT $0.8384; ALARX LT $0.9783; SPECX LT $0.3918; 65 tickers mapped from the official 2025 name+class print). Global Focus / International Focus / Weatherbie Enduring Growth 2022 name rows omitted (2025 names differ). Official `Distrib_ETFS.pdf` + Wayback 2021/2023 add ATFV / FRTY / AWEG (FRTY 2021 ST $1.0687; AWEG 2025 LT $0.45647). **Expected live lift after Manual Deploy:** year-depth, not a 5y unlock (`funds_with_5y` stays ~873 until a 2021 Victory or 2021/2023/2024 Alger MF book appears). Leave `SEED_FORCE_FULL` **off** — warm delta should ingest the new fixture fingerprints. Smoke: `MMEAX` / `VETAX` / `RSGRX` / `USSPX` / `ACAAX` / `ALARX` / `FRTY`. **Still blocked (not invented):** American Century 2021/2024 paid family book; Invesco ICI 2021–2022 406; Alger MF 2021/2023/2024; Victory 2021. Missing years stay unmatched / Undisclosed.

**Wave 4 lookback (next harvestable official YE books after Wave 3):** Official books only — never invented. Full-fixture `lookback_5y` after Wave 3 was **762 / 589 MF / 173 ETF**; after this wave **785 / 612 MF / 173 ETF** (`+23` five-year MFs, ETF unchanged). **Densified:** **Northern Trust** 2024/2025 `estimated-capital-gains-*.pdf` files are paid YE books (page copy: “Northern Funds paid capital gain distributions”); `infer_stage` now treats paid + year-end page copy as `final` even when the filename contains `estimated` (Macquarie CGE-RET September estimate stays preliminary). Family YE **19/16/10/0/7 → 19/16/10/15/22** with **9** funds at 5y (was 0): NOIEX / NOLCX / NOLVX / NOMIX / NSGRX / NSCKX / NSIDX / NOSGX / NOSIX. **MFS** official 10-year Class A Excel adds MRGAX / MDIDX / MWEFX / MWOFX / MIDAX / MAGWX / MAMAX / MRSAX / NDVAX / BRWAX (MRGAX 2021 LT $2.03573 / 2025 LT $6.24390; MDIDX 2021 LT $0.20404 / 2025 LT $0.75145; MRSAX 2021–2024 income only; BRWAX 2023 income only). Family **11 → 21** funds at 5y. Same-Class-A aliases skipped. **Allspring** Institutional `/i/` product pages add EIVIX / EGOIX / ESPNX (2021–2025 YE CG) and EMGNX (December income only; no published CG). Family **2 → 6** funds at 5y. **Macquarie** official paid books CGE-RET-ACT-2022 (WSTAX LT $12.373) and unversioned CGE-RET-ACT 2025 paid (WSTAX LT $10.603; Nomura-branded; distinct from CGE-RET estimate). Family YE **0/0/20/16/0 → 0/41/20/16/21** — **0** new 5y (CGE-RET-ACT-2021 404; 15 Class A now near-4 for 2022–2025). **Skipped (noted, not invented):** Principal product pages truncate before 2021–2022; Invesco 2021–2022 ICI XLSX still 406; Virtus `8ua/202N-mfs_distributions_calyr_detail.pdf` year URLs alias the 2025 file; Hartford 2021–23 sibling PDFs are HTML; Schwab extra product pages 403; Amundi 2021–22 finals 404; Oakmark 2021–23 news URLs 404; Federated Preliminary+Capital+Gains 2023/2024 0-byte; Columbia 2021/2023/2025 YE siblings still 404; Fidelity DPL6 SPA; JPM 19a 404; Franklin SPA; BlackRock unsafe HTML; GSAM 403; PIMCO no ST/LT PDF. Missing years stay unmatched / Undisclosed.

**Wave 12 (estimate-feed readiness):** Every top-40 family except **Amundi** now has a `live=True` estimate hub/PDF in adapter config so `python -m app.cli refresh` and `POST /ingest/fetch` walk the real issuer URL weekly. Seasonal empty / 403 / SPA / PDF-bytes pages are **no-op success** (fixture fallback; no invented zeros). `GET /coverage` exposes `estimate_feed_ready`, `estimate_feed_status` (`prelim_updated` | `paid_history_only` | `deferred` | `skipped`), `history_years`, `performance_tickers`, and `lookback_5y` (count of funds with official final/paid per-share amounts in each of 2021–2025, plus `%` of the book with ≥5 distinct YE years). Missing years stay unmatched — never invented as $0. Bare `%` QDI columns are excluded. Growth of $X fixtures added for mapped distribution tickers: ABALX, VIGAX, VBIAX, TRBCX, DODGX, SWTSX, SWANX, NOSIX, MDDVX, JDCAX, ALLW.

**Wave 13 (10k bar + distribution-space families + ticker intake):** Fixture unique tickers **~3,400 → 3,561** (35.6% of the 10,000 aspiration; already above the 1,000+ launch bar). First Eagle keeps the full 2025 estimate + 2024 40-ticker paid book; 2025 family paid PDF sibling URLs 404 (product-page heroes stay SGENX / SGOVX / FEVAX). VanEck unlocked official 2025 ETF estimate payers (CLOB / CLOI / EINC) plus the full 2024 ETF YE book (13 → **56** tickers; GDX / SMH / MOAT / IBOT / MOTG; printed None omitted). WisdomTree added the official 2024 final CG payer book (7 → **9**). **First Trust** is now a registered adapter (rank 111) from the official 19(a) ContentGUID notice (BFAP / BFJL / BGLD / IGLD). Federated 2025 prelim PDF is the full **87**-class book (was PAYR 19(a) only). JPM 2024 19a Appendix A and Thrivent 2024 Wayback paid table add year depth. GMO ETF Trust 2025 prior-year 1099-DIV is December income + any-month ST. Harbor / Nationwide / Voya / Oakmark estimate hubs are on the weekly walk. `POST /requests/tickers` records a Website-submitted ticker; `POST /ingest/ticker-requests` picks it up. Never invents amounts. Amundi skipped. SPA/403 still deferred. Growth of $X fixtures added from Yahoo monthly adj close for SGENX / FEVAX / GDX / SMH / GTR / WTPI.

**Wave 14 (ranks 41+ three-pillar densify):** Fixture unique tickers **3,561 → 3,583**. Thin top-40 leftovers stay deferred (SSGA Angular, GSAM 403, PIMCO no ST/LT PDF, Franklin SPA, Eaton Vance open-end missing, Lord Abbett no-pay-only, UBS 403, First Eagle 2025 paid PDF 404). Started **beyond-40 families 41–53** with the same playbook (annual performance / historical YE / estimate hub even if empty). Official 2024 books harvested (never invented): Voya 2024 estimate (NLCAX LT $1.905); Oakmark 2024 Wayback paid YE (OAKEX ST $0.0276 / LT $0.7241; published $0 CG stored); Tweedy 2024 estimate (TBGVX LT $1.706; printed None ST omitted; 2024 Final sibling 404); Gabelli 2024 1099 YE summary via Wayback (GABGX LT $6.96640; live GET 403); Royce 2024 Investment-class paid YE (RYTRX ST $0.0584 / LT $0.2980); Victory 2024 final Class A book (MMEAX ST $0.801347 / LT $3.015874); SEI 2024 estimate (SIMT Large Cap Growth ST $1.541 / LT $7.596); Brown Advisory 2024 schedule (BAFFX ST $0.15 / LT $1.72); William Blair 2024 Class I (BGFIX LT $3.03562). Harbor / Nationwide 2024 ST/LT family books still missing (Harbor 2024 PDF 404; Nationwide MFN-0434AO / MFN-1042AO are not CG grids). NYLI / Touchstone 2024 ST/LT books not found. Weekly estimate hubs now live for Tweedy, Gabelli, Royce, NYLI, Touchstone, Victory, SEI, Brown Advisory, and William Blair (empty/403/PDF-bytes = no-op success). Amundi skipped. Growth of $X fixtures added from Yahoo monthly adj close for HACAX, NWHOX, NLCAX, OAKMX, TBGVX, GABGX, RYTRX, MMEAX, BAFFX, BGFIX.

**Wave 16 (Website Submit-ticker + FE / VanEck / First Trust):** Website `POST /request/ticker` / `GET /request/ticker?status=queued` is the beta intake (201 queued / 200 already_covered / 422 invalid; SQLite `ticker_requests`; weekly `POST /ingest/ticker-requests` fetches the matched adapter and never invents amounts). Official densify: First Eagle 2025 ETF paid PDF (FEGE income $0.589 / ST $0.000 / LT $0.000; FEOE $0.738 / $0 / $0; open-end 2025 paid siblings still 404); VanEck 2024 paid mutual-fund YE (INIVX income $0.7750; MWMIX ST $1.4731 / LT $1.4325; printed None omitted); First Trust Capital Management 2025 table is interval / tender-offer (omitted) and Vest “Coming Soon” rows omitted. Growth of $X added for FEGE, MWMIX, BGLD.

**Wave 17 (VanEck / First Trust / WisdomTree densify + weekly ticker pickup):** Fixture unique tickers **3,591 → 3,824**; funds **3,870 → 4,102** (38.2% of the 10,000 aspiration). Official books only: VanEck 2023 equity-ETF YE (GDX income $0.5001; IBOT ST $0.6716) + 2023 MF YE (INIVX $0.0102; MWMIX ST $1.6352) + 2025 paid MF/ETF YE (INIVX $1.5675; MWMIX ST $1.9529 / LT $1.6944; GDX $0.6331; MOTG ST $1.8899 / LT $4.0549; printed None / all-None / finals-to-come omitted) → **71** tickers. First Trust 24 Sep 2025 family declaration of **146** ETFs (FVD $0.2519; FTHI $0.1710; FPE $0.0845; CIBR $0.0006; blank LT omitted) → **150** tickers with the 19(a) sleeve. WisdomTree official December 2025 income declaration is the family income book (**85** tickers; DGRW $0.23270; published $0.00000 income stored; printed $0.00000 ST/LT omitted). Jensen 2024 official PDF (JENSX / JENIX LT $6.77; Mid Cap LT $1.10 without printed tickers omitted). Diamond Hill 2024 estimate sibling (DHLAX ST $0.035 / LT $2.900). First Eagle 2025 open-end paid siblings still 404; Gold / GIB / Small Cap remain Drupal SPAs. WisdomTree 2023 ETF final sibling still not a stable public file; Digital Funds omitted. Ranks 63–90 now have `live=True` estimate hubs on the weekly walk (empty/403/PDF-bytes = no-op success; Impax stays deferred/geo-gated). Weekly Action runs `python -m app.cli ticker-requests` after refresh. Growth of $X added for INIVX, FEOE, XC, FVD, JENSX. Amundi skipped. Never invents amounts.

**Wave 18 (ranks 41–110 densify + weekly estimate hubs):** Fixture unique tickers **3,825 → 3,993**; funds **4,108 → 4,281** (39.9% of the 10,000 aspiration; +168 tickers / +173 funds). Official books only — never invented. **Victory** 2025 estimate + official finals for Portfolios I/II, RS, and Portfolios III / USAA (MMEAX LT $3.922505; VETAX $1.677515; RSGRX $1.817625; USSPX ST $0.026267 / LT $2.615144) → **150** tickers; Pioneer / Victory Portfolios IV stays on skipped `amundi`. **Harbor** Institutional tickers from the official prospectus (HACAX LT $11.89; HSICX published $0.00 LT stored; HAVLX LT $3.69) → **9** tickers; monthly-income-only / no-CG rows omitted. **NYLI** full paying flyer Class I (MLAIX LT $1.01–$3.00) → **24** tickers. **Touchstone** Class A + official ETF tickers TSEC / SIO / TUSI (TVLAX LT $1.28631) → **10** tickers / **18** funds (remaining PDF rows name-only). **First Eagle** 2025 family paid PDF sibling URLs still 404; product-page 2025 paid grids now scrapeable (SGENX LT $4.654; FEFAX ST $0.339 / LT $2.015; published $0.000 stored) → **42** tickers; Overseas I/R6 not separately printed; interval / CEF omitted. Nationwide 2025 PDF 403 this session — deferred. Gabelli live PDF 403 this session — existing fixture left as-is. Ranks 91–110 now have `live=True` estimate hubs on the weekly walk (empty/403/PDF-bytes = no-op success). Queued Website ticker-requests: **none**. Growth of $X added for HAVLX, VETAX, FEFAX, YACKX. Amundi skipped.

**Wave 19 (ranks 41–110+ thin-family harvest):** Fixture unique tickers **3,988 → 4,225**; funds **4,268 → 4,542** (42.2% of the 10,000 aspiration; +237 tickers / +274 funds; Amundi / Pioneer excluded from the count). Official books only — never invented. **American Beacon** full 2025 share-class YE via Wayback after live WP 403 (AADEX ST $0.3607 / LT $2.3846) → **110** tickers; all-dash rows omitted. **AMG** full printed I/N/Z YE (YACKX LT $2.8135) → **71** tickers; SMA + monthly no-CG omitted; Harding/Tweedy stay on their adapters. **Lazard** full Institutional / Open / R6 estimate (LZIEX ST $0.20 / LT $1.50) → **40** tickers; all-dash Concentrated / High Yield omitted. **Harding Loevner** official media PDF is the full share-class book (HLMNX LT $3.415402) → **16** tickers. **Baird** Inst+Inv equity payers (BSVIX LT $1.23087) → **8** tickers; bond / SMID printed None omitted. **GQG** full Inst/Inv/R6 + GQGU (GQEIX LT $0.81; published $0.00 stored) → **16** tickers. **LSV** Inst+Inv YE (LSVEX LT $4.4395) → **14** tickers. **Boston Partners** printed Inst/Inv (BPAIX LT $2.73) → **12** tickers; EM Dynamic dash/liquidation omitted. **Manning & Napier** December CG-paying CUSIP rows (CEIIX LT $0.46350) → **4** tickers / **36** funds; monthly income-only omitted. **Buffalo** remaining Investor-class estimate rows (BUFEX LT $3.35047) → **8** funds. Nationwide live MFN-0435AO 403 and Gabelli live 2025 memo 403 this session — deferred after noting; existing fixtures left as-is. Homestead / Boston Trust / Ariel live PDFs 403. Amundi skipped. Weekly estimate hubs added for Beacon / AMG / Lazard tax pages (empty/403/PDF-bytes = no-op success). Growth of $X added from Yahoo monthly adj close for AADEX, LZIEX, BSVIX, GQEIX, LSVEX.

**Wave 20 (ranks 41–110 remaining thin-family harvest):** Fixture unique tickers **4,228 → 4,358**; funds **4,545 → 4,706** (43.6% of the 10,000 aspiration; +130 tickers / +161 funds; Amundi / Pioneer excluded from the count). Official books only — never invented. **Royce** full printed 2025 ticker book (RYTRX ST $0.0257 / LT $0.7656) → **34** tickers; printed em-dashes omitted. **Oakmark** Investor / Advisor / Institutional / R6 with official tickers from oakmark.com/our-funds/ (OAKEX LT $0.7640; OAKMX income $1.5797; published $0.0000 stored) → **32** tickers. **Kinetics** full share-class YE (WWNPX LT $8.68572; published $0.00 stored) → **23** tickers. **Meridian** full share-class YE (MVALX ST $0.86910 / LT $4.10477; published $0.00 stored) → **18** tickers. **Hennessy** Investor + Institutional December YE (HFCSX LT $17.84742) → **27** tickers; quarterly / monthly income-only and Cornerstone Growth Investor “no 2025 distributions” omitted. **Marsico** full Investor + Institutional (MFOCX LT $4.9890; MXXIX is Midcap Growth Focus) → **10** tickers. **Heartland** Investor + Institutional (HRTVX ST $0.05228 / LT $4.34950) → **6** tickers. **RiverPark** Institutional + Retail paying rows (RPXIX LT $2.6688) → **6** tickers; all-dash omitted. **Longleaf** product-page LLPFX + LLSCX (income-only $0.3415) + LLGLX (ST $0.1104 / LT $0.8608); International sibling 404. **GuideStone** full paying-fund table → **7** tickers / **21** funds (Investor tickers only where previously identified; rest name-only; all-dash bond/RE/Impact omitted). **Diamond Hill** remaining paying funds name-only except DHSCX / DHPAX / DHLAX. **Baillie Gifford** EAFE Plus / International Alpha name-only (LT $1.6704 / $1.3236); all-dash omitted. **Brandes** International Small Cap + EM Value name-only; Tax-loss Core Plus / SMART omitted. **FAM** published $0.00 stored; Institutional Small Cap name-only. **Madison** official ETFs MAGG LT $0.00386 / MSTI LT $0.05541. **Driehaus** full book; tickers only DMCRX / DMAGX. Already-deferred 403/SPA left as-is: Nationwide, Gabelli, Homestead, Boston Trust, Ariel. New 403 this session — deferred: Hotchkis, Champlain, FMI, Impax, Locorr, Conestoga, Jensen, Causeway. Amundi skipped. Weekly estimate hubs added for Kinetics / Meridian / RiverPark / Longleaf (empty/403/PDF-bytes = no-op success). Growth of $X added from Yahoo monthly adj close for HFCSX, WWNPX, MERDX, MFOCX.

**Wave 22 (Amundi / Pioneer included):** Official Pioneer / Victory Portfolios IV tax books are now on the weekly estimate ladder per Eric 2026-09-08. Unique Amundi tickers **4 → 64**; funds **4 → 64**. `estimate_feed_status=prelim_updated`, `estimate_feed_ready=true`. Live hubs: Pioneer tax center, Amundi US tax center (redirects to Pioneer), Victory tax center, plus the 10/15/2025 estimate PDF and 2025 final PDFs that still resolve (Pioneer path + Victory-hosted Portfolios IV). Official books only — never invented: 2025 Class A estimate (PIODX ST $0.53 / LT $3.73 / 9.09% of NAV); 2025 finals all printed open-end share classes (PIODX Class A ST $0.8354 / LT $3.4776; published $0 stored; N/A omitted; Pioneer ILS Interval Fund XILSX omitted); 2024 Final Capital Gain Distributions (PIODX LT $4.1900; PGSVX / PISVX); 2024 special year-end income estimates (Class Y PICYX / STRYX); 2023 finals + 10/31/2023 estimates. Growth of $X from Yahoo monthly adj close for PIODX / PIGFX. Ticker intake no longer skips `amundi`. Weekly `refresh` / `POST /ingest/fetch` walk Amundi with every other family (live first, fixture fallback).

**Wave 23 (mega / $1B+ ETF densify):** Official issuer books only — never invented $0 for unpublished years. Live `GET /funds` (seed=complete) was missing advisor-core ETFs (QQQ, IVV, IWM, EFA, AGG, GLD, SCHD, ACWX, IEMG, IEFA, ITOT, TLT, LQD, HYG, VNQ, ARKK, BNDX). **iShares** official stamped distribution-summary PDFs 2021–2025 are now December YE ICI Primary CSVs (**~338–377 tickers/year**; IVV Dec 2025 $2.413592; IWM $0.842454; AGG $0.326375 + $0.334012; ITOT $0.486672). Expected unique-ticker lift **~300+** iShares income payers that the CG HTML never listed. **Vanguard** ICI appends VNQ / BNDX December YE (VNQ 2025 $0.800500; BNDX monthly $0.104400 + YE $0.968600; 2021 BNDX official ST $0.005900 stored). **Schwab** ETF product pages add SCHD / SCHX / SCHB / SCHF / SCHG December YE (SCHD 2025 $0.2782; official $0.0000 ST/LT stored). **ARK** is a new rank-114 adapter from the official 2021 FINAL handout (ARKK ST $0.5249 / LT $0.2577); 2022 official “no distributions” is not stored as invented $0; 2023–2025 PDFs unpublished. **GLD** official FAQ (grantor trust makes no distributions) → 2025 published $0.000000. **QQQ** official Invesco QQQ Trust financial highlights (N-30B-2 / HK annual report) publish fiscal-year ordinary-income per share for years ended September 30 (2025 $2.84 / 2024 $3.04 / 2023 $2.17 / 2022 $1.97 / 2021 $1.77) — full-year paid totals, not a single December payable; quarterly US YE $/share notices were not column-safe. **JEPI / JEPQ** US monthly income $/share is not on a column-safe am.jpmorgan.com / 19a page (Dec 2025 ETF 19a Appendix A has no JEPI/JEPQ because they paid no CG). Official US fiscal-year ordinary-income per share is in the J.P. Morgan Exchange-Traded Fund Trust N-CSR Financial Highlights (years ended June 30): JEPI 2025 $4.67 / 2024 $4.16 / 2023 $6.04 / 2022 $4.96 / 2021 $4.85; JEPQ 2025 $6.11 / 2024 $4.86 / 2023 $5.64 / 2022 commencement stub $0.38. AU/CA JEPI unit amounts are a different share class — not used. Categories added for the new mega tickers. **Follow-on ≥$1B family-book expansion:** official Vanguard ICI December YE for VGT / VFH / VCIT / VCSH / VTEB / VMBS / VGSH / VGIT / VGLT / VONG / VONV / BNDW / sector ETFs (VGT 2025 $0.757000; VCIT Dec monthly $0.322300 + $0.335800); official Schwab product-page December YE for SCHA / SCHM / SCHE / SCHV / SCHP / SCHZ / SCHH / SCHC / FNDF (SCHA 2025 $0.1301; SCHM 2025 $0.1334). Still unmatched (no column-safe official US income $/share this wave — not invented): QQQM, RSP, SPHD, SPLV, JPST, JAAA, GLDM, MDY, FNDX / FNDE / FNDA. **Manual Deploy:** leave `SEED_FORCE_FULL` **off** — warm disk densifies changed fixture fingerprints only. Smoke after seed: `GET /funds?q=QQQ` / `IVV` / `IWM` / `AGG` / `JEPI` / `SCHD` / `ARKK` / `VNQ` / `GLD` / `VGT` / `SCHA`.

**Wave 9 densify toward 10k (Nuveen full estimate book + Franklin DIST-SUMM CEFs):**
Official issuer books only — never invented. **Nuveen** 2025 estimated taxable distributions PDF
(`documents.nuveen.com` uniqueId `3c3be13d-d800-48e2-a537-c251162ab9f4`, `download=1`)
is the **full mutual-fund share-class book** — **~521 tickers** after omitting 7 SMA /
Managed Account rows (`is_excluded_product`). Heroes: TIIRX LT **$1.97** (6.49% of NAV);
NSBAX ST **$0.04** / LT **$4.89**; TINRX ST **$0.21** / LT **$0.33**. Manager-printed
`$-` stored as published **$0.00**. 2025 tax-character letters (QDI / US-gov %) skipped.
**Franklin Templeton** DIST-SUMM 2025 CEF calendar totals
(`franklintempleton.com/forms-literature/download/DIST-SUMM`) — **28 CEFs** after
skipping Royce (RGT/RMT/RVT stay on the Royce adapter). Heroes: FT income **$0.341** /
LT **$0.145** / RoC **$0.024**; EMO income **$0.756** / RoC **$3.504**. Open-end
Franklin / Putnam estimate hub remains a JS SPA — FKINX / PEYAX unmatched.
Skipped this wave (no column-safe family ST/LT $/share): Allspring 20251010 product-alert
(HTML login gate); GS 2025 1099 character letter; PIMCO / Lord Abbett / Eaton Vance /
PGIM / Baron; unmatched $1B+ ETFs **QQQM / RSP / SPHD / SPLV / JPST / JAAA / GLDM /
MDY / FNDX / FNDE / FNDA**. JPM 19a is name-only (Class A already aliased).
`#135` mega ETF densify merged first (`11ef78b`). Expected unique-ticker lift
**~540** (Nuveen ~517 new + Franklin ~24 new CEFs). Years: Nuveen 2025 estimates;
Franklin 2025 CEF calendar YE (not a 5y unlock).
**Manual Deploy:** leave `SEED_FORCE_FULL` **off**. Smoke after seed: `GET /funds?q=TIIRX` / `NSBAX` / `EMO`.

**Wave 10 densify toward 10k (Fidelity Advisor share-class + Schwab Fundamental ETFs):** Official books only — never invented. Stacks on merged Wave 9 (`#137`). Retail Fidelity DPL6 stays the FBGRX / FCNTX book. **Fidelity Advisor** is a separate official Institutional DPL (`FIIS_SP52_DPL2_DSC1` estimates + `FIIS_SP10_DPL2_DSC1` prior-year paid) and needs the A/C/M/I/Z `shareClassId=1SC3SC10SC9SC50805SC50405SC50855SC` filter — default DPL2 without it is Class I-heavy. 2025 paid book is **799** new tickers (0 overlap with retail DPL6): FAGAX / FAGCX Growth Opp Dec LT **$8.58500**; FTRIX Mega Cap Stock Dec LT **$0.27700**; FCIGX Small Cap Growth Dec LT **$0.77100**. 2026 Advisor estimate sleeve is seasonal upcoming only (FCIGX ST $0.355 / LT $6.922 / 17.30% of NAV as of 2026-07-31). Family unique tickers **~395 → ~1,194**. **Schwab** product pages add FNDX / FNDE December YE 2021–2025 (FNDX 2025 $0.1222; FNDE 2025 $1.2986) and FNDA December YE 2021–2024 (2024 $0.1643); FNDA 2025 December is not on the official product page — unmatched, not invented. Official $0.0000 ST/LT stored. Categories added for FAGAX / FAGCX / FTRIX / FCIGX / FNDX / FNDE / FNDA. **Manual Deploy:** leave `SEED_FORCE_FULL` **off** — warm disk densifies changed `fidelity` / `schwab` fixture fingerprints only. Smoke after seed: `GET /funds?q=FAGAX` / `FTRIX` / `FCIGX` / `FNDX` / `FNDE` / `FNDA`.

**Wave 11 densify toward 10k (Columbia full share-class YE + First Trust December books):** Official stamped PDFs only — never invented. Stacks on merged Wave 10 (`#138`). No new adapter (114 families stay registered). **Columbia Threadneedle** 2024–2025 December YE PDFs expand from Class A–only (~40 tickers) to the full printed share-class book (A/Advisor/C/Institutional/Institutional 2/Institutional 3/R/S): 2025 **228** tickers (LBSAX / GSFTX / CDDRX Dec LT **$1.33133**; CBLAX ST **$0.38493** / LT **$2.11142**; LEGAX ST **$0.23481** / LT **$6.79982**; ELGAX ST **$0.02832** / LT **$0.87597**; LCCAX ST **$0.19063** / LT **$2.53637**); 2024 **203** tickers (LBSAX LT **$1.38581**; LEGAX LT **$4.05105**; ELGAX LT **$0.72066**). June midyear skipped; published $0.00 December rows omitted; incomplete wraps dropped. Expected unique-ticker lift **~190** Columbia share classes. **First Trust** official December family declarations add YE depth plus a few names absent from the Sep 2025 146-ETF book: 12/11/2025 (152 paired of 156 printed; FVD **$0.3186**; FTHI **$0.1770**; FTCB income **$0.0950** / ST **$0.0318** / LT **$0.0473**; WCME **$0.0142**) and 12/12/2024 (147 paired of 159 printed; FVD **$0.2752**; FTHI **$0.1720**). Wrapped unpaired rows omitted, not invented. Years: Columbia Dec 2024–2025 (+ existing 2022 Class A); First Trust Dec 2024–2025 (+ existing Sep 2025 / 19(a)). Categories copied from Class A / conservative name rules for Dividend Income, Balanced, Cornerstone Growth, Select Large Cap Growth, Contrarian Core share classes. **Skipped (still blocked):** GSAM advisor 403 / public 1099-character % RoC; PIMCO 1099 character (no ST/LT $/share); PGIM AEM viewer/attestation; Allspring family PDFs login-gated / product pages JS-injected; Lord Abbett paying-fund family PDF missing (product SPA); Baron tax center is calendar-only (new family would break the 114-family lock); MSIM 2024 open-end PDF Akamai 403 (2025 sibling is ETF-only); Franklin/Putnam open-end JS SPA; American Funds family tables still name-only; Invesco 2021–22 ICI 406; Eaton Vance open-end ST/LT book still missing. **Manual Deploy:** leave `SEED_FORCE_FULL` **off** — warm disk densifies changed `columbia_threadneedle` / `first_trust` fixture fingerprints only. Smoke after seed: `GET /funds?q=GSFTX` / `CDDRX` / `CBLAX` / `WCME` / `FTCB`.

**Wave 12 densify toward 10k (Principal / Allspring / Hartford product-page share classes):** Official issuer product pages only — never invented. Stacks on merged Wave 11 (`#139`). No new adapter (114 families stay registered). Does not retouch `#135` mega ETFs, `#137` Nuveen/Franklin CEF, `#138` Fidelity Advisor + Schwab FND*, or `#139` Columbia + First Trust. **Principal** public `principalam.com/us/fund/<ticker>` December YE CG books expand 4 → **~86** unique tickers (2025 **79** / 2024 **79** / 2023 **48**): PQIAX ST **$0.1254** / LT **$3.3687**; PEMGX LT **$2.4892**; PBLCX LT **$8.3248**; PLGIX ST **$0.3345** / LT **$1.9823**; LTSTX ST **$0.0449** / LT **$0.9348**. Family GetFile estimate stays a viewer shell. **Allspring** ticker-keyed Class A / C / extra Institutional product pages add **~32** 2025 YE names on top of WFMIX / SGRNX / EIVIX / EGOIX / ESPNX / EMGNX (WFPAX LT **$4.26857**; SGRAX LT **$8.85612**; WOFNX ST **$0.40163** / LT **$4.06281**; years 2021–2025). Family CG PDFs stay login-gated. **Hartford** share-class product pages (`/funds/{slug}.class{N}.html`) add **~186** ticker-keyed 2025 YE I/C/F/R/Y classes (HDGIX LT **$3.9283**; HFMIX LT **$5.4448**; HGIIX LT **$6.1237**). Class A stays on the fund-level PDF / alias map (IHGIX / HAIAX / HFMCX and name-keyed ITHAX / HQIAX) so upsert keys are not forked. Official printed $0.0000 ST stored when paired with a printed LT. Expected unique-ticker lift **~300** (fixture unique **7,322 → 7,622**; Principal ~+82 + Allspring ~+32 + Hartford ~+186). Years: Principal 2023–2025; Allspring 2021–2025; Hartford 2025 product-page classes (+ existing 2024–2025 PDF). **Skipped:** T. Rowe all-class PDF already dense (variable QA* omitted); American Funds YE still name-only; Invesco ETF ICI/19a 406 this session; Hartford ETF estimate is a no-pay list; JH/MFS nameless rows stay alias-mapped (no upsert-key fork); Eaton Vance family 19(b) 403; MSIM open-end 403; PIMCO / GSAM / Allspring family PDF gated or missing ST/LT; Amundi skipped. `SEED_FORCE_FULL` **off**. **Manual Deploy:** do not. Smoke after seed: `GET /funds?q=PLGIX` / `LTSTX` / `WFPAX` / `HDGIX` / `HFMIX`.

**Wave 13 densify toward 10k (MFS I/R6/C paid YE + T. Rowe ETF YE):** Official books only — never invented. Stacks on merged Wave 12 (`#140` Principal / Allspring / Hartford) — those families were not retouched. No new adapter (114 families stay registered). **MFS** official 10-year Excel + product-page share-class tickers add Class **I / R6 / C** December paid YE **2021–2025** (~232 new 2025 tickers; Class A stays on the existing book — MIGHX / MFEGX / MEIAX not re-emitted). Heroes: MGTIX 2025 income **$0.30697** / LT **$4.20618**; MFEIX 2025 LT **$25.35332**; MEIIX 2025 LT **$3.86919**. Massachusetts Investors Growth R3 ticker MIGHX equals Class A — skipped. Published $0.00000 omitted. **T. Rowe Price** official ETF YE HTML (`…/etfs/{year}-year-end-distributions.html`) 2023–2025: 25 / 14 / 9 paying tickers; ~17 new vs the mutual-fund book (TCAF / TCAL / TVAL / THEQ / TMSL / TOUS / TGRT / TFNS / TMED / TAXE / TIER / TGLB / TURF / TMNL / TMSF / TMNS). All-dash TACN / TACU / TCHP / TTEQ / 2025 TGRW omitted. Heroes: TCAF 2025 income **$0.1916**; THEQ 2025 income **$0.1437** / ST **$0.0548** / LT **$0.0237**; TVAL 2025 income **$0.4061**. Expected unique-ticker lift **~250–300** on top of Wave 12 (MFS I/R6/C ~232 + TRP ETF ~17 + MFS B/R1–R4 estimate aliases ~54; fixture unique **7,622 → ~7,870–7,920**). Years: MFS I/R6/C 2021–2025; T. Rowe ETF 2023–2025. **Skipped:** Dimensional 2025 ETF tax sheet is CUSIP-keyed NII already in the estimate book (no new tickers); Janus monthly/quarterly/final PDFs 0 new vs ICI 2021–2025; John Hancock 403; WisdomTree Nov/Sep income PDFs no stable new tickers; VanEck 2022 sibling URLs HTML not PDF; Invesco 2021–22 ICI 406; T. Rowe variable QA* not on public ticker YE HTML; American Funds YE still name-only / F2 product pages Next.js SPA; Eaton Vance / MSIM 403; Lord Abbett paying-fund PDF 404 / hub JS SPA; #135 mega ETFs / #137 Nuveen/Franklin CEF / #138 Fidelity Advisor + Schwab FND* / #139 Columbia + First Trust / #140 Principal/Allspring/Hartford not retouched. **Manual Deploy:** leave `SEED_FORCE_FULL` **off**. Smoke after seed: `GET /funds?q=MGTIX` / `MFEIX` / `MEIIX` / `TCAF` / `THEQ` / `TVAL`.

**Wave 14 densify toward 10k (American Funds share-class product pages):** Official Capital Group product-page `historicalDistributions` JSON only — never invented. Stacks on merged Wave 13 (`#141` MFS I/R6/C + T. Rowe ETFs) — those families were **not** retouched. No new adapter (114 families stay registered). Does not retouch `#135` mega ETFs, `#137` Nuveen/Franklin CEF, `#138` Fidelity Advisor + Schwab FND*, `#139` Columbia + First Trust, `#140` Principal/Allspring/Hartford, or `#141` MFS / TRP ETFs. **American Funds** Class A YE tables stay name-keyed (AMCPX / ABALX / AGTHX). Sibling C / F-1 / F-2 / F-3 / R-1–R-6 / 529 classes are ticker-keyed from each official `https://www.capitalgroup.com/individual/investments/fund/{TICKER}` page (**917** new tickers; 2021–2025 December YE). Heroes: AMCFX 2025 LT **$2.1509** / 2024 income **$0.2434** / LT **$2.5220**; AMPCX 2025 LT **$2.1509**; FMACX 2024 income **$0.2835** / LT **$2.5220**; RAFGX 2024 income **$0.2833** / LT **$2.5220**; GFAFX 2025 income **$0.1920** / LT **$8.3640**; AMBFX 2025 income **$0.1310** / LT **$2.1250**. Per-class ordinary income is taken from that class page (not copied from Class A). Published $0.0000 omitted. Expected unique-ticker lift **~917** on top of Wave 13 (live ~8,001 after Wave 12 + Wave 13 ~250–300 → ~8,251–8,301; after Wave 14 **~9,168–9,218**). **Skipped (still blocked):** Dimensional 2025 ETF tax sheet is CUSIP-keyed / not column-safe here; Janus ICI already dense; John Hancock live site 403 (Wayback 2025 PDF is the existing Class A book); WisdomTree / VanEck already dense; Invesco 2021–22 ICI 406 / QQQM 406; Eaton Vance / MSIM 403; Lord Abbett paying-fund PDF still missing (hub is JS); Amundi/Pioneer already included. Optional `has_estimate` / `coverage_status` for unpaid prelims (FBGRX ex 2026-09-11; Nuveen 2025 past-season) left as-is — flag is future-window only; no schema change. **Manual Deploy:** do not. `SEED_FORCE_FULL` **off**. Smoke after seed: `GET /funds?q=AMCFX` / `AMPCX` / `GFAFX` / `AMBFX` / `RAFGX`.

**Wave 21 (name-only ticker maps + three pillars):** Fixture unique tickers **4,359 → 4,432**; funds **4,706 → 4,706** (44.3% of the 10,000 aspiration; +73 tickers / +0 funds; Amundi / Pioneer excluded). Official ticker maps only — never invented amounts. Harvestable public books among registered families remain thin; this wave attached issuer-printed identifiers to already-transcribed name-only remainder rows. **GuideStone** Investor tickers from official product pages / SAI (GGEZX LT $3.279591; GMZXX ST $0.000031) → **21** tickers. **Diamond Hill** remaining Investor tickers from diamond-hill.com (DHMAX LT $1.590; DHTAX LT $1.838; DIAMX LT $0.019; DHIAX LT $0.233) → **7** tickers. **Baillie Gifford** Institutional tickers from the official prospectus (BGCSX LT $1.6704; BINSX LT $1.3236) → **5** tickers. **Brandes** Class I from brandes.com (BISMX ST $0.16 / income $0.28; BEMIX income $0.06) → **5** tickers. **FAM** official fenimoreasset.com Small Cap Investor FAMFX / Institutional FAMDX (LT $0.773); prior FAMDX-on-Investor assignment corrected. **Driehaus** full official ticker book (DVSMX / DNSMX / DSMDX / DRIOX / DIDEX / DREGX / DIEMX / DRESX / DEVDX) → **11** tickers. **Touchstone** additional Class A from official westernsouthern.com/touchstone product pages (TGVFX / TEGAX / TSNAX / SAGWX) → **14** tickers; Dividend Equity / International Value / Large Cap Focused / Large Company Growth still name-only. **Buffalo** remaining Investor tickers from official SAI / product pages (BUFOX / BUFBX / BUFDX / BUFIX / BUFMX) → **8** tickers. **Manning & Napier** CUSIP/class rows mapped from official am.manning-napier.com/products/mutual-funds (RAIIX LT $0.10760; MNHAX; MNBIX; MNMIX) → **36** tickers. No new adapter: Baron tax center is still a calendar only; Neuberger / PGIM stay skipped (no scrapeable family ST/LT book). Already-deferred 403/SPA left as-is: Nationwide, Gabelli, Homestead, Boston Trust, Ariel, Hotchkis, Champlain, FMI, Impax, Locorr, Conestoga, Jensen, Causeway, plus top-40 SSGA Angular / GSAM 403 / PIMCO no ST/LT PDF / Franklin SPA / Eaton Vance open-end missing / UBS 403. Amundi skipped. Weekly estimate hubs already live for ranks 1–110 (empty/403/PDF-bytes = no-op success). Growth of $X added from Yahoo monthly adj close for GGEZX, DHLAX, BGAKX, BGVIX, FAMVX, DMCRX.

**Wave 15 (launch-bar pillar quality, ranks 56–62):** Live DB already clears the **1,000+** ticker launch bar (~3,400+ distinct). This wave densifies **existing heroes** (performance + multi-year YE + estimate hub) instead of adding thin single-row tickers. Official books only: AQR 2024 **final Class I** (AQGIX ST $0.6140 / LT $0.5462 / 11.68% of NAV; AUEIX ST $0.1898 / LT $4.3691 / 18.93% of NAV; printed dashes omitted; N/R6 clones not added); Causeway 2024 **final Inst+Inv** (CIVIX ST $0.1324 / LT $1.1868; CEMIX published $0.0000 stored); Matthews Asia official product-page paid history **2021–2024** for MEGMX / MAPTX / MINDX only (MAPTX 2024 income $0.58609 / LT $0.99319 / 8.0% of NAV; MINDX 2024 ST $1.41120 / LT $2.39476 / 12.7% of NAV); Bridgeway 2024 estimate (BRAGX LT $2.54426; BRUSX ST $1.13357; BRGOX NII-expected with no amount omitted). Alger `Distrib_FUNDS_2024.pdf` 404, Harding Loevner 2024 siblings 404, TCW unversioned final PDF is the 2025 book — no invented 2024 rows. Weekly estimate hubs now live for AQR, Causeway, Alger, Harding Loevner, Matthews Asia, TCW, and Bridgeway. Growth of $X fixtures added from Yahoo monthly adj close for AQGIX, CIVIX, CHUSX, HLMNX, MAPTX, TGDIX (BRAGX Yahoo adj-close empty — omitted). Website Submit-ticker aliases: `POST /request/ticker` (201 queued / 200 already_covered / 422 invalid) and `GET /request/ticker?status=queued`.

| Family | Estimate feed? | Status | Multi-year history? | Performance? |
| --- | --- | --- | --- | --- |
| BlackRock / iShares | Yes (live iShares CG HTML) | prelim_updated | 2021–2026 | MDDVX, AGG |
| Vanguard | Yes (tax-center + YE SPA) | paid_history_only | 2021–2025 | VFIAX, VTIAX, VIGAX, VBIAX, VXUS |
| Fidelity | Yes (live FIIS_SP52_DPL6 + Advisor DPL2 A/C/M/I/Z) | prelim_updated | 2021, 2024–2026 + Advisor 2025 | FBGRX, FAGAX |
| State Street / SPDR | Yes (Angular ETF + MF hubs) | deferred | 2021–2025 | SPY, ALLW |
| J.P. Morgan | Yes (19a PDF walked) | prelim_updated | 2024–2025 | — |
| Goldman Sachs | Yes (advisor tax-center, 403) | deferred | 2025 sample | — |
| American Funds | Yes (tax-center + midyear/YE) | prelim_updated | 2021–2026 | AGTHX, AMCPX, ABALX |
| PIMCO | Yes (tax-center walked) | deferred | sample only | — |
| Invesco | Yes (tax guide + 2025 PDF) | prelim_updated | 2021–2025 | — |
| T. Rowe Price | Yes (distributions hub + YE HTML + ETF YE) | prelim_updated | 2021–2025 | TRBCX, TCAF |
| UBS | Yes (products hub) | prelim_updated | 2025 | — |
| Franklin Templeton | Yes (SPA estimate hub) | deferred | 2024–2025 19(a) + DIST-SUMM 2025 CEF | — |
| BNY Mellon | Yes (2025 estimate PDF) | prelim_updated | 2022–2025 | — |
| Nuveen | Yes (document viewer) | prelim_updated | 2025 | — |
| Northern Trust | Yes (2025 CG PDF) | prelim_updated | 2021–2025 | NOSIX |
| Morgan Stanley | Yes (tax forms hub) | paid_history_only | 2024–2025 | — |
| Schwab | Yes (family SPA + Bynder PDF) | paid_history_only | 2021–2025 | SWTSX, SWANX |
| Dimensional | Yes (2025 estimate PDF) | prelim_updated | 2024–2025 | — |
| Columbia Threadneedle | Yes (midyear PDF) | prelim_updated | 2022, 2024–2025 | LBSAX, GSFTX |
| Amundi / Pioneer | Yes (Pioneer / Amundi / Victory hubs + 2025 estimate/final PDFs) | prelim_updated | 2023–2025 | PIODX, PIGFX |
| Allspring | Yes (product-alerts hub) | paid_history_only | 2021–2025 | — |
| Janus Henderson | Yes (2025 estimate PDF) | prelim_updated | 2021–2025 | JDCAX |
| American Century | Yes (HTML hub + retail PDF) | prelim_updated | 2022–2023, 2025 | — |
| Dodge & Cox | Yes (Q1 2026 estimate PDF) | prelim_updated | 2021–2026 | DODIX, DODGX |
| MFS | Yes (mfs_cg_fly PDF) | prelim_updated | 2021–2026 | MIGHX, MGTIX, MFEIX |
| Lord Abbett | Yes (HTML hub + no-pay PDF) | prelim_updated | 2025 | — |
| AllianceBernstein | Yes (2025 GEN-5796 PDF) | prelim_updated | 2023, 2025 | — |
| Federated Hermes | Yes (preliminary.do SPA) | prelim_updated | 2025 full prelim PDF | — |
| Virtus | Yes (June 2026 estimate PDF) | prelim_updated | 2024–2026 | — |
| Eaton Vance | Yes (tax-center + 19b) | deferred | 2025 | — |
| John Hancock | Yes (2025 estimate PDF) | prelim_updated | 2022–2025 | — |
| Principal | Yes (tax-center hub) | paid_history_only | 2023–2025 | — |
| Thrivent | Yes (capital-gains HTML) | paid_history_only | 2024–2025 | — |
| Hartford | Yes (2025 estimate PDF) | prelim_updated | 2024–2025 | — |
| Macquarie | Yes (CGE-RET PDF) | prelim_updated | 2023–2025 | — |
| First Eagle | Yes (2025 estimate PDF) | prelim_updated | 2023–2025 | SGENX, FEVAX, FEGE, FEOE, FEFAX |
| GMO | Yes (July 2026 Trust PDF) | prelim_updated | 2025–2026 | — |
| Artisan | Yes (tax-center YTD HTML) | paid_history_only | 2024–2026 | — |
| Calamos | Yes (2025 estimate PDF) | prelim_updated | 2024–2025 | — |
| Wasatch | Yes (2025 estimate PDF) | prelim_updated | 2022, 2024–2025 | — |

**Year-depth before → after (fixture ingest; calendar year on `as_of` or `ex_date`; ranks 1–40 movers):**

| Family | Before (tickers / year) | After |
| --- | --- | --- |
| Dimensional | 2024:3 / 2025:140 | **2024:138** / 2025:140 |
| Macquarie | 2023:20 / 2024:3 / 2025:21 | 2023:20 / **2024:16** / 2025:21 |
| Hartford | 2024:3 / 2025:25 | **2024:14** / 2025:25 |
| AllianceBernstein | 2023:3 / 2025:19 | **2023:15** / 2025:19 |
| Northern Trust | 2021:19 / 2022:16 / 2023:10 / 2024:15 / 2025:22 | unchanged this wave |
| Schwab | 2021:2 / 2022–2024:2 / 2025:4 | **2021:5 / 2022–2024:5 / 2025:79** |
| State Street / SPDR | 2025 estimate:3 | **2021:127 / 2022:127 / 2023:128 / 2024:150 / 2025:168** + estimate sample |
| Franklin Templeton | 2024–2025:1 (FT) | **2025:~32** (19a FT / FTF / TEI / SMDLX + DIST-SUMM 28 CEFs) |
| Fidelity | 2024:350 / 2025:349 / 2026:15 | **2021:204** (DPL6 through FIMIX) / **2022–2023:1** (FCNTX highlights only) / 2024:350 / 2025:349 + **Advisor 2025:799** / 2026:15 + Advisor seasonal estimates |

**Advisor-visible N/A gaps (smoke heroes; YoY `matched=false`, totals null — not invented $0):**

| Hero | Years present | Advisor-visible N/A | Why |
| --- | --- | --- | --- |
| VFIAX / VBIAX / VIGAX | 2021–2025 | none in 2021–2025 | ICI December + YE HTML |
| TRBCX | 2021–2025 | none in 2021–2025 | YE HTML + 2021–2022 PDFs |
| DODIX | 2021–2025 | none in 2021–2025 | Tax letter + product API |
| FBGRX | 2021, 2024–2026 | **2022–2023** | 2021 DPL6 official; 2022–2023 DPL6 not in CDX (HPDY SPA) — not invented |
| FCNTX | **2021–2025** | none in 2021–2025 | 2021 DPL6 ST/LT; 2022–2023 prospectus highlights (OI + total CG, no ST/LT); 2024–2025 DPL6 ST/LT |
| AMCPX / AGTHX | 2021–2025 (name-keyed) | ticker-only score looks empty | Aliases still resolve AMCAP / Growth Fund of America |
| CGHM | 2026 midyear only | **2021–2025** | Inception 6/25/24; official 2024–2025 YE em-dash (no CG — not stored as $0) |

| Rank | Family | Before (tickers / funds) | After | Book used | Full-book vs flagship history |
| --- | --- | --- | --- | --- | --- |
| 1 | BlackRock / iShares | 12 / 12 | **44 / 121** | iShares ETF CG HTML + BlackRock 2025 open-end MF book | 44 ETF payers + 77 OEF funds (Investor A when listed). SMAs skipped. |
| 2 | Vanguard | 26 / 26 | **297 / 297** | Column-safe full ICI December 2021–2025 (31-token layout) | **2021–2025 full December.** Wrap/DAILY rows omitted. 2025 omits VFIAX/VBIAX/VIGAX (YE HTML). YE page is SPA. |
| 3 | Fidelity | 15 / 15 | **350 / 350** | Live prior-year paid table `FIIS_SP10_DPL6` + estimate `FIIS_SP52_DPL6` | Estimate table is still “funds expecting CG” (15). Prior-year paid is the full book. |
| 5 | J.P. Morgan | 2 / 2 | 2 / **38** | Full 2025 + official 2024 Section 19a Appendix A | Notices are unsplit CG $/share except MMKT LT. SEEGX / JLGMX keep the Large Cap Growth LT mapping ($9.32525 / $0.79868). |
| 7 | American Funds | 3 / 46 | **22 / 84** | Live 2025 YE HTML | 2025 YE is the public table. 2024 YE + estimate samples unchanged (name-heavy). |
| 9 | Invesco | 2 / 5 | **11 / 53** | Full 2025 MF estimate PDF + full 20 Nov 2025 ETF press-release table | SMA High Yield Bond skipped. PDF has no MF tickers. 2024 estimate still thin. |
| 10 | T. Rowe Price | 18 / 18 | **232 / 232** + Wave 13 ETF YE | Live 2023–2025 YE HTML + ETF YE | **2023–2025 full MF book** + Wave 13 ETF YE HTML (TCAF / THEQ / TVAL). 2022 YE + prelim remain PDF flagship transcriptions. |
| 13 | BNY Mellon | 3 / 3 | 2 / **42** | Full 2025 MF paying-fund PDF + 12-ETF $0.00 book | Tickers only for DGAGX / PEOPX. Paid YE product pages still flagship. ETF PDF prints published $0.00 (stored). |
| 15 | Northern Trust | 5 / 5 | **22 / 22** | 2025 equity CG PDF + ICI Dec income-only | NOMIX / NSGRX / NSCKX recovered. ICI totals stored as income only when CG book is em-dash. FI daily lines omitted. |
| 18 | Dimensional | 3 / 3 | **140 / 140** | Full 2025 CG PDF + **full 2024 paid December PDF** (published $0.000 kept) | **2024–2025 full-book.** DISVX 2024 LT $0.184. `.../2021-2023-distributions.pdf` aliases serve the 2024 file. |
| 20 | Amundi / Pioneer | 4 / 4 | **64 / 64** | Official 2025 estimate + 2025 finals + 2023–2024 YE | Included per Eric 2026-09-08. Interval XILSX omitted. |
| 22 | Janus Henderson | 3 / 3 | **222 / 222** + **149–191 ICI tickers / year** | **2021–2025 ICI Primary paid YE** (full share-class) + 2025 final estimate PDF | ICI is the paid book (JDCAX LT $4.95363 / $0.02107 / $3.88875 / $5.46939 / $6.96694). Forty Fund is on 2021 ICI (absent from the 2021 FINAL PDF). 2023–2024 estimate PDFs still A-share flagships. |
| 23 | American Century | 3 / 3 | **389 / 389** + **350 / 350 (2023)** + **266 / 266 (2022)** | Full 2025 + 2023 Wayback + official 2022 retail estimate PDFs | Paid TWCGX product page still flagship. 2022 TWCGX LT $0.7247. 2024 unversioned PDF is the 2025 book. 2021 sibling 404. |
| 27 | AllianceBernstein | 3 / 3 | 3 / **19** | Full 2025 paying-fund estimate + **2023 full Wayback GEN–5796–1023** | Class A tickers only for AGRFX / APGAX / ABASX. AGRFX 2023 LT $6.95. 2024 overwritten. |
| 29 | Virtus | 3 / 3 | 3 / **4** | Full listed June 2026 estimate PDF (4 funds) | 2025 paid / 2024 19(a) still flagship. |
| 41 | Harbor | 3 / 3 | 3 / **9** | 2025 estimate PDF Institutional rows | Tickers only where already identified (HACAX / HASCX / HAIDX). |
| 43 | Voya | 3 / 3 | 3 / **17** | 2025 estimate PDF paying funds | Class A tickers only for NLCAX / VYCAX / NMCAX; other rows are PDF names. |
| 51 | SEI | 0 / 3 | 1 / **51** | Full 2025 paying-fund estimate PDF | Fund-level (QALT ticker when printed). All-dash rows omitted. |
| 52 | Brown Advisory | 4 / 4 | 4 / **17** | Full 2025 Inst/Inv/Adv estimate PDF | Tickers only for BAFFX / BAFGX / BAFWX / BVALX. All-dash funds omitted. |
| 54 | VanEck | 3 / 3 | **71 / 71** | 2025 MF/ETF estimate + **2023–2025 paid ETF/MF YE** | Printed `None` omitted. GDX 2023 $0.5001 / 2024 $0.4025 / 2025 $0.6331. INIVX 2023 $0.0102 / 2025 paid $1.5675. |
| 55 | WisdomTree | 4 / 4 | **85 / 85** | 2025 + 2024 final CG payers + **Dec 2025 family income declaration** | Dashed no-CG omitted. DGRW income $0.23270. Published $0.00000 income stored. |
| 111 | First Trust | 0 / 0 | **150+ / 150+** | 19(a) + Sep 2025 146-ETF + **Dec 2025 / Dec 2024 family declarations** | FVD Dec 2025 $0.3186; FTHI $0.1770; FTCB LT $0.0473. Wrapped unpaired omitted. |
| 114 | ARK Invest | 0 / 0 | **7 / 7** | Official 2021 FINAL CG handout | ARKK ST $0.5249 / LT $0.2577. 2022 official no-distribution letter not stored as invented $0. |
| 56 | AQR | 4 / 4 | **75 / 75** | Full 2025 I/N/R6 estimate PDF | Diversifying Strategies uses the later 12/19–12/23 dates. |
| 57 | Causeway | 3 / 3 | **10 / 10** | Full 2025 Institutional + Investor final PDF | — |
| 58 | Alger | 3 / 3 | **84 / 84** | Full 2025 share-class PDF | International Small Cap ALCZX collision omitted. Published $0.00 stored. |
| 16 | Morgan Stanley | 3 / 3 | **16 / 16** | Full listed 2025 ETF YE income table | CG columns were em-dash / 0.00% (omitted as $0 CG). Open-end YE PDF still Akamai-blocked. |
| 31 | John Hancock | 3 / 3 | 3 / **56** | Full 2025 CG + income-only MF/ETF rows from the same PDF | Closed-end rows skipped. All-dash omitted. 2022–2024 still A-share flagships. |
| 34 | Hartford | 3 / 3 | 3 / **25** | Full 2025 paying-fund estimate + equity/FI finals + **2024 full equity final** | No-pay list omitted. Tickers only for HFMCX / HAIAX / IHGIX. HFMCX 2024 LT $1.67. |
| 35 | Macquarie | 3 / 3 | **21 / 21** | Full 2025 paying-fund estimate + **2023–2024 full paid Class A books** | No-pay list omitted. 2024 WSTAX ST $1.108 / LT $8.135 (16 Class A). |
| 33 | Thrivent | 3 / 3 | 3 / **13** | 2025 + **2024 Wayback** paying-fund HTML | Tickers only for TMSIX / IILGX / THLCX. TMSIX 2024 LT $1.33794. |
| 36 | First Eagle | 3 / 3 | **40 / 40** | 2025 open-end estimate + full 2024 share-class paid PDF | Class A tickers from official 2024 PDF. Interval/CEF omitted. Footnote-b income omitted. |
| 37 | GMO | 3 / 3 | 3 / **29** + **9 ETF tickers** | July 2026 Trust estimate + **2025 ETF Trust YE 1099-DIV** | Published $0.000 stored. BCHI/INVG ST stored; Box 2a LT $0 omitted. |
| 38 | Artisan | 2 / 2 | **51 / 51** | Column-safe 2024–2025 Year-End Tax Reporting ICI PDFs | December income + any-month ST/LT. 2024 LT at token 11. 2021–2023 ICI public but transposed (not column-safe). YTD HTML keeps ARTKX 2026 income. |
| 39 | Calamos | 3 / 3 | 3 / **13** | Full 2025 paying-fund estimate PDF | All-dash omitted. Class A tickers only where previously identified. |
| 40 | Wasatch | 3 / 3 | 3 / **13** | Full 2025 listed-fund estimate PDF | Investor tickers only for WGROX / WAIGX / WMCVX. |

**Still thin (public book not column-safe / SPA / 403):** Goldman / PIMCO (samples; GSAM 403; PIMCO 1099-character / SAI, no open-end ST/LT PDF), UBS (403 / unparseable price page), Franklin **open-end** estimate grid (SPA; CEF 19a + DIST-SUMM 2025 calendar harvested — ~32 CEF tickers), Dodge (Q1 2026 PDF is 2 funds; December tax-letter URL returned the foreign-source booklet), Nuveen **cleared** the 50-fund bar (full 2025 estimate book ~521 tickers; live viewer still JS — fixture fallback), Columbia 2025 mid-year all-funds PDF (wrap-unsafe), William Blair 2025 PDF (text extract reverses columns). MFS 2025 fly PDF is the full %NAV book (name-keyed; official Class A tickers where product pages identify them). State Street estimate page is still Angular (paid XLSX harvested). Schwab family SPA is still JS (2025 PDF harvested).

**Large families still under 50 MF/ETF funds, and why**

| Rank | Family | Funds now | Why under 50 |
| --- | --- | --- | --- |
| 4 | State Street / SPDR | **170** | **Cleared.** Official XLSX paid YE 2021–2025. Estimate page still Angular. |
| 5 | J.P. Morgan | 38 | Full 2025 19a Appendix A exhausted (open-end + ETF + 4 MMKT LT). No broader YE HTML |
| 6 | Goldman Sachs | 2 | Advisor tax center 403; sample only |
| 8 | PIMCO | 2 | No public HTML estimate grid; `ZZ*` sample |
| 11 | UBS | 4 | Estimate PDF 403 / rotating JCR; price page unparseable |
| 12 | Franklin Templeton | **~32** | **CEF DIST-SUMM 2025 + 19(a) harvested.** Open-end estimate grid is still SPA; FKINX / PEYAX unmatched. |
| 13 | BNY Mellon | 42 | Full 2025 MF paying-fund PDF (30) + ETF $0.00 book (12) exhausted |
| 14 | Nuveen | **~521** | **Cleared.** Full 2025 mutual-fund estimate book (download=1). SMA / Managed Account omitted. |
| 15 | Northern Trust | 22 | Equity CG + ICI income-only exhausted; FI is daily/monthly (not stored as YE income) |
| 16 | Morgan Stanley | 16 | 2025 ETF YE income table exhausted; open-end YE PDF Akamai-blocked |
| 17 | Schwab | **79** | **Cleared.** Official 2025 annual PDF + 2021–2024 ≥$1B product pages. Family SPA still JS. |
| 19 | Columbia Threadneedle | 4 | 2025 mid-year all-funds PDF wrap-unsafe |
| 20 | Amundi / Pioneer | 4 | **Skipped** (non-US parent) |
| 21 | Allspring | 2 | Family estimate PDFs gated |
| 24 | Dodge & Cox | 4 | Public Q1/tax-letter books are small; no full YE CG grid |
| 26 | Lord Abbett | 3 | Public PDF is $0 no-pay list only |
| 27 | AllianceBernstein | 19 | Full 2025 paying-fund PDF exhausted (19 listed) |
| 28 | Federated Hermes | 87 | Official 2025 prelim PDF (50135); tax-center JS |
| 29 | Virtus | 4 | June 2026 estimate PDF lists 4 funds |
| 30 | Eaton Vance | 1 | CEF 19(b) sample; open-end on MSIM |

**Cleared the 50-fund bar:** BlackRock / iShares (121), Vanguard (**297**), Fidelity (350), State Street / SPDR (**170**), American Funds (84), Invesco (53), T. Rowe (232), Schwab (**79**), DFA (140), Janus (222), American Century (389), MFS (**175**), John Hancock (**56**), Artisan (**51**), **Nuveen (~521)**. Closest remaining large-family public books: BNY (42), JPM (38).

**Large families still under 50 MF/ETF tickers (name-heavy books or gated):** BlackRock 44 (OEF book has no ticker column), American Funds 22, Invesco 11, plus every under-50-fund family above. Official books are fund-level — tickers were not invented.

**Ranks 31–40 still under 50 (public book lists fewer than 50, or gated):** Principal 2 (GetFile cover only; 2023–2025 product-page paid YE), Thrivent 13 (full paying HTML), Hartford **25** (full 2025 paying PDF + 2024 full equity final), Macquarie **26** (2025 Class A paying PDF + 2023–2024 CGE-RET-ACT full paying books), First Eagle **40** (full 2024 share-class paid + 2025 estimate; book lists ~13 strategies / 40 classes, not 50+), GMO 29 (full Trust PDF), Calamos 13, Wasatch 13.

**Handoff (ranks 1–40 only):** remaining unlocks are gated (SSGA Angular estimate page, JPM broader YE / no 2024 19a, GSAM 403, PIMCO open-end ST/LT PDF, UBS JCR 403, Franklin **open-end** SPA, Schwab family SPA, MSIM open-end PDF, Capital Group ticker column, Fidelity 2021–2023 HPDY SPA, ACI 2021/2024 PDFs, Columbia wrap-unsafe). Nuveen mutual-fund 2025 estimate book is harvested (viewer still JS — fixture fallback). Artisan 2021–2023 ICI PDFs exist but token order / Box 1a breakdown is not column-safe. MFS fly PDFs remain current-year only (10-year Excel now covers additional official Class A pages). John Hancock 2022–2024 sibling PDFs 403 from automated clients. Do not expand ranks 41–110. Amundi / Pioneer is included (Victory-hosted Pioneer tax center). SMAs stay out of the 50-fund bar.

## Multi-year history and estimate → actual

History packs focus on **US-domiciled** fund firms. Prefer US managers when choosing which gaps to fill. **Amundi / Pioneer is included** per Eric 2026-09-08 — official 2023–2025 Pioneer / Victory Portfolios IV tax-center books (US Pioneer retail transferred to Victory Capital in April 2025). Ranks 21–40 in this pass are US books (John Hancock / Manulife US Investments; Macquarie Delaware Funds US book; GMO US Trust only — skip GMO Australia).

The upsert key includes `as_of` and `ex_date`, so a September preliminary, a December update, and a January final are **separate rows**. Do not collapse them.

### Website Search: unique funds (`GET /funds`)

`GET /distributions` returns **distribution rows** (many per fund). Website Search / Sample Estimates should list **unique funds** instead:

```
GET /funds?limit=50&offset=0
GET /funds?q=AMCAP&limit=50&offset=0
GET /funds?q=ZZZZZ&limit=50&offset=0
GET /funds/lookup?ticker=AGTHX
GET /funds?fund_family=Vanguard&limit=50&offset=0
```

| Query | Default | Notes |
| --- | --- | --- |
| `limit` | 50 | Max 200 |
| `offset` | 0 | Server-side skip |
| `q` | — | Ticker / name / family / identifier (same alias rules as `/distributions`) |
| `fund_family` | — | Optional family filter |
| `category` | — | Optional Morningstar-style category (e.g. `Large Growth`). Case/hyphen insensitive. Unknown names return an empty list — never invent. |

Response: `{ "items", "limit", "offset", "total" }`. Each item is a stored fund only (never invented):

```json
{
  "ticker": "AMCPX",
  "fund_name": "AMCAP Fund",
  "fund_family": "American Funds",
  "fund_identifier": "amcap-fund",
  "category": "Large Growth",
  "latest_as_of": "2025-12-15",
  "has_estimate": true,
  "coverage_status": "estimate_announced",
  "nav_per_share": "45.700000",
  "nav_as_of": "2026-09-08",
  "nav_source": "yahoo_last_close"
}
```

`ticker` is null when the stored book is name-keyed and no Class A / Investor A alias exists. `category` is null when no trusted Morningstar-style category is known — **null > wrong**. `nav_per_share` / `nav_as_of` / `nav_source` are the latest weekly NAV print (Yahoo last regular close preferred). They stay **null** when unknown — never invented. Website Search / Sample Estimates / illustrate should read these instead of asking the advisor for NAV. `has_estimate` is true only when an unpaid `preliminary_estimate` / `updated_estimate` still has a **future** `ex_date` or `payable_date` (and no `final` / `paid` row for that fund + calendar year). Past-season prelims do not flip the flag. Ingest deletes (and will not re-seed) a past prelim once a same-fund, same-year final/paid exists — leftover past prelims with no matching final are kept and never invented into a final. `total` is the unique-fund count, not the distribution-row count.

**`coverage_status` (Eric 2026-09-10 — never conflate awaiting vs not in book; never invent estimates):**

| Value | Where | Website UI |
| --- | --- | --- |
| `awaiting_estimate` | In-book `GET /funds` item when `has_estimate=false` (no future unpaid prelim) | **Awaiting Estimate** |
| `estimate_announced` | In-book item when `has_estimate=true` (unpaid manager-published estimate) | Show the stored estimate — do not invent amounts |
| `not_in_universe` | Ticker lookup **miss only** | **Add to universe** → `POST /request/ticker` |

`GET /funds` items are always in-book, so they never return `not_in_universe`. Locked examples after fixture ingest: **AGTHX** → `awaiting_estimate`; **FBGRX** → `estimate_announced`.

**Ticker miss (not in the book):**

- `GET /funds?q=ZZZZZ` → `{ "items": [], "total": 0 }` — empty list. This is **not** Awaiting Estimate.
- `GET /funds/lookup?ticker=ZZZZZ` → **404** `{ "coverage_status": "not_in_universe", "ticker": "ZZZZZ", "message": "…", "add_to_universe": "POST /request/ticker" }`

Website **Add to universe** must `POST /request/ticker` (see **Website Submit-ticker** below). Do not invent a fund row or a distribution amount while the ticker is queued.

`GET /funds/categories` returns `{ items: [{ category, fund_count }], uncategorized, total_funds, categorized, coverage_pct }` so Website can populate a Versus Category picker and compute averages / +/- vs category from `GET /funds?category=…` (average the illustrated tax fields of funds that share `category`).

`category` is also attached on `GET /distributions` items and on illustrate / portfolio-illustrate responses wherever fund metadata already appears (`IllustrationComponent.category`, `PortfolioHoldingOut.category`). It is identity-level metadata, not a distribution amount, and is never invented. Website Paid History can filter rows with the same `category` query param (`GET /distributions?category=Large+Blend&ex_date_from=…`).

See **Fund category (Versus Category)** below for coverage and how unknowns stay null.

### Fund category (Versus Category)

Website can average illustrated tax / distribution fields by `category` and show +/- vs that category. This API persists category on **fund identity** (ticker / `fund_identifier`), not on each distribution amount.

| Source | When used |
| --- | --- |
| Curated issuer identities | Flagship / Class A maps (Capital Group, Vanguard, Dodge & Cox, iShares cores, performance heroes) from public fact-sheet Morningstar US Category |
| Conservative name rules | Unambiguous names only: S&P 500 / Russell / EAFE / target-date / explicit Large-Cap Growth / Total Bond Market / etc. |
| Yahoo `fundProfile.categoryName` | Remaining tickers, only when the published name canonicalizes to the Morningstar-style taxonomy |
| **Null** | Anything left — opaque active names, name-only remainder rows, parser samples, Yahoo miss / unpublished category |

Rebuild the catalog with `python3 scripts/build_fund_categories.py` (add `--yahoo` to refresh ticker lookups). Catalog file: `app/fund_categories.json`. This pass: **4,483 / 4,859 unique fixture funds (92.3%)** have a category; **376 stay null** (name-only remainder rows, unpublished Yahoo `fundProfile`, alt/buffer names that still do not canonicalize, parser samples). Do **not** invent a category to raise the percentage. Versus Category UI should skip nulls when averaging.

`GET /distributions` still uses `page` / `page_size` / `total`. Website may send `limit` / `offset` as aliases (`limit` → `page_size`, `offset` → `page = floor(offset / page_size) + 1`). The response keeps `page` / `page_size`.

`GET /distributions` already supports `as_of_from` / `as_of_to`, `publication_stage`, `fund_identifier` (exact slug or ticker identity), `fund_family`, and **`category`** (same Morningstar-style strings as `GET /funds` / `GET /funds/categories`). `category` is an exact match on the fund’s category (case/hyphen insensitive via `canonical_category`). Unknown names return `{ items: [], total: 0 }`. Filtered `total` includes `category` combined with the other query filters so Website Paid History can page `ex_date_from` / `ex_date_to` + `fund_family` + `category` without walking the book. Category is resolved from fund identity metadata (same source as `/funds`) — the filter does not hydrate `raw_payload` or add a schema column.

**`sort` / `order` (Website Paid History column sort):** optional. Applied **after** the filters above and **before** `limit`/`offset` so `total` is unchanged and page 1 of `sort=amount&order=desc` is the highest Dist $/Share in the filtered set (not just the current page). Aliases: `sort_by` → `sort`, `sort_dir` → `order`. Fields: `amount` (numeric Dist $/share — `amount` with `amount_unit=per_share` only; SQL NULL last; does not invent zeros), `ex_date`, `ticker`, `fund_name`, `as_of`. When `sort` is omitted, the current default order is preserved (`as_of` desc, `fund_name`, `estimate_type`) even if `order` is sent. When `sort` is set and `order` is omitted: `amount` / `ex_date` / `as_of` default to `desc`; `ticker` / `fund_name` default to `asc`. ORDER BY uses stored columns / `ix_dist_*` — not `raw_payload`.

**Compare estimate vs paid for one fund:**

1. `GET /distributions?fund_identifier=amcap-fund&publication_stage=preliminary_estimate` — % of NAV ranges (often `total_capital_gains`).
2. `GET /distributions?fund_identifier=amcap-fund&publication_stage=final` — year-end per-share LTCG/STCG.
3. `GET /distributions?fund_identifier=amcap-fund&as_of_from=2024-01-01&as_of_to=2024-12-31` — one tax year’s publication window.
4. Units differ (`percent_of_nav` vs `per_share`); convert with NAV before subtracting. Illustration uses `as_of` or `prefer_publication_stages` so you do not add estimate + final.

Fixture packs today (ranks 1–40 historical pass):

| Family | Years in fixtures | Live archive notes |
| --- | --- | --- |
| BlackRock / iShares | 2026 midyear paid + 2025 YE ETF + 2021–2025 open-end MF | Live ETF HTML https://www.ishares.com/us/capital-gains-distributions. Open-end HTML books https://www.blackrock.com/us/individual/resources/tax-information/2025-distributions (2024 / 2023 / 2022 / 2021 siblings). Live OEF pages are per-fund share-class tables — fixtures flatten November–December YE Investor A rows (Equity Dividend LT $1.089256 / $0.740291 / $0.481929 / $0.728360 / $0.999925). 2025 live flatten was not a lookback gain vs the existing Investor A book. iShares 2023–2024 tax kits remain 1099-style PDFs, not an ETF HTML CG grid. |
| Vanguard | 2021–2025 ICI **full December** + 2025 YE HTML for VFIAX / VBIAX / VIGAX | **ICI first.** Official Primary Layout PDFs. 2021–2025 December rows are column-safe full-book (31-token layout; wrap/DAILY bleed skipped). 2025 ICI skips VFIAX / VBIAX / VIGAX so the YE HTML fixture is not double-counted. |
| Fidelity | **2021 DPL6 (204 tickers) + 2022–2023 FCNTX highlights + 2024–2025 full prior-year paid** + 2026 estimate + **Advisor 2025 A/C/M/I/Z (799 tickers)** | Live HTML: current estimates `FIIS_SP52_DPL6` + Advisor `FIIS_SP52_DPL2_DSC1` (A/C/M/I/Z `shareClassId`) and prior-year `FIIS_SP10_DPL6` + Advisor `FIIS_SP10_DPL2_DSC1` (FBGRX 2025 paid LT $5.07300 ex 2025-09-12; 2026 estimate LT $21.021 as of 2026-07-31). **Record date is unpublished** on both DPL6 tables (Ex / Pay / As of only) — `record_date` stays null; not invented from ex−1. Proof: `fixtures/fidelity/RECORD_DATE.md`. **2024 is the full DPL6 book** from Wayback `20250321032441id_` (350 tickers; FBGRX Dec LT $1.66900 / Sep LT $11.08100; FCNTX Dec LT $0.85500). **2021 DPL6** is Wayback `20221209193656id_` verified rows through FIMIX (204 tickers; FCNTX Dec LT $1.62700 / Feb LT $0.40000). Later range fetches of that timestamp replay a 2024 digest — N–Z not invented. **2022–2023 DPL6 still not in CDX** (HPDY SPA). FCNTX 2022–2023 uses the official retail prospectus financial highlights (OI $0.08 / CG $1.36 and OI $0.08 / CG $0.61) as ordinary_income + total_capital_gains — ST/LT not published, not invented. No QDI % columns. |
| State Street / SPDR | **2021–2025 paid YE** (168 tickers in 2025) + 2025 estimate sample | Official XLSX `.../spdr-etf-historical-distributions.xlsx` (SPY Dec 2025 income $1.993368 / ST $0 / LT $0; ALLW ST $0.253072 / LT $0.172577). Estimate page still Angular. SPLG renamed SPYM 10/31/2025. ZZSSGA remains a parser-layout sample. |
| J.P. Morgan | 2025 Section 19a full Appendix A (open-end + ETF) | Unsplit estimated CG $/share. SEEGX / JLGMX keep Large Cap Growth LT $9.32525. No confirmed official 2024 $/share 19a. |
| Goldman Sachs | 2025 sample (GLCGX) | Advisor tax center 403-walled; no public historical HTML. |
| American Funds | **2021–2025 full public YE CG books** (tax-year as_of) + Class A product-page history (ABALX / AMCAP / GFA / ICA / WMIF / NPF / EUPAC / NWF / AMF / CIB) + 2024/2025 reprint + 2026 midyear | 2021–2024 individual YE URLs are 404; fixtures are Wayback id_ snapshots of the official tables with as_of = December ex-date (AMCAP 2021 LT $1.1710 / 2024 $2.5220 / 2025 $2.1509; no Dec 2022 AMCAP CG). ABALX official `ambal-a` JSON: Dec OI $0.1000 (2021–2023) / $0.1100 (2024–2025); Dec 2021 LT $0.8600; 2022–2023 LT published $0.0000 omitted; special $0.0850 / $0.3550. 2025 tax-year book is the public YE table (January 2026 reprint as_of unchanged). Bare QDI % omitted. **CGHM** inception 6/25/24 — no 2021–2023 rows; official 2024/2025 YE em-dash ST/LT not stored as $0. |
| PIMCO | Layout sample only (ZZPIMI / ZZPIMB) | Re-checked 2026-09-08: tax-center document is SAI/supplement; 2025 tax PDF is 1099 character. No open-end ST/LT $/share book. Not invented. |
| Invesco | **2023–2025 ICI Primary December YE** + 2024/2025 estimates | Official broker XLSX on the open-end tax guide (`2025-Primary-Broker-File-…xlsx`, `oe-2024-primary-broker-file.xlsx`, `oe-2023-primary-broker-file.xlsx` + Real Estate companions). December income / ST / LT $/share only (Daily / $0 / QDI % omitted). VAFAX Dec 2025 LT $4.0375 / 2024 LT $1.0971. SteelPath companions had no December YE $/share. 2021–2022 sibling XLSX 404 — not invented. |
| T. Rowe Price | 2021–2025 YE + 2022 prelim + Wave 13 ETF YE 2023–2025 | 2023–2025 HTML (same path, year in the filename). 2021–2022 YE PDFs are the full mutual-fund/ETF books (TRBCX LT $16.03 / $6.0394 final; 2022 prelim $5.75). Wave 13 official ETF YE HTML (`…/etfs/{year}-year-end-distributions.html`): TCAF 2025 income $0.1916; THEQ $0.1437 / ST $0.0548 / LT $0.0237; TVAL $0.4061. Em-dash / Paid monthly omitted. |
| UBS | 2025 estimate + 2025 paid (PWTAX) | No public filled ICI. Estimate PDF is rotating AEM/JCR and often 403. 2023–2024 paid archives not fetchable — skipped. |
| Franklin Templeton | 2024 + 2025 19(a) (FT / FTF / TEI / SMDLX) + **DIST-SUMM 2025 CEF calendar (~28 tickers)** | ICI hub is a JS SPA. Open-end estimate tool is SPA. DIST-SUMM: FT income $0.341 / LT $0.145 / RoC $0.024; EMO income $0.756 / RoC $3.504. December 2025 19(a): FT income $0.0358; FTF $0.0418 / RoC $0.0197; TEI ST $0.0648 / RoC $0.1846; SMDLX paid $0.149600 / RoC $0.073334. Royce CEFs stay on the Royce adapter. ≥$1B open-end (FKINX) not on a scrapeable family PDF — skipped. |
| BNY Mellon | 2022–2025 paid YE (DGAGX) + 2025 full estimate book | No public filled ICI. 2024 family estimate PDF URL was empty. 2025 estimate is every paying fund (tickers only DGAGX / PEOPX). Paid YE from the public Appreciation product page (2025 LT $6.4552 coexists with 10/31 estimate LT $6.29). |
| Nuveen | **2025 estimate full share-class book (~521 tickers)** | No public filled ICI. Viewer URL is a JS shell; `download=1` is the official PDF. TIIRX LT $1.97 / 6.49% of NAV; NSBAX ST $0.04 / LT $4.89. Manager-printed `$-` stored as $0.00. SMA / Managed Account omitted. 2024–2025 tax-character letters (QDI / US-gov %) are not ST/LT $/share — skipped. |
| Northern Trust | **2021–2025** YE (2021–2024 full equity CG + 2025 full equity CG + ICI Dec income-only) | **ICI listed.** Filled Primary Reports 2022–2025 are public PDFs. First amount is Total Distribution — CG-paying tickers not ingested as income. December ICI totals stored as ordinary income only when the CG book is em-dash. **2021** `capital-gains-2021.pdf` is the full equity CG book (NOSIX ST $0.096491 / LT $0.985777). |
| Morgan Stanley | 2024 + 2025 ETF YE (CVLC income; 0% CG) | No public filled ICI. Live ETF PDFs often Akamai 403; fixtures transcribe official document text. 2025 open-end PDF blocked. |
| Schwab | **2021–2025** (2025 full annual PDF; 2021–2024 ≥$1B product pages) | Official 2025 PDF `schwab.bynder.com/m/3990d008e1558d0d/` (79 tickers; SWANX LT $1.5191; SWLSX LT $0.4957). 2021–2024 add SWSSX / SWISX / SWLGX (SWSSX 2021 LT $2.3981). Family annual SPA still JS. Daily NII omitted. |
| Dimensional | **2024 + 2025** full books (DISVX / DFELX / DFQTX) | No public filled ICI. 2025 retail estimate PDF is every share class (DISVX LT $1.060). **2024** `2024-distributions.pdf` is the full December MF/ETF book (DISVX income $0.305 / LT $0.184; DFELX income $0.288 / LT $0.012; DFQTX income $0.101 / published $0.000 CG stored). `.../2021-2023-distributions.pdf` aliases serve the 2024 file. |
| Columbia Threadneedle | 2022 / 2024 / 2025 YE paid + 2025 midyear sample | No public filled ICI. 2025 mid-year all-funds PDF is wrap-unsafe (not a column-safe full extract). Wave 11 2024–2025 YE PDFs are the full share-class book (2025 228 tickers; LBSAX LT $1.33133; GSFTX / CDDRX same). 2023 YE PDF still 403/404. |
| Amundi / Pioneer | **2023–2025** official Pioneer / Victory tax-center books (PIODX / PIGFX) | Included per Eric 2026-09-08. 2025 Class A estimate + full 2025 open-end finals (interval XILSX omitted). 2024 Final CG + special YE income. 2023 finals + 10/31/2023 estimates. Live hubs + PDFs walked weekly; fixture fallback. |
| Allspring | **2021–2025** paid YE (WFMIX / WFPAX / SGRAX) | No public filled ICI. Family estimate PDFs are gated login HTML. Product-alerts hub is walked weekly. Wave 12 adds Class A / C / extra Inst product pages (WFPAX 2025 LT $4.26857; SGRAX $8.85612; WOFNX ST $0.40163 / LT $4.06281). Existing Inst rows unchanged. |
| Janus Henderson | **2021–2025 ICI Primary paid YE** + 2021–2022 FINAL paid companions + 2023–2025 estimates | **ICI first** for 2021–2025 (JDCAX LT $4.95363 / $0.02107 / $3.88875 / $5.46939 / $6.96694). Estimate PDFs coexist (JDCAX $3.87 / $5.42 / $6.92). 2021 FINAL paid PDF remains (Forty Fund not on that list — JDBAX 2021 LT $1.50790). Daily ICI income lines skipped. |
| American Century | **2022 + 2023 + 2025** full retail estimates + 2025 paid (TWCGX) | No public filled ICI. 2025 retail estimate PDF is every share class (TWCGX LT $10.4978) plus product-page paid Total $9.7631 (no ST/LT split). 2023 book from Wayback `estimated-distributions-september-aci-retail.pdf` (TWCGX ST $0.0349 / LT $2.4201 / 5.58% of NAV). **2022 official book** `2022-Estimated-Distributions_ACI-MFs-and-ETFs_final` (TWCGX income $0.0037 / LT $0.7247 / 2.00% of NAV; daily bond income skipped). 2024 unversioned retail PDF serves 2025. 2021 sibling 404. |
| Dodge & Cox | 2021–2025 Dec YE paid + Q1 2026 estimate | No public filled ICI. Supplemental tax letters (DODGX Dec 2025 LT $1.1999 / 2024 LT $12.036). 2023–2021 letter PDF siblings 404; Dec YE transcribed from the public product-page API `https://api-v1.dodgeandcox.com/api/funds-distribution` (DODIX Dec income $0.0570 / $0.1010 / $0.1290 / $0.1300 / $0.1347). Quarters omitted so one as_of is not summed. |
| MFS | **2021–2025 YE paid** (Class A + Wave 13 I/R6/C ~232 tickers/year) + 2025 full %NAV estimate + 2026 midyear paid | No public filled ICI. 2025 fly PDF is every published share-class / all-classes row (MIGHX LT 8%–9%; published 0% stored). Official Class A tickers on product-page identifiers (MIGHX / MITTX / MFEGX / MGIAX / OTCAX / MFRFX / MTCAX). Official 10-year Excel on additional Class A pages supplies December YE 2021–2025 (MEIAX LT $1.01429 / $2.67110 / $3.13988 / $3.57266 / $3.86919; MFEGX LT $4.65025 / $1.39190 / $7.90687 / $25.50349 / $25.35332). Wave 13 I/R6/C Excel YE: MGTIX 2025 income $0.30697 / LT $4.20618; MFEIX LT $25.35332; MEIIX LT $3.86919. OTCAX has no 2022–2023 YE row; MNDAX has no 2023–2025 YE row. 2024 fly PDF 404. |
| Lord Abbett | 2025 $0 no-pay list | No public filled ICI. Public PDF lists funds not expected to pay 2025 CG. 2024 sibling 404. No paying-fund ST/LT grid. |
| AllianceBernstein | **2023 full paying-fund estimate** + 2025 full paying-fund estimate | No public filled ICI. 2025 Final_GEN-5796-1025.pdf is every listed payer (AGRFX LT $16.36; Class A tickers only AGRFX / APGAX / ABASX). Unversioned FINAL_GEN-5796.pdf now serves 2025; 2024 overwritten. **2023** GEN–5796–1023 from Wayback `20240422225619` is every listed payer (AGRFX LT $6.95; APGAX LT $1.50; ABASX ST $0.13 / LT $1.32). |
| Federated Hermes | 2025 full prelim PDF (87 classes) + PAYR 19(a) | ICI Primary/Secondary listed on token URLs (not a stable public download; some books are monthly muni lines). Family tax-center grids are JS. Kaufmann pages have no scrapeable ST/LT history. |
| Virtus | 2024 19(a) + 2025 paid + 2026 June full listed estimate | No public filled ICI. 2026 June PDF lists 4 funds (STVTX LT $0.1767); 2025 calyr paid Dec (STVTX LT $0.427834); 2024 19(a) income + combined CG $1.907616. |
| Eaton Vance | 2025 CEF 19(b) (EOI) | No public filled ICI. March 2025 19(b) (EOI $0.1338 LT). 2024 sibling PDFs 403. Open-end YE stays on `morgan_stanley`. |
| John Hancock | 2022–2025 estimate ranges (TAGRX / JBGAX; USGLX 2024–2025) | No public filled ICI. Press-release PDFs still posted. USGLX 2022–2023 em-dash (no CG — omitted). Manulife parent; US JH Investments book. |
| Principal | **2023–2025 paid YE** (~86 tickers) | No public filled ICI. GetFile estimate is a viewer shell. Wave 12 product-page December YE book (2025 79 tickers; PQIAX LT $3.3687; PBLCX $8.3248; PLGIX $1.9823). Quarterly income omitted. |
| Hartford | **2024–2025 PDF** + 2025 share-class product pages | No public filled ICI. Final equity PDFs (HFMCX LT $1.67 / $5.44). Wave 12 product pages add ~186 I/C/F/R/Y classes (HDGIX LT $3.9283; HFMIX $5.4448). Class A stays alias-mapped. |
| Macquarie / Delaware | **2023–2024** full paid + 2025 estimate (WSTAX) | No public filled ICI. US Delaware/Macquarie Funds book only. **2024** CGE-RET-ACT-2024 is the full paying-fund table (WSTAX ST $1.108 / LT $8.135; 16 Class A tickers). **2023** CGE-RET-ACT-2023 is the full paying-fund table (WSTAX LT $5.331; 20 Class A tickers). 2025 estimate LT $10.051. Non-US Macquarie trusts skipped. |
| First Eagle | 2023–2025 paid YE + 2025 full open-end estimate + 2024 full share-class paid | No public filled ICI. 2025 estimate PDF is every listed open-end fund (SGENX LT $4.12–$4.17; FEVAX LT $1.77–$1.82) with Class A tickers from the official 2024 paid PDF. 2024 paid PDF is every open-end share class (40 tickers; Credit Opportunities omitted). 2025 family paid PDF siblings still 404; product-page 2025 paid grids now include Gold / GIB / Small Cap / Rising Dividend (SGENX LT $4.654; FEFAX ST $0.339 / LT $2.015). |
| GMO | 2026 July estimate (GQETX) only | No public filled ICI. US Trust July/Dec 2025 sibling filenames 404. **Skip GMO Australia** unit-trust estimates. |
| Artisan | **2024–2025 ICI YE** (full share-class) + 2026 YTD paid (ARTKX) | **ICI-style Year-End Tax Reporting PDFs.** 2025 is 30-token (ARTIX LT $5.017255; ARTKX Nov LT $2.725068). 2024 is column-safe with LT at token 11 (ARTIX ST $0.456695 / LT $2.067175). 2021–2023 siblings are public but transposed ICI (funds as columns) — not column-safe. YTD HTML keeps ARTKX 2026 income $0.338342. |
| Calamos | 2024 + 2025 estimates (CVGRX) | No public filled ICI. 2024 estimate PDF (CVGRX ST $1.24 / LT $1.84). 2023 sibling 404. |
| Wasatch | 2022 + 2024–2025 paid YE + 2025 estimate (WGROX) | No public filled ICI. 2024 estimate sibling 404. Product-page paid (WGROX 2025 LT $6.345749 / 2024 $8.282696 / 2022 $0.457965). **2023 gap** — no YE row on the product page. |
| Harbor | 2025 estimate (9 Institutional tickers) | No public filled ICI. 2024 sibling PDF 404. Institutional tickers from the official prospectus (HACAX / HAVLX). Third-party combined dividend totals unused. |
| Nationwide | 2025 paid (NWHOX) only | US-domiciled. No public filled ICI. 2024 MFN-0434AO is not a CG book. Hub PDF is unversioned. |

**ICI Primary Layout inventory (top AUM, verified 2026-09-07):**

| Rank | Family | Public filled ICI file? | Notes |
| --- | --- | --- | --- |
| 1 | BlackRock / iShares | no | Open-end 2021–2025 tax-information HTML (flattened Nov–Dec YE). iShares tax kits are 1099-style PDFs, not ICI Primary Layout. |
| 2 | Vanguard | **yes** | Advisor tax center PDFs 2021–2025 (and earlier). Preferred source. |
| 3 | Fidelity | no | Institutional HTML estimates + prior-year paid table. |
| 4 | State Street / SPDR | no | Angular estimate page. Official paid XLSX is public at `.../spdr-etf-historical-distributions.xlsx`. |
| 5 | J.P. Morgan | no | Section 19a PDFs. |
| 6 | Goldman Sachs | no | Advisor tax center 403-walled. |
| 7 | American Funds | no | Public HTML YE + historical-distributions tool. |
| 8 | PIMCO | no | Notices / PDF hub; no ICI download. |
| 9 | Invesco | listed, not fetchable | Open-end tax guide names ICI Primary files; no stable public URL (JS / 406). |
| 10 | T. Rowe Price | no | Public YE HTML (2023–2025) + 2021–2022 YE PDFs. |
| 11 | UBS | no | Estimate PDF is rotating AEM/JCR; price-page HTML for 2025 paid. |
| 12 | Franklin Templeton | listed, not fetchable | Tax-center ICI reports page is a JS SPA; no stable filled-file URL. |
| 13 | BNY Mellon | no | Estimate PDFs + product-page paid history. |
| 14 | Nuveen | no | Document-viewer estimate PDF (`download=1` is the full 2025 MF book). 2024–2025 letters are tax character only. |
| 15 | Northern Trust | **yes (income-only subset)** | Public `nf-ici-primary-*.pdf` 2022–2025. First amount is total (income+CG). December ICI stored as income only when the CG book is em-dash; CG-paying tickers stay on the companion CG PDF. 2021 equity CG PDF is public. |
| 16 | Morgan Stanley | no | ETF/open-end tax PDFs under `/im/publication/forms/tax/`. |
| 17 | Schwab | no | SPA family grids; official 2025 annual PDF + product-page HTML history. |
| 18 | Dimensional | no | Public chmedia distribution PDFs. |
| 19 | Columbia Threadneedle | no | Public midyear estimate + YE cap-gains PDFs. |
| 20 | Amundi / Pioneer | no | Pioneer / Victory tax-center PDFs. **2023–2025 official books included** (Eric 2026-09-08). |
| 21 | Allspring | no | Product-alert estimate PDFs gated; product-page paid HTML used. |
| 22 | Janus Henderson | **yes (2021–2025)** | Official ICI Primary Layout PDFs on the advisor tax hub. 2021 file is `Janus Henderson ICI Primary Layout 2021.pdf` (JDCAX on ICI; absent from the 2021 FINAL PDF). 2024 ICI Primary is `Janus-Henderson-2024-ICI-Primary-Layout.pdf` (hyphenated). |
| 23 | American Century | no | JS hub + 2025 retail PDF; 2023 Wayback + official 2022 `2022-Estimated-Distributions_ACI-MFs-and-ETFs_final`. 2024 unversioned path is the 2025 file. 2021 404. |
| 24 | Dodge & Cox | no | Supplemental tax letters + Q1 estimate PDFs. |
| 25 | MFS | no | 2025 full %NAV fly PDF (175 rows) + official 10-year Excel YE 2021–2025 Class A + Wave 13 I/R6/C Excel (~232 tickers/year) + product-page 2025/2026 paid. |
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
| `amount_unit` | `per_share` or `percent_of_nav`. Bare `"100%"` / `"41.94%"` and QDI "% of dividends that are qualified" are **not** ingested. Real $/share tax-character rows **are** ingested (`ordinary_income`, ST/LT gains, `qualified_dividend` when published as $/share, `special_dividend`, `return_of_capital`, `total_capital_gains`, …). |
| `needs_review` / `review_reason` / `data_quality_flags` | Set after ingest when a `per_share` row is a **category outlier**. Default: more than **±50%** vs the category median for the same calendar year + `estimate_type` (`CATEGORY_OUTLIER_THRESHOLD_PCT=50`, `CATEGORY_OUTLIER_MIN_PEERS=3`). Uses % of NAV when NAV is present, else $/share. Never auto-deleted. Filter: `GET /distributions?needs_review=true`. |
| `record_date`, `ex_date`, `payable_date` | When the manager prints them. Null when the source omits the field (Fidelity `FIIS_SP52_DPL6` / DPL6 paid and Conestoga 2026 estimates have no Record column — see `fixtures/fidelity/RECORD_DATE.md`). Never invented from ex−1 or other heuristics. |
| `as_of` | Page publication date (Capital Group `meta name=date`) |
| `publication_stage` | `preliminary_estimate`, `updated_estimate`, `final`, `paid`. Midyear **estimate** books (Columbia `mid-year-cap-gain-estimates`) stay `preliminary_estimate` / `updated_estimate`. Midyear **paid** / special / interim / semi-annual amounts (Capital Group `midyear-cap-gains`, iShares mid-year table, Davis June rows) map to `paid`. Year-end HTML/PDF maps to `final` (or the matching estimate stage). |
| `source_url` | Page or partner URL |
| `raw_payload` | Original row/page context for audit (list endpoints omit it unless `include_raw=true`) |
| `ingested_at` | Server timestamp of last upsert |

Re-running the **same** source document updates the existing row. A new `as_of` (September preliminary vs December update vs January final) inserts a new snapshot.

## Coverage (portfolio review)

Sparse family coverage makes Aftertax-style portfolio analytics wrong: a book that is 40% Vanguard / iShares / Fidelity looks like it has no taxable distributions if those adapters are stubs. The registry is the **top 110 US-advisor-relevant firms** (AUM ranks 1–110) plus **First Trust** (rank 111), **DWS / Xtrackers** (112), **Catalyst** (113), and **ARK Invest** (114). Multi-year history packs prefer **US-domiciled** managers. `GET /coverage` returns `implemented_pct` (today 114/114 fixture parsers) so the website can later compute *% of portfolio dollars covered*.

`GET /fund-families` includes `coverage_tier` (`implemented` | `stub`), `aum_rank` (1 = largest / highest priority), and `priority`.

When a holding’s ticker or family is not in the store, Website Engineering should call `POST /coverage/gaps` with `{ticker or fund_name, fund_family?, holding_dollars?}`. The API logs the gap in SQLite and returns:

| `suggested_next_step` | Meaning |
| --- | --- |
| `fetch_adapter` | A registered parser exists — run `POST /ingest/fetch` for that slug, then search. If the ticker is still missing, partner-ingest the row. |
| `queued` | Slug is registered but not implemented (none of the top 110 today). |
| `manual_ingest` | Unknown family — `POST /ingest/distributions` is the escape hatch. |

### Website contract: submit a ticker

Coverage gaps log an uncovered holding. They do **not** queue issuer-source ingest. Website Engineering should put a “Request this ticker” box on the uncovered-holding state and call this intake. **Do not block illustrate** on a pending request, and **never invent amounts** while the row is queued.

`POST /requests/tickers` — **202 Accepted**

```json
{
  "ticker": "SGENX",
  "fund_name": "First Eagle Global Fund",
  "fund_family": "first_eagle",
  "source": "website_ui"
}
```

`ticker` is required (uppercased). `fund_name` / `fund_family` / `source` are optional (`source` defaults to `website_ui`).

Response:

| Field | Meaning |
| --- | --- |
| `id` | Request id (poll with `GET /requests/tickers`) |
| `status` | `already_covered` — ticker is already in the store. `matched` — a registered adapter can fetch it. `search_issuer` — no adapter yet; queued for an issuer-source hunt. `queued` — adapter registered but not implemented. `skipped` — Amundi / Pioneer. |
| `adapter_slug` | Family slug when known |
| `detail` | Human-readable next step. Always says not to invent amounts for `search_issuer` / `skipped`. |

`GET /requests/tickers?status=queued` lists recent requests (`status` filter optional).

**Website Submit-ticker / Add to universe** (same SQLite `ticker_requests` table; no auth for beta):

When Search / lookup returns **not in book** (`GET /funds?q=` empty list or `GET /funds/lookup` 404 `not_in_universe`), Website shows **Add to universe** and POSTs here — not “Awaiting Estimate”.

`POST /request/ticker` body `{ ticker, note?, source? }` — ticker is uppercased. This is the intake Website should call.

| HTTP | `status` | When |
| --- | --- | --- |
| **200** | `already_covered` | Distributions already exist for that ticker |
| **201** | `queued` | New request persisted for weekly expand / issuer search |
| **422** | — | Invalid ticker (not 2–8 `A–Z` / `0–9`) |

Response body is exactly `{ "id", "ticker", "status", "message" }` — no auth for beta. Do not block illustrate on a pending request. Never invent amounts.

`GET /request/ticker?status=queued` lists pending rows for the weekly expand job.

`POST /ingest/ticker-requests?mode=fixture` (weekly job / operator) picks up `queued` / `search_issuer` / `matched` rows, runs `POST /ingest/fetch` for the matched family when known, then sets `already_covered` if the ticker is now in the store. Unknown tickers stay `search_issuer` on the operator path (`/requests/tickers`) and `queued` on the Website path (`/request/ticker`). Amundi stays `skipped`. Empty/403/SPA live hubs remain no-op success.

Weekly GitHub Action `.github/workflows/weekly-ingest.yml` runs `python -m app.cli refresh` then `python -m app.cli ticker-requests` so queued Website Submit-ticker rows are expanded after the family walk. No amounts are invented.

| Rank | Slug | Display name | Parser | Live HTML | Public source (verified 2026-09-07) |
| --- | --- | --- | --- | --- | --- |
| 1 | `blackrock` (alias `ishares`) | BlackRock / iShares | implemented | yes | https://www.ishares.com/us/capital-gains-distributions |
| 2 | `vanguard` | Vanguard | implemented | JS SPA + ICI PDF fixtures | **ICI first:** Primary Layout PDFs 2021–2025 under `/content/dam/fas/pdfs/`. 2021–2025 December rows are full-book (wrap/DAILY bleed skipped). YE SPA is fallback for 2025 VFIAX / VBIAX / VIGAX only. |
| 3 | `fidelity` | Fidelity | implemented | yes (estimates + prior-year + Advisor A/C/M/I/Z) | https://institutional.fidelity.com/app/tabbed/products/FIIS_SP52_DPL6.html?navId=324 ; prior-year `FIIS_SP10_DPL6` ; Advisor `FIIS_SP52_DPL2_DSC1` / `FIIS_SP10_DPL2_DSC1` (`shareClassId` A/C/M/I/Z) |
| 4 | `state_street` (aliases `spdr`, `ssga`) | State Street / SPDR | implemented | Angular estimate + official XLSX fixtures | https://www.ssga.com/library-content/products/fund-data/etfs/us/spdr-etf-historical-distributions.xlsx |
| 5 | `jpmorgan` (alias `jpm`) | J.P. Morgan AM | implemented | PDF / no HTML grid | Section 19a PDFs under am.jpmorgan.com `.../section-19-notices/` |
| 6 | `goldman_sachs` (aliases `gs`, `gsam`) | Goldman Sachs AM | implemented | 403 / PDF library | https://www.gsam.com/content/gsam/us/en/advisors/literature-and-forms/forms-and-tax-center.html |
| 7 | `american_funds` (alias `capital_group`) | American Funds | implemented | yes | Capital Group individual tax center (see below) |
| 8 | `pimco` | PIMCO | implemented | PDF / notices | https://www.pimco.com/us/en/resources/tax-center |
| 9 | `invesco` | Invesco | implemented | PDF + PR (2024–2025 fixtures) | 2025 PDF + 2024 In Focus `contentId=29096ee0-8ec4-4199-930f-645be9d07e64` |
| 10 | `t_rowe_price` (alias `trp`) | T. Rowe Price | implemented | yes (2023–2025 HTML + ETF YE; 2022 PDF) | MF: https://www.troweprice.com/personal-investing/resources/planning/tax/dividend-distributions/mutual-funds/2025-year-end-distributions.html ; ETF: `…/etfs/2025-year-end-distributions.html` |
| 11 | `ubs` | UBS Asset Management | implemented | price-page HTML / PDF | https://www.ubs.com/us/en/assetmanagement/funds/mutual-fund-price.html (paid PWTAX); estimate PDF from the mutual-fund product hub |
| 12 | `franklin_templeton` (aliases `franklin`, `templeton`, `putnam`) | Franklin Templeton | implemented | JS SPA + 19(a) PDF + DIST-SUMM | https://www.franklintempleton.com/tools-and-resources/tax-center ; CEF 19(a) e.g. `.../ft-section-19-notice-12-31-2025` ; DIST-SUMM `.../download/DIST-SUMM` |
| 13 | `bny_mellon` (aliases `bny`, `dreyfus`) | BNY Mellon / Dreyfus | implemented | PDF + product HTML | 2025 estimate PDF + DGAGX paid YE 2022–2025 on the Appreciation product page |
| 14 | `nuveen` (alias `tiaa`) | Nuveen / TIAA | implemented | PDF viewer | https://documents.nuveen.com/Documents/Nuveen/Default.aspx?uniqueId=3c3be13d-d800-48e2-a537-c251162ab9f4 |
| 15 | `northern_trust` (aliases `nt`, `ntam`) | Northern Trust | implemented | PDF + ICI-derived HTML | 2021 full equity CG + 2022–2024 flagship + 2025 equity CG + ICI Dec income-only; FI daily omitted |
| 16 | `morgan_stanley` (aliases `msim`, `ms`) | Morgan Stanley IM | implemented | PDF (often Akamai-walled) | 2024 + 2025 ETF YE under `/im/publication/forms/tax/` |
| 17 | `schwab` (alias `charles_schwab`) | Charles Schwab IM | implemented | JS family page; product HTML | Product pages `swtsx` / `swppx` (2022–2025); 2025 family SPA fallback |
| 18 | `dimensional` (alias `dfa`) | Dimensional | implemented | PDF | **2024–2025 full books** (`2024-distributions.pdf` 138 tickers; DISVX 2024 LT $0.184) |
| 19 | `columbia_threadneedle` (aliases `columbia`, `ameriprise`) | Columbia Threadneedle | implemented | PDF | 2025 midyear + 2025/2024/2022 YE share-class `*cap-gain*` PDFs |
| 20 | `amundi` (aliases `pioneer`, `victory_pioneer`) | Amundi US / Pioneer | implemented | PDF + tax-center hubs | Included per Eric 2026-09-08. Live Pioneer / Amundi / Victory hubs + 2025 estimate/final PDFs. Official 2023–2025 books (PIODX ST/LT). Interval omitted. |
| 21 | `allspring` (aliases `wells_fargo`, `wfam`) | Allspring | implemented | product-page HTML / gated PDF | Paid YE 2022–2025 on `.../special-mid-cap-value/` and `.../growth/i/` (WFMIX / SGRNX). Family estimate PDFs gated. |
| 22 | `janus_henderson` (alias `janus`) | Janus Henderson | implemented | ICI PDF + estimate/final PDF | 2021–2025 ICI Primary paid YE (JDCAX LT $4.95363 / $0.02107 / $3.88875 / $5.46939 / $6.96694) plus estimate PDFs and 2021–2022 FINAL paid companions. |
| 23 | `american_century` | American Century | implemented | JS hub + PDF + product HTML | 2025 retail estimate PDF + 2023 Wayback + official 2022 retail estimate (TWCGX LT $0.7247 / $2.4201 / $10.4978) + TWCGX product-page paid Total $9.7631. |
| 24 | `dodge_cox` (aliases `dodge`, `dodgx`) | Dodge & Cox | implemented | PDF | Q1 2026 estimate + 2024/2025 supplemental tax letters (DODGX Dec YE). 2023 letter 404. |
| 25 | `mfs` | MFS Investment Management | implemented | PDF + product HTML + 10-year Excel | 2025 full %NAV fly PDF (175 rows; official Class A tickers) + 10-year Excel YE 2021–2025 Class A + Wave 13 I/R6/C Excel (~232 tickers/year; MGTIX / MFEIX / MEIIX) + paid YE 2025 / midyear 2026. 2024 fly 404. |
| 26 | `lord_abbett` (alias `lord`) | Lord Abbett | implemented | PDF (no-pay list) | 2025 Funds-with-Losses.pdf. 2024 sibling 404. No paying-fund ST/LT grid. |
| 27 | `ab` (aliases `alliancebernstein`, `alliance_bernstein`) | AllianceBernstein | implemented | PDF | 2025 Final_GEN-5796-1025.pdf; **2023** Wayback `20240422225619` GEN–5796–1023 full paying book. 2024 overwritten. |
| 28 | `federated_hermes` (alias `federated`) | Federated Hermes | implemented | JS tax center + prelim PDF + 19(a) | Official 2025 prelim 50135 (KAUAX LT $0.638052) + PAYR 19(a). ICI token-walled. |
| 29 | `virtus` | Virtus | implemented | PDF | 2026 June estimate + 2025 calyr paid + 2024 19(a) (STVTX). |
| 30 | `eaton_vance` (alias `ev`) | Eaton Vance | implemented | CEF 19(b) PDF | March 2025 combined 19(b) (EOI). 2024 siblings 403. |
| 31 | `john_hancock` (aliases `manulife`, `jh`) | John Hancock / Manulife | implemented | PDF | Press-release estimate PDFs 2022–2025 (TAGRX). US JH Investments book. |
| 32 | `principal` | Principal | implemented | product-page HTML / viewer PDF | PQIAX / PEMGX product-page paid YE 2023–2025. Tax hub GetFile estimate PDF is a viewer shell. |
| 33 | `thrivent` | Thrivent | implemented | yes | https://www.thriventfunds.com/support/tax-resource-center/capital-gains.html |
| 34 | `hartford` | Hartford Funds | implemented | PDF | 2025 estimate memo + 2024/2025 final equity PDFs under `.../capgainsdistributions/` (HFMCX) |
| 35 | `macquarie` (aliases `delaware`, `delaware_funds`) | Macquarie / Delaware Funds | implemented | PDF | US CGE-RET 2025 estimate + **2023–2024** CGE-RET-ACT full paying books (WSTAX). Non-US Macquarie trusts skipped. |
| 36 | `first_eagle` (alias `fei`) | First Eagle | implemented | PDF + product HTML | 2025 full open-end estimate + 2024 full share-class paid PDF + product-page 2025 paid YE (SGENX / FEFAX; 42 tickers). 2025 family paid PDF siblings still 404. |
| 37 | `gmo` | GMO | implemented | PDF | US Trust July 2026 estimate. 2025 siblings 404. Skip GMO Australia. |
| 38 | `artisan` (alias `artisan_partners`) | Artisan Partners | implemented | ICI PDF + YTD HTML | 2024–2025 Year-End Tax Reporting ICI. YTD HTML for 2026 ARTKX income. 2021–2023 ICI public but transposed / not column-safe. |
| 39 | `calamos` | Calamos | implemented | PDF | 2024 + 2025 estimate PDFs (CVGRX). 2023 sibling 404. |
| 40 | `wasatch` | Wasatch | implemented | PDF + product HTML | 2025 estimate PDF + WGROX product-page paid 2022/2024/2025 (2023 gap). |
| 41 | `harbor` | Harbor | implemented | PDF | 2025 estimate PDF (9 Institutional tickers; HACAX / HAVLX). 2024 sibling 404. |
| 42 | `nationwide` | Nationwide | implemented | PDF | 2025 MFN-0435AO (NWHOX). US-domiciled. 2024 sibling is not a CG book. |
| 43 | `voya` (alias `allianzgi`) | Voya | implemented | PDF | https://individuals.voya.com/document/tax-center/2025-estimated-capital-gains.pdf |
| 44 | `oakmark` (aliases `harris`, `harris_associates`) | Oakmark / Harris Associates | implemented | yes — fixture fallback | https://oakmark.com/news-insights/2025-oakmark-year-end-fund-distributions/ |
| 45 | `tweedy` (alias `tweedy_browne`) | Tweedy, Browne | implemented | PDF | https://www.tweedyfunds.com/wp-content/uploads/sites/10/2025/10/2025-Estimated-Distributions-9-30-25-2.pdf |
| 46 | `gabelli` (alias `gamco`) | Gabelli | implemented | PDF | https://gabelli.com/wp-content/uploads/2025/12/Distribution-memo-12.29.2025.pdf |
| 47 | `royce` | Royce | implemented | yes — fixture fallback | https://www.royceinvest.com/news/2025/4Q25/open-end-funds-2025-year-end-distributions |
| 48 | `nylife` (aliases `mainstay`, `nyli`) | New York Life Investments / MainStay | implemented | PDF | 2025 paying-fund estimate flyer (24 Class I tickers; MLAIX). https://www.nylim.com/assets/documents/tax/cap-gains-estimate.pdf |
| 49 | `touchstone` | Touchstone | implemented | PDF | 2025 CG PDF (14 tickers; TVLAX / TGVFX / TEGAX / TSNAX / SAGWX + ETF TSEC / SIO / TUSI). Dividend Equity / International Value / Large Cap Focused / Large Company Growth still name-only. |
| 50 | `victory` (aliases `vcm`, `victory_capital`) | Victory Capital | implemented | PDF | 2025 estimate + official finals for Portfolios I/II, RS, and Portfolios III / USAA (150 tickers; MMEAX / VETAX / RSGRX / USSPX) plus Wave 7 2022–2023 I/II / RS / III lookback (MMEAX 2022 LT $2.389672). 2021 still 404. Pioneer / Portfolios IV skipped. |
| 51 | `sei` (alias `seic`) | SEI | implemented | PDF | https://www.seic.com/sites/default/files/2025-11/SEI%20Capital%20gains%20distribution%20estimates_11.20.2025.pdf |
| 52 | `brown_advisory` (alias `brown`) | Brown Advisory | implemented | PDF | https://www.brownadvisory.com/sites/default/files/2025-10/2025-Capital-Gain-Distribution-Update.pdf |
| 53 | `william_blair` (aliases `blair`, `wbim`) | William Blair | implemented | PDF | https://media.im.williamblair.com/v1/media/edge/images/williamblaib9c8-wbim74f8-wbimprod42cd-8345/media/documents/resources/us/distributions/william-blair-funds---annual-distributions-2025---class-i-n-and-r6.pdf |
| 54 | `vaneck` (alias `van_eck`) | VanEck | implemented | PDF | https://www.vaneck.com/us/en/vaneck-funds-estimated-yearend-distributions-2025.pdf |
| 55 | `wisdomtree` (alias `wt`) | WisdomTree | implemented | PDF | https://www.wisdomtree.com/investments/-/media/us-media-files/documents/about/pdf/2025/wisdomtree-etfs-declare-final-capital-gains-distributions-2025.pdf |
| 56 | `aqr` | AQR | implemented | PDF | https://funds.aqr.com/-/media/Funds/Tax-Documents/2025/2025-AQR-Funds-Announces-Estimated-Distributions.pdf?sc_lang=en |
| 57 | `causeway` | Causeway | implemented | PDF | https://www.causewaycap.com/wp-content/uploads/2025_Causeway-Funds-Final-Distributions.pdf |
| 58 | `alger` (aliases `fred_alger`, `fredalger`) | Alger / Fred Alger | implemented | PDF | 2025 MF + ETF books + Wayback 2022 MF (ACAAX LT $0.8384) and 2021/2023 ETF (FRTY 2021 ST $1.0687). 2023/2024 MF siblings 404. |
| 59 | `harding_loevner` (aliases `harding`, `hl`) | Harding Loevner | implemented | PDF | https://wealth.amg.com/pdf-library/harding-loevner-2025-year-end-distributions/ |
| 60 | `matthews_asia` (alias `matthews`) | Matthews Asia | implemented | yes — fixture fallback | https://www.matthewsasia.com/funds/mutual-funds/ |
| 61 | `tcw` | TCW | implemented | PDF | https://edge.sitecorecloud.io/thetcwgroupc320-tcwweb7bc3-prod0f26-25f9/media/Downloads/TCW/Products/US-Funds/TCW-Funds/Distribution-and-Tax-Information/TCW-FUND-Distributions-final.pdf?sc_lang=en |
| 62 | `bridgeway` | Bridgeway | implemented | PDF | https://bridgewayfunds.com/wp-content/uploads/sites/2/2025/11/2025-Distribution-Estimates-for-Website.pdf |
| 63 | `jensen` | Jensen | implemented | yes — fixture fallback | https://www.jenseninvestment.com/insights/2025-growth-mutual-fund-distributions/ |
| 64 | `diamond_hill` (alias `diamond`) | Diamond Hill | implemented | PDF | 2025 estimate + 2024 sibling; Investor tickers DHSCX / DHMAX / DHPAX / DHLAX / DHTAX / DIAMX / DHIAX from official product pages. |
| 65 | `champlain` (aliases `cip`, `cipvt`) | Champlain | implemented | PDF | https://cipvt.com/wp-content/uploads/2025/12/Champlain-Funds-2025-Year-End-Distributions-Final-12-16-25.pdf |
| 66 | `driehaus` | Driehaus | implemented | PDF | 2025 YE PDF; official tickers DMCRX / DVSMX / DNSMX / DSMDX / DRIOX / DIDEX / DREGX / DIEMX / DRESX / DEVDX / DMAGX. |
| 67 | `hotchkis` (aliases `hw`, `hotchkis_wiley`) | Hotchkis & Wiley | implemented | PDF | https://www.hwcm.com/wp-content/uploads/2025/03/HW-Funds-Dec-2025-Div-Cap-Gain-Distributions.pdf |
| 68 | `marsico` | Marsico | implemented | yes — fixture fallback | https://www.marsicofunds.com/investor-resources/content/distributions.fs |
| 69 | `osterweis` (alias `ost`) | Osterweis | implemented | PDF | https://www.osterweis.com/files/Distribution-Estimates.pdf |
| 70 | `davis` (alias `davis_funds`) | Davis Funds | implemented | yes — fixture fallback | https://davisfunds.com/funds/distributions |
| 71 | `primecap` (aliases `odyssey`, `primecap_odyssey`) | PRIMECAP Odyssey | implemented | PDF | https://www.primecap.com/wp-content/uploads/2025/11/2025-Distribution-Estimates-as-of-10312025-PCF000287.pdf |
| 72 | `ariel` | Ariel | implemented | PDF | https://www.arielinvestments.com/wp-content/uploads/2025/12/Distributions_ArielFund_as-of-12.17.2025-Final.pdf |
| 73 | `baird` | Baird | implemented | PDF | https://www.bairdassetmanagement.com/siteassets/pdfs/distributions/2025-final-capital-gains.pdf |
| 74 | `longleaf` (alias `southeastern`) | Longleaf Partners | implemented | yes — fixture fallback | https://southeasternasset.com/investment-offerings/longleaf-partners-fund/ |
| 75 | `buffalo` | Buffalo | implemented | PDF | 2025 estimate PDF; official Investor tickers BUFEX / BUFOX / BUFBX / BUFGX / BUFDX / BUFIX / BUFTX / BUFMX. |
| 76 | `gqg` | GQG Partners | implemented | PDF | https://gqg.com/content/2025/10/2025-Estimated-Capital-Gain-Distributions-09.30.pdf |
| 77 | `third_avenue` (aliases `thirdave`, `tav`) | Third Avenue | implemented | yes — fixture fallback | https://www.thirdave.com/2025-income-capital-gain-distributions |
| 78 | `heartland` | Heartland | implemented | yes — fixture fallback | https://www.heartlandadvisors.com/Resources/Tax-Information |
| 79 | `fmi` (alias `fmimgt`) | FMI | implemented | PDF | https://www.fmimgt.com/fmi/funds/cs/CS_distribution_summary_2025.pdf |
| 80 | `impax` (aliases `pax`, `impaxam`) | Impax / Pax | implemented | gated HTML — fixture | https://impaxam.com/customer-service/distributions/ |
| 81 | `american_beacon` (alias `beacon`) | American Beacon | implemented | PDF | https://americanbeaconfunds.com/wp-content/uploads/2025/09/2025-Annual-Ordinary-Income-and-Capital-Gains-Mutual-Funds-updated.pdf |
| 82 | `baillie_gifford` (aliases `baillie`, `bg`) | Baillie Gifford | implemented | PDF | 2025 estimate PDF; Institutional / Class K tickers BSGPX / BGCSX / BGAKX / BINSX / BGESX from official prospectus. |
| 83 | `brandes` | Brandes | implemented | PDF | 2025 estimate PDF; Class I tickers BISMX / BGVIX / BIIEX / BEMIX / BSCMX from official brandes.com pages. |
| 84 | `mairs_power` (aliases `mairs`, `mairsandpower`) | Mairs & Power | implemented | yes — fixture fallback | https://www.mairsandpower.com/about-us/company-news/290-2025-capital-gains-and-dividends |
| 85 | `boston_trust` (aliases `walden`, `boston_trust_walden`) | Boston Trust Walden | implemented | PDF | https://www.bostontrustwalden.com/wp-content/uploads/2025/12/Boston-Trust-Mutual-Funds-2025-Ex-Date-ending-NAV.pdf |
| 86 | `grandeur_peak` (alias `grandeur`) | Grandeur Peak | implemented | yes — fixture fallback | https://grandeurpeakglobal.com/distributions/ |
| 87 | `hennessy` | Hennessy | implemented | yes — fixture fallback | https://www.hennessyfunds.com/funds/distributions |
| 88 | `fam` (alias `fenimore`) | FAM / Fenimore | implemented | yes — fixture fallback | 2025 tax-center HTML; official tickers FAMVX / FAMWX / FAMEX / FAMFX / FAMDX. |
| 89 | `meridian` (alias `arrowmark`) | Meridian | implemented | PDF | https://www.arrowmarkpartners.com/meridian/wp-content/uploads/sites/2/2025-Final-Distributions-Meridian-Funds-121925.pdf |
| 90 | `kinetics` (alias `horizon_kinetics`) | Kinetics | implemented | PDF | https://kineticsfunds.com/wp-content/uploads/2025/12/2025-Q4-Kinetics-Funds-Final-Distributions.pdf |
| 91 | `lazard` (alias `lam`) | Lazard | implemented | PDF | https://www.lazardassetmanagement.com/docs/1791/LazardFundsAnnualDistributionDeclarationEstimated.pdf |
| 92 | `manning_napier` (aliases `manning`, `manningandnapier`) | Manning & Napier | implemented | PDF | 2025 YE PDF; official product-page tickers on CUSIP/class rows (36 tickers; CEIIX / MNDFX / RAIIX / MNHAX). |
| 93 | `westwood` (alias `whg`) | Westwood | implemented | PDF | https://westwoodgroup.com/wp-content/uploads/2025/10/Fund-Distribution-2025-Cap-Estimate_STAMPED.pdf |
| 94 | `boston_partners` (aliases `bostonpartners`, `robeco`) | Boston Partners | implemented | PDF | https://www.bostonpartners.com/uploads/2025/11/b15ac374201c51486acab7203763117a/bp-funds-estimated-cap-gain-dist-10_31_2025.pdf |
| 95 | `homestead` (alias `nreca`) | Homestead | implemented | PDF | https://www.homesteadadvisers.com/wp-content/uploads/Year-End-Distributions.pdf |
| 96 | `madison` (alias `madison_funds`) | Madison | implemented | yes — fixture fallback | https://madisonfunds.com/resources/tax-center/ |
| 97 | `lsv` (alias `lsvasset`) | LSV | implemented | PDF | https://www.lsvasset.com/pdf/fund-docs/2025-Distributions-12-25.pdf |
| 98 | `lkcm` (alias `luther_king`) | LKCM | implemented | PDF | https://lkcmfunds.com/wp-content/uploads/2025-LKCM-Year-End-Mutual-Fund-Distribution-Estimates-11-3-25.pdf |
| 99 | `oberweis` (alias `oam`) | Oberweis | implemented | PDF | https://oberweisfunds.com/wp-content/uploads/2026/03/2025-Final-Distributions-Sheet.pdf |
| 100 | `riverpark` (alias `rp`) | RiverPark | implemented | PDF | https://riverparkfunds.com/assets/pdfs/news/Distribution_Info_2025_Website_RFT_FINAL_CAP_GAINS_FINAL_INCOME.pdf |
| 101 | `amg` (aliases `amg_funds`, `amgfunds`) | AMG | implemented | PDF | https://wealth.amg.com/pdf-library/amg-funds-2025-year-end-distributions/ |
| 102 | `guidestone` (alias `guide_stone`) | GuideStone | implemented | yes — fixture fallback | 2025 Capital-Gains HTML; official Investor tickers (21; GGEZX / GMZXX / GVIZX / GFSZX / GMGZX). |
| 103 | `value_line` (aliases `valueline`, `vl`) | Value Line | implemented | yes — fixture fallback | https://vlfunds.com/gains |
| 104 | `permanent_portfolio` (alias `prpfx`) | Permanent Portfolio | implemented | PDF | https://www.permanentportfoliofunds.com/pdf/2025%20Supplemental%20Tax%20Information_FINAL.pdf |
| 105 | `conestoga` | Conestoga | implemented | yes — fixture fallback | https://conestogacapital.com/capital-gains-information/ (2026 estimate ST/LT/Total only — no Record/Ex/Pay; `record_date` null) |
| 106 | `kopernik` | Kopernik | implemented | PDF | https://www.kopernikglobal.com/wp-content/uploads/2025/12/KGI-CG-MEMO-December-2025-FINAL-1.pdf |
| 107 | `locorr` | LoCorr | implemented | PDF | https://locorrfunds.com/wp-content/uploads/2021/04/LoCorr-Funds-Annual-CapitalGains-Dividends.pdf |
| 108 | `timothy_plan` (alias `timothy`) | Timothy Plan | implemented | PDF | https://timothyplan.com/download/Capital_Gains_Distribution.pdf |
| 109 | `hodges` | Hodges | implemented | PDF | https://www.hodgescapital.com/hubfs/Mutual_Funds/Documents/Year_End_Distribution_Estimates.pdf |
| 110 | `tocqueville` | Tocqueville | implemented | PDF | https://www.tocquevillefunds.com/wp-content/uploads/2025/12/2025-FINAL-Distributions-December-9-2025.pdf |
| 111 | `first_trust` (aliases `ft`, `ftportfolios`) | First Trust | implemented | PDF 19(a) | https://www.ftportfolios.com/Common/ContentFileLoader.aspx?ContentGUID=ad59e9bb-c8bb-4696-bf2d-42b9fa64b17e |
| 114 | `ark` (aliases `ark_invest`, `ark_funds`, `arkinvest`) | ARK Invest | implemented | PDF FINAL | https://etfs.ark-funds.com/hubfs/1_Download_Files_ETF_Website/Distribution%20Files/ARKETFs_12021_Handout_Capital_Gains_Distribution_2021.pdf |

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

**Victory vs Pioneer / Amundi:** Pioneer open-end books stay on `amundi` (aliases `pioneer`, `victory_pioneer`), now included per Eric 2026-09-08. `victory` is Victory Portfolios I/II (Integrity / Sycamore / Multi-Cap) plus official 2025 RS and Portfolios III / USAA finals. Pioneer / Victory Portfolios IV is the `amundi` adapter (Victory-hosted Pioneer tax center).

**Clearbridge / Western Asset:** skipped as distinct `FundSource`s. Both are Franklin / Legg Mason brands. Use `franklin_templeton` (aliases `franklin`, `templeton`).

**Brandywine:** skipped. US retail books overlap Franklin / Macquarie; no distinct public 2025 estimate or paid family table was found.

**DoubleLine:** skipped for this tier. The public 12/4/2025 final capital-gains PDF (`https://doubleline.com/wp-content/uploads/12-4-2025-DoubleLine-Funds-Final-Capital-Gains.pdf`) lists $0.00 for every fund — no scrapeable non-zero estimate book. Use `POST /ingest/distributions` if an advisor notice has amounts.

**Guggenheim:** skipped. Public materials are CEF monthly distributions / Section 19(a) notices, not an open-end family capital-gains estimate book.

**First Trust:** implemented (rank 111, aliases `ft`, `ftportfolios`). Official Section 19(a) notice `ContentGUID=ad59e9bb-c8bb-4696-bf2d-42b9fa64b17e` is the current NII/ST/LT/ROC book for BFAP / BFJL / BGLD / IGLD. Official 24 Sep 2025 family declaration `ContentGUID=865e45a8-c914-4704-bc74-7227c3cabaf5` is the 146-ETF ordinary-income book (FVD $0.2519). Wave 11 adds official December family declarations `ContentGUID=cf8dadde-0a3c-463c-b694-5111dbd18e39` (2025; FVD $0.3186) and `ContentGUID=93a2ae96-a7c6-468c-b68b-8f516d1de5c4` (2024; FVD $0.2752). Blank LT omitted. Wrapped unpaired rows omitted. Interval / tender-offer First Trust Capital Management and Vest “Coming Soon” rows omitted.

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
| 2025 year-end distributions (final LTCG/STCG, special dividends; QDI % of income is not ingested) | https://www.capitalgroup.com/individual/service-and-support/tax-center/2025-year-end-distributions.html |
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

SQLAlchemy models are dialect-neutral (`JSON` on SQLite, `JSONB` on Postgres; Numeric; timezone-aware DateTime). `psycopg[binary]` is a default image dependency. File SQLite still uses NullPool + WAL (`WEB_CONCURRENCY=1`). Postgres uses QueuePool (`pool_size=5`, `max_overflow=5`, `pool_pre_ping`, `pool_recycle=1800`).

```bash
export DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/distributions
alembic upgrade head   # required before serving Postgres; also the Render pre-deploy command
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

`postgres://` and `postgresql://` URLs (Render internal) are rewritten to `postgresql+psycopg://` at config time.

SQLite local / pytest still use `create_all` + `_ensure_*` until cutover. Production Postgres schema is Alembic revision `0001_initial` (seven tables, frozen upsert keys, `VARCHAR(36)` PKs — not native UUID).

Copy a frozen SQLite snapshot (never invent amounts):

```bash
python scripts/copy_sqlite_to_postgres.py \
  --source sqlite:////path/to/distributions.db \
  --dest postgresql+psycopg://user:pass@host/distributions
```

Live Render stays on SQLite until Eric runs `docs/CUTOVER.md`. Do not apply `docs/render.postgres-launch.example.yaml` to `aftertax-data-api`.

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
# Optional Postgres path (skip SQLite-only EXPLAIN tests automatically):
# TEST_DATABASE_URL=postgresql+psycopg://distributions:distributions@localhost:5432/distributions pytest -q
```

Coverage includes HTML normalization (American Funds plus top-110 family fixtures), multi-year history filters, upsert idempotency, search filters, tax illustration math, portfolio coverage, Current vs Proposed allocation compare, compare-chart deltas, Growth of $X performance series, and coverage-gap logging.

## Layout

```
app/
  main.py              FastAPI app
  api.py               HTTP routes
  models.py / schemas.py / crud.py
  db.py / config.py    Dialect-aware engine + DATABASE_URL rewrite
  sources/             FundSource adapters + HTML parser
  services/ingest.py   Fetch + upsert orchestration
  services/illustrate.py  Tax-impact illustration
  services/performance.py Growth of $X (Yahoo adj-close; not weekly refresh)
  services/coverage.py Coverage snapshot + gap logging
  services/copy_db.py  SQLite → Postgres copy + checksum
  cli.py               seed / fetch / families
alembic/               Postgres schema (0001_initial)
scripts/copy_sqlite_to_postgres.py
docs/CUTOVER.md        Eric Manual Deploy checklist
fixtures/<family>/     HTML fixtures (American Funds + top 110)
fixtures/performance/  Monthly adj-close fixtures (AGTHX, SPY, AGG, VXUS, …)
tests/
```
