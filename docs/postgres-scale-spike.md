# Postgres + multi-worker scale plan

**Status:** Implementation in progress / **greenlit** (Eric, lean path).  
Engineering lands on `cursor/postgres-lean-cutover-dbd2` (base: `cursor/fund-distribution-ingest-api-85ed`).  
**Do not** migrate production, change live Render env, cut traffic, or apply the example Blueprint to `aftertax-data-api` from this work. Eric will **Merge + Manual Deploy** using [CUTOVER.md](./CUTOVER.md).

**Approved lean path:** Web Starter + `WEB_CONCURRENCY=2` after cutover; Postgres **Basic-1gb**; remove SQLite disk after cutover; no Redis/CDN.

**Audience:** Eric + implementation.  
**Source branch:** `cursor/fund-distribution-ingest-api-85ed` @ `60aefca` (includes #117 / #118).  
**Live API probed this spike (2026-09-10, read-only):** https://aftertax-data-api.onrender.com  
**This work does not invent fund or distribution amounts.**

Friends / soft beta stay on SQLite until Eric's cutover window.

**Data | Engineering — read first:** [Locked coordination rules](#2-locked-data--engineering-coordination-do-not-relax) · [Draft entity list](#3-draft-entity-list-confirmed-2026-09-10) · [Schema freeze](#5-schema-freeze)

**Confirmed (2026-09-10)** by Data | Engineering — all §3 entities/keys OK. Non-blocking migrate constraints in [§3.9](#39-non-blocking-migrate-constraints-confirmed).

---

## 1. Why this spike

#117 stopped concurrent `/funds` from 502ing (NullPool + WAL + page-scoped live-estimate). #118 stopped ticker Search from table-scanning `raw_payload`. Production Search is now usable for a single user (~0.13–0.34s on this probe) but the architecture is still **one uvicorn worker + one SQLite file on a Starter disk**.

That combination cannot be official-launch scale:

| Constraint | Why it blocks launch |
|---|---|
| `WEB_CONCURRENCY=1` | Concurrent Search serializes on one process. #118 still saw ~15s/request on an 8-way burst *after* #117. |
| Persistent disk at `/var/data` | Render: **single instance only**, **zero-downtime deploys disabled**. |
| File SQLite + `NullPool` | Correct for SQLite; wrong for Postgres. One connection per request, no sharing across workers. |
| Weekly GitHub Action | Writes a **runner-local** SQLite unless a `DATABASE_URL` secret exists. It cannot see `/var/data` on Render. Live book is fixture boot-seed, not the weekly job. |

Soft beta can keep SQLite. Official / paid traffic needs Postgres + a real pool + more than one worker, and (after the disk is gone) the option to add a second instance later.

---

## 2. Locked Data | Engineering coordination (do not relax)

These rules are **locked** for the scale plan. This spike does not implement them; it records them so the later Postgres work cannot “optimize” them away. Accuracy still beats scale.

### 2.1 Accuracy first — never invent estimates

| Rule | How the live API already behaves | Scale / Postgres implication |
|---|---|---|
| Never invent amounts | Parsers + upsert skip characterization `%` (QDI-of-income). Missing values stay **null**. | Copy and Alembic must preserve **null vs 0**. Do not `COALESCE` amounts to 0. |
| **Awaiting Estimate** when in-book but unpublished | `GET /funds` `coverage_status=awaiting_estimate` (`has_estimate=false`). Not a miss. | Do not invent a prelim row to “fill the hero bar.” |
| **Undisclosed** when a history year is missing | `GET /coverage` lookback_5y: missing 2021–2025 finals stay unmatched / Undisclosed — **never invented as $0**. | Lookback queries stay `final`/`paid` + `per_share` only. |
| Ticker not in universe | `GET /funds/lookup` 404 `not_in_universe`. Never conflate with Awaiting Estimate. | Unchanged contract. |
| **Announced $0 kept** | Upsert will store `amount=0` if a parser emits it. **Gap:** `app/sources/ici.py` currently `continue`s on `Decimal("0")` — ICI $0 lines never reach the book. Other adapters do not have that skip. | Flag for Data (not this spike). Postgres must still allow 0. Do not add a CHECK that rejects 0. |
| Historical **% of NAV** | `est $/share ÷ nav_on_distribution_day × 100` (`ex_date`, else `payable_date`; last print on or before, ≤7 days). Null if unknown — **never today's weekly NAV** for a past day. | `fund_nav_history` natural key `(ticker, nav_as_of)` stays frozen. |
| Live **% of NAV** | `est $/share ÷ latest weekly NAV` (`fund_navs`). | `fund_navs` unique `ticker` stays frozen. |

Hero-bar math lives in `app/services/nav.py` (Eric lock 2026-09-09) and `app/schemas.py` `percent_of_nav`.

### 2.2 Storage portable

- Prefer types/indexes that compile on **both** SQLite (soft beta) and Postgres (launch).
- **Do not add new SQLite-only features** (new PRAGMAs, `EXPLAIN QUERY PLAN` in app code, SQLite-only `ALTER` helpers, FTS5, etc.).
- Keep `raw_payload` **out of hot Search paths** (post-#118). Unique-fund Search selects identity columns only (`id`, `fund_identifier`, `fund_name`, `fund_family`, `ticker`, `as_of`, `ingested_at`).
- New indexes must be expressible in Alembic for Postgres; SQLite `_ensure_*` is legacy until cutover.

### 2.3 Efficient ingest

- Delta / upsert by **natural keys** (see [§3](#3-draft-entity-list-confirmed-2026-09-10)). Same `as_of` + ex-date + type updates; a new `as_of` inserts.
- **No full re-seed on boot.** Warm disk / warm Postgres: densify missing families or changed fixture fingerprints only. `SEED_FORCE_FULL=true` is intentional-only (OOM risk on Starter; worse at 32k rows).
- **Weekly scrape:** locked target is **Sunday 6:00 America/Chicago** for estimates **and** NAV.  
  **Current Action** (`.github/workflows/weekly-ingest.yml`) is `0 14 * * 0` and `0 14 * * 1` (Sun + Mon 14:00 UTC ≈ **9:00 CT** CDT). Align the cron at implementation — **do not change the live workflow in this spike.**  
  After cutover the Action should write the **same** Postgres (external URL + psycopg3). Today it cannot see `/var/data`.

### 2.4 Hero bar for every fund

Website hero (API surfaces; UI owns layout) for each in-book fund:

| Slot | Source of truth | Missing behavior |
|---|---|---|
| 5-year paid history | `distribution_estimates` where `publication_stage` in `final`/`paid`, `amount_unit=per_share` | Undisclosed for that year — never $0 |
| Weekly NAV | `fund_navs.nav_per_share` on `GET /funds` | null — never invented |
| Dist-day NAV | `fund_nav_history` joined on ex/payable date | null — never use weekly NAV for a past day |
| Category | `app/categories.py` (in-process; **not a table**) | null — never invented |
| Estimates when published | unpaid prelim/updated with future ex/payable → `estimate_announced` | else **Awaiting Estimate** |

There is **no `funds` table**. A “fund” is `COUNT(DISTINCT fund_identifier)` over `distribution_estimates`. Do not add a funds table at cutover (product change; ping Scale).

### 2.5 Schema freeze (summary)

Densify stays on **SQLite** until cutover. Full protocol (verbatim agreement + mapping): [§5](#5-schema-freeze). Breaking Postgres-only type/PK changes are called out in [§6.1](#61-proposed-table--type-changes).

---

## 3. Draft entity list (confirmed 2026-09-10)

**Confirmed (2026-09-10)** by Data | Engineering — all §3 entities/keys OK against live ingest.

Surrogate `id` values are `VARCHAR(36)` UUID text — **not** the upsert identity.

Logical names used in freeze pings (`funds`, `distributions`, `fund_navs`, seed paths) map to the physical tables below.

### 3.1 `distribution_estimates` — logical **distributions** (+ derived **funds**)

**What:** One published tax-character line (income, ST/LT, QDI $/share, ROC, …).  
**Derived fund:** latest row per `fund_identifier` (`row_number` in `search_funds`). Never a separate funds row.

| | |
|---|---|
| Surrogate PK | `id` |
| **Natural / upsert key** | `upsert_key` = `make_upsert_key`: `family\|ident\|share_class\|estimate_type\|as_of\|ex_date` (lowercased family/ident/class; ISO dates or empty) |
| Unique | `uq_distribution_upsert_key` (`upsert_key`) |
| Identity fields | `fund_family`, `fund_identifier` (ticker or slugified name; Class A alias may replace name), `ticker`, `share_class`, `estimate_type`, `as_of`, `ex_date` |
| Amounts | `amount` / `amount_min` / `amount_max` `Numeric(18,6)` — **0 allowed**; null = unknown |
| Unit | `amount_unit`: `per_share` \| `percent_of_nav` (bare `percent` is not ingested). **Load-bearing** for Website $ vs % — preserve exactly. |
| Stage | `publication_stage`: `preliminary_estimate` / `updated_estimate` / `final` / `paid`. **Load-bearing** with `amount_unit` for Website $ vs % rules — preserve exactly. |
| Dist-day NAV (API) | Response fields `nav_on_distribution_day`, `nav_on_distribution_day_as_of`, `nav_on_distribution_day_source` — joined from `fund_nav_history`, **not** stored on this table. Migrate must keep exposing them on dist rows. |
| Audit | `raw_payload` JSON — **not selected on Search** |
| Quality | `needs_review`, `review_reason`, `data_quality_flags` |

**Indexes (keep names on Postgres):**

| Index | Columns | Role |
|---|---|---|
| `ix_dist_ticker` | `ticker` | #118 exact ticker Search |
| `ix_dist_fund_identifier` | `fund_identifier` | #118 + lookup |
| `ix_dist_fund_name` | `fund_name` | name Search (btree; leading-wildcard still scans) |
| `ix_dist_family` | `fund_family` | family filter |
| `ix_dist_publication_stage` | `publication_stage` | live-estimate / lookback |
| `ix_dist_estimate_type` | `estimate_type` | type filter |
| `ix_dist_as_of` | `as_of` | history / YoY |
| `ix_dist_ex_date` | `ex_date` | dist-day join |
| `ix_dist_fund_search` | `ticker, fund_identifier, fund_name, fund_family, as_of, ingested_at, id` | covering index — avoids `raw_payload` table scan |

**Do not change `make_upsert_key` during migration.** A new publication `as_of` is a new row; the same document updates in place.

### 3.2 `fund_navs` — logical **fund_navs** (weekly)

| | |
|---|---|
| Surrogate PK | `id` |
| **Natural key** | `ticker` (unique `uq_fund_nav_ticker`) |
| Payload | `nav_per_share` `Numeric(18,6)` **> 0** in writer (`nav.py` rejects ≤0); `nav_as_of`; `source` |
| Indexes | `ix_nav_ticker`, `ix_nav_fund_identifier`, `ix_nav_as_of` |

Hero weekly NAV. Live % of NAV and live dist-$ use this print.

### 3.3 `fund_nav_history` — dist-day NAV

| | |
|---|---|
| Surrogate PK | `id` |
| **Natural key** | `(ticker, nav_as_of)` unique `uq_fund_nav_history_ticker_as_of` |
| Indexes | `ix_nav_hist_ticker_as_of` (`ticker`, `nav_as_of`) |

Historical % of NAV. Join: last print with `nav_as_of ≤ distribution_day` and ≥ day−7. Missing → null.

### 3.4 `seed_family_state` — seed path

| | |
|---|---|
| **Natural / PK** | `family_slug` |
| Payload | `fixture_fingerprint` (sha256 of fixture names/sizes/mtimes), `updated_at` |

Boot densify: 0 rows for a family → ingest; fingerprint change → ingest; warm + same fingerprint → skip. **No full rebuild.**

### 3.5 `ingest_runs`

| | |
|---|---|
| Surrogate PK | `id` |
| **Natural (soft)** | `(fund_family, started_at)` — not unique; one row per run |
| Indexes | `ix_ingest_family_started` (`fund_family`, `started_at`) |
| Payload | `mode`, `status`, counts, `source_urls` JSON |

### 3.6 `ticker_requests`

| | |
|---|---|
| Surrogate PK | `id` |
| **Natural (soft)** | `ticker` — **not unique** (repeat submits allowed; statuses `queued` / `search_issuer` / `matched` / …) |
| Indexes | `ix_ticker_request_status`, `ix_ticker_request_ticker`, `ix_ticker_request_created` |

Website Add-to-universe. Never invents amounts.

### 3.7 `coverage_gaps`

| | |
|---|---|
| Surrogate PK | `id` |
| **Natural (soft)** | append-only advisor miss (`ticker` / `fund_name` / `fund_family` + `created_at`) — no unique |
| Indexes | `ix_gap_created` |

### 3.8 Not a table (hero still needs them)

| Logical entity | Where | Natural key |
|---|---|---|
| **Fund** (hero identity) | Derived from `distribution_estimates.fund_identifier` | `fund_identifier` (plus display `ticker`) |
| **Category** | `app/categories.py` map | ticker / identifier / name / family → category string or null |

Adding either as a real table is a **ping-required** product change, not a cutover requirement.

Local dump of physical columns/indexes: `python3 scripts/schema_inventory.py`.

### 3.9 Non-blocking migrate constraints (confirmed)

Data | Engineering confirm — **do not block** densify or this spike. Implementation must honor:

1. **Dist rows expose `nav_on_distribution_day*`.** `GET /distributions` and illustrate attach `nav_on_distribution_day`, `nav_on_distribution_day_as_of`, `nav_on_distribution_day_source` (join from `fund_nav_history` on ex/payable; null if unknown). These are **API fields**, not columns on `distribution_estimates`. Migrate must **preserve that exposure** even though history lives in `fund_nav_history`. Do not drop the join, the history table, or the response fields. Do not substitute weekly `fund_navs` for a past distribution day.
2. **`publication_stage` + `amount_unit` are load-bearing** for Website $ vs % rules. Preserve enum values exactly (`per_share` vs `percent_of_nav`; stages `preliminary_estimate` / `updated_estimate` / `final` / `paid`). Do not remap, merge, or drop them in Alembic or the copy.
3. **Soft freeze tip** is still post-#117/#118 on `cursor/fund-distribution-ingest-api-85ed`. Densify remains **additive-only** (new rows/families, category/NAV/history fills).

---

## 4. Inventory (verified in repo + live `/health` / `/funds`)

### 4.1 Live book snapshot (2026-09-10, public GET only)

| Metric | Value |
|---|---|
| `GET /health` | `status=ok`, `db=ok`, `seed=complete`, 113 registered families |
| Unique funds (`GET /funds?limit=1`) | **5,614** |
| Distribution rows (`GET /distributions?limit=1`) | **32,029** |
| 5-year lookback (`GET /coverage`.lookback_5y) | 4,046 book funds; **800** with 2021–2025 finals (**19.8%**) |
| Ticker Search `q=AGTHX` | HTTP 200 in **0.13s** |
| Name Search `q=Balanced` | HTTP 200 in **0.34s** |
| First page `GET /funds?limit=50` | HTTP 200 in **0.30s** |

README still says “a cold full book is ~11k rows.” That figure is **stale**. Densify waves (#99, #103, #105, #106, …) grew the stored book to ~32k rows. Do not use 11k for capacity, OOM, or copy-time estimates.

`SEED_FORCE_FULL=true` on Starter (512 MB) is still a documented OOM risk (#113). That risk is **higher** now, not lower.

### 4.2 SQLAlchemy engine (`app/db.py`)

| Item | Current behavior |
|---|---|
| Default URL | `sqlite:///./data/distributions.db` (`app/config.py`) |
| Render URL | `sqlite:////var/data/distributions.db` (`render.yaml`) |
| Vercel override | `sqlite:////tmp/distributions.db` if `VERCEL` and relative sqlite URL |
| File SQLite pool | **`NullPool`** — one connection per checkout. Comment: QueuePool + file SQLite deadlocks under concurrent `/funds`. |
| In-memory tests | `StaticPool` for `sqlite://` / `sqlite:///:memory:` |
| Postgres path today | No `poolclass` → SQLAlchemy default **`QueuePool`**, plus `pool_pre_ping=True`. **No `pool_size` / `max_overflow` / `pool_recycle` set.** |
| SQLite connect args | `check_same_thread=False`, `timeout=15.0` |
| SQLite PRAGMAs (connect event) | `foreign_keys=ON`; file only: `journal_mode=WAL`, `busy_timeout=15000`, `synchronous=NORMAL`, `temp_store=MEMORY` |
| Schema create | `Base.metadata.create_all` on boot — **no Alembic directory exists** |
| Additive SQLite patches | `_ensure_quality_columns` (`needs_review`, `review_reason`, `data_quality_flags`) and `_ensure_search_indexes` (`ix_dist_fund_identifier`, `ix_dist_publication_stage`, `ix_dist_fund_search`) via raw `ALTER` / `CREATE INDEX` |
| Lock retry | `read_with_lock_retry` — SQLite `locked`/`busy` only; used by `GET /funds` and `GET /funds/lookup` |

Tests that lock this in: `tests/test_seed_on_start.py` (`test_sqlite_file_uses_wal`, `test_sqlite_file_uses_null_pool`, `test_sqlite_search_indexes_exist`). `EXPLAIN QUERY PLAN` in `tests/test_funds_search_speed.py` is **SQLite-only**.

### 4.3 Models / tables (`app/models.py`)

Dialect-neutral SQLAlchemy 2.0 mappings. Types that need a Postgres decision are called out.

| Table | PK | Notable columns / constraints | Indexes |
|---|---|---|---|
| `distribution_estimates` | `id` `String(36)` UUID text | `upsert_key` unique; `Numeric(18,6)` amounts; `Date` tax dates; `JSON` `raw_payload` + `data_quality_flags`; `Boolean` `needs_review`; `DateTime(timezone=True)` `ingested_at` | family, ticker, fund_name, fund_identifier, publication_stage, estimate_type, as_of, ex_date, covering `ix_dist_fund_search` |
| `coverage_gaps` | UUID text | `Numeric(18,2)` holding; booleans for adapter flags | `ix_gap_created` |
| `ticker_requests` | UUID text | website ingest queue | status, ticker, created_at |
| `fund_navs` | UUID text | unique `ticker`; `Numeric(18,6)` NAV | ticker, fund_identifier, nav_as_of |
| `fund_nav_history` | UUID text | unique `(ticker, nav_as_of)` | `(ticker, nav_as_of)` |
| `seed_family_state` | `family_slug` | fixture fingerprint for boot densify | — |
| `ingest_runs` | UUID text | `JSON` `source_urls` | `(fund_family, started_at)` |

**Not in the DB:** Morningstar-style categories (`app/categories.py` in-process map). Category filter on `GET /funds` still materializes unique funds in Python when `category=` is set.

**SQLite-only SQL in app code:** PRAGMAs + the `_ensure_*` ALTERs (SQLite `BOOLEAN NOT NULL DEFAULT 0` / `JSON`). Queries themselves use SQLAlchemy (`ilike`, `row_number`, `nulls_last`, `count(distinct)`). Those compile on Postgres. Name Search still uses leading-wildcard `ILIKE '%…%'` — fine on both; **not indexable** without `pg_trgm` on Postgres.

### 4.4 Boot / seed / paths

| Knob | Where | Live Blueprint value |
|---|---|---|
| `SEED_ON_START` | `app/config.py`, `app/main.py` lifespan | `true` — background thread after `init_db()` |
| `SEED_FORCE_FULL` | env + settings | `false` — warm `/var/data` densifies missing families / changed fixture files only |
| SQLite dir create | `app/main.py` `_ensure_sqlite_dir`, `app/cli.py` `_ensure_db` | mkdir parent of sqlite path |
| Fetch mode | `FETCH_MODE` | `fixture` on Render |
| Health | `GET /health` | liveness: 200 once HTTP listens; `health.db` may be `busy:…`; `health.seed` is `running` then `complete` |

Warm-disk densify (`app/services/boot_seed.py`) is the **supported** way the live book grows. A Manual Deploy must not rebuild ~32k rows.

### 4.5 Render / Docker / start command

**`render.yaml` (live Blueprint shape):**

- Service `aftertax-data-api`, `runtime: docker`, `plan: starter` (512 MB / 0.5 CPU)
- Disk `aftertax-data`, mount **`/var/data`**, **1 GB**
- `DATABASE_URL=sqlite:////var/data/distributions.db`
- `WEB_CONCURRENCY=1` (comment: multiple workers on one SQLite file → locks / 502s)
- `healthCheckPath: /health`
- CORS + category-outlier knobs

**`Dockerfile`:**

```
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WEB_CONCURRENCY:-1}
```

Binds `0.0.0.0:$PORT` (Render-correct). Default workers = 1.

**`docker-compose.yml`:** local SQLite volume `dist-data` → `/app/data`. No Postgres service today.

**Image deps (`requirements.txt`):** FastAPI / uvicorn / SQLAlchemy / pydantic / httpx / bs4 / lxml. **No Postgres driver in the default image.** `pyproject.toml` optional extra: `postgres = ["psycopg[binary]>=3.2.0"]` (psycopg3).

### 4.6 Weekly ingest + driver mismatch (hypothesis verified in files)

`.github/workflows/weekly-ingest.yml`:

- If repo secret `DATABASE_URL` is set → install **`psycopg2-binary`** and use that URL.
- Else → `sqlite:///./data/distributions.db` on the GitHub runner (ephemeral).

README / `.env.example` / `pyproject.toml` document **`postgresql+psycopg://`** (psycopg3). The workflow installs **psycopg2**. SQLAlchemy URLs:

| URL | Driver |
|---|---|
| `postgresql+psycopg://…` | psycopg3 — matches app docs |
| `postgresql://…` or `postgresql+psycopg2://…` | psycopg2 — matches the Action today |

**Hypothesis (not contradicted by the repo; Render MCP was unauthorized so Dashboard secrets were not inspected):** the weekly Action is **not** updating the live Render SQLite disk. Production durability is the Starter disk + fixture densify on boot. After Postgres, the Action *can* write the same database — but only if the driver and URL dialect are aligned and the secret is the **external** URL (`sslmode=require`).

Locked coordination wants **Sunday 6:00 CT** (estimates + NAV). The Action today is Sun+Mon 14:00 UTC ≈ 9:00 CT. Treat that as an implementation alignment item, not a live workflow edit in this spike.

### 4.7 Migrations state

- **No `alembic/`**, no `alembic.ini`.
- Production schema = `create_all` + two `_ensure_*` helpers aimed at existing SQLite disks.
- README already says: “For production, swap that for Alembic migrations.”

The Action schedule is **not** the locked Sunday 6:00 CT target (see [§2.3](#23-efficient-ingest)). Align later; do not edit the live workflow in this spike.

---

## 5. Schema freeze

Locked agreement with Data | Engineering. **SPIKE ONLY** — this section documents the protocol; it does not migrate production.

Densify **stays on SQLite** until cutover. Soft-freeze tip is still post-#117/#118 on `cursor/fund-distribution-ingest-api-85ed`. Densify remains **additive-only**.

### 5.1 Agreement (verbatim)

- **Soft freeze now:** spike inventories/drafts against tip of `cursor/fund-distribution-ingest-api-85ed` (post-#117/#118). Densify stays **additive-only** (new rows/families, category/NAV/history fills). Engineering **pings Scale** before migrations that change columns/types/indexes on core tables: **funds**, **distributions**, **fund_navs**, **seed paths**.
- **Hard freeze when Eric greenlights cutover:** pause densify schema changes for **~24–48h** during migrate + dual-run; ingest may still **upsert into the frozen shape**.
- **No ping needed:** new distribution/NAV/category rows via existing upserts; weekly scrape.
- **Ping required:** new columns, renamed fields, dropping `raw_payload` reliance, seed-on-start behavior, worker/DB URL config.

### 5.2 Soft freeze (now → greenlight)

Densify is **additive-only**: new distribution/NAV/history rows, new families, category-map fills, lookback years. No column/type/index redesign on core entities.

**Core entities for ping** (logical name in the agreement → physical table):

| Logical (Data \| Eng) | Physical table(s) |
|---|---|
| funds | derived from `distribution_estimates.fund_identifier` (**no `funds` table**) |
| distributions | `distribution_estimates` |
| fund_navs | `fund_navs` + `fund_nav_history` |
| seed paths | `seed_family_state`, boot densify, `SEED_*` env |

Engineering **pings Scale** before any migration that changes columns, types, or indexes on those.

### 5.3 Hard freeze (when Eric greenlights cutover)

Pause densify **schema** changes for **~24–48 hours** during migrate + dual-run. Ingest may still **upsert into the frozen shape** (new rows / updated `upsert_key` documents). Then re-copy SQLite → Postgres (or replay ingest) before traffic moves.

### 5.4 No ping needed

- New distribution / NAV / category **rows** via existing upserts
- Weekly scrape (estimates + NAV) into the current keys
- Fixture HTML / parser / adapter densify that does not change the schema
- Soft-beta traffic on live SQLite

### 5.5 Ping Scale required

- New columns or renamed fields
- Dropping or changing `raw_payload` reliance (Search must keep it off the hot path; dropping the column is a product/audit change)
- Seed-on-start behavior (`SEED_ON_START` / `SEED_FORCE_FULL` / fingerprint rules)
- Worker / `DATABASE_URL` / disk / pool config (production Render)
- New first-class `funds` or `categories` table
- Changing `make_upsert_key` or unique keys on `fund_navs` / `fund_nav_history`

### 5.6 Frozen vs not frozen (copy validity)

**Frozen until cutover:**

- `upsert_key` algorithm and `uq_distribution_upsert_key`
- `fund_navs.ticker` unique; `fund_nav_history (ticker, nav_as_of)` unique
- `seed_family_state.family_slug` PK / fingerprint meaning
- Table/column renames or PK type change (native UUID = **breaking — do not**)
- Dropping `raw_payload` or `ix_dist_fund_search`
- Production `DATABASE_URL`, `WEB_CONCURRENCY`, disk mount, Render secrets
- `publication_stage` and `amount_unit` values (Website $ vs % — [§3.9](#39-non-blocking-migrate-constraints-confirmed))
- Dist-row API fields `nav_on_distribution_day*` (joined from `fund_nav_history`; not weekly NAV)

**Not frozen — keep going on SQLite:**

- Fixture / parser / adapter densify (5y lookback is 19.8%)
- `SEED_ON_START` warm-disk delta (not `SEED_FORCE_FULL`)
- Website contracts (`/funds`, `/illustrate`, `/performance`)
- Soft-beta traffic on the live SQLite API

**Re-copy rule:** any densify that lands on SQLite after the last copy must be re-copied (or replayed via `POST /ingest/fetch` against Postgres) before traffic moves.

---

## 6. Draft Postgres schema + migration approach

### 6.1 Proposed table / type changes

Keep the **same seven tables and unique keys** so a row-for-row copy is possible and densify upserts stay stable. See [§3](#3-draft-entity-list-confirmed-2026-09-10) (confirmed 2026-09-10).

| Current | Postgres recommendation | Breaking? | Why |
|---|---|---|---|
| `String(36)` UUID PKs | Keep `VARCHAR(36)` at cutover. Native `UUID` later only. | **Yes if native UUID now** — do not | Copy + every `id` rewrite. Ping required. |
| `sqlalchemy.JSON` | **`JSONB`** | **No** (dialect mapping) | Same SQLAlchemy attribute. Search still must not SELECT it (#118). |
| `Boolean` / `DEFAULT 0` | native `BOOLEAN` default `false` | **No** | SQLite `_ensure_*` SQL is not the PG path. |
| `Numeric(18,6)` / `Date` / `Text` | unchanged | **No** | Portable. **0 amounts allowed.** |
| `DateTime(timezone=True)` | `TIMESTAMPTZ` | **No** (dialect mapping) | Copy must preserve UTC. |
| Existing btree indexes | same names | **Yes if dropped/renamed** | Ticker path needs `ix_dist_ticker` / `ix_dist_fund_identifier` / `ix_dist_fund_search`. Extra `pg_trgm` = ping (index change). |
| Name `ILIKE '%q%'` | optional `pg_trgm` GIN | Additive; **ping** | Not required for ticker path. |
| Categories | stay in Python | **Yes if new table** | Product change; ping Scale. |
| `make_upsert_key` | unchanged | **Yes if changed** | Idempotency contract. Freeze. |

**Breaking — do not do at cutover:** native UUID PKs, drop `raw_payload`, change `upsert_key`, add `funds`/`categories` tables, `SEED_FORCE_FULL` on production boot.

Do **not** change `upsert_key` / `make_upsert_key` during migration. That is the idempotency contract.

### 6.2 Alembic plan

1. Add Alembic; `env.py` reads `settings.database_url`.
2. Autogenerate **revision 001** = current models (seven tables + indexes + uniques). Review by hand (JSONB, timestamptz, boolean defaults).
3. Production / preview Postgres boot: `alembic upgrade head` in a **pre-deploy command** (cancels the deploy if it fails). Do not run migrations from random uvicorn workers.
4. SQLite local + pytest: keep `create_all` + `_ensure_*` until SQLite is retired, **or** run Alembic against file SQLite in tests (second choice; more moving parts).
5. After cutover, new columns go through Alembic only. Delete `_ensure_*` once no SQLite disk remains.

Suggested layout (implementation PR, not this spike):

```
alembic.ini
alembic/env.py
alembic/versions/0001_initial_postgres.py
```

### 6.3 Engine behavior after Postgres

| URL | Pool | Notes |
|---|---|---|
| file SQLite (beta / local) | keep **NullPool** + WAL PRAGMAs + `WEB_CONCURRENCY=1` | Soft beta unchanged. |
| `postgresql+psycopg://` | **QueuePool** `pool_size=5`, `max_overflow=5`, `pool_pre_ping=True`, `pool_recycle=1800` | Drop NullPool. 2 workers × 10 = 20 connections; Basic plans allow 100. |
| sqlite memory tests | StaticPool | unchanged |

Install `psycopg[binary]` in the Docker image (or `requirements.txt`), not only the optional extra. Align the weekly Action on **psycopg3** + `postgresql+psycopg://`.

Render internal URLs are typically `postgres://…`. SQLAlchemy 2 needs an explicit driver: rewrite `postgres://` / `postgresql://` → `postgresql+psycopg://` at config time. Do not store secrets in git.

### 6.4 Data copy strategy

~32k estimate rows + NAV / gaps / ticker_requests / seed fingerprints is a **small** database. Prefer a **controlled Python copy** over a blind SQL dump.

| Method | Use? | Notes |
|---|---|---|
| **SQLAlchemy two-engine copy** (recommended) | Yes | Same models; batch insert; normalize bool / JSON / timestamptz. Runs from a laptop or a one-shot job against a **snapshot**, never against live writes as the only copy. |
| **pgloader** SQLite → Postgres | Acceptable backup | Test JSON/bool mapping on a copy first. |
| `sqlite3 .dump` / `pg_restore` | No | SQLite SQL is not Postgres SQL. |
| Live dual-write in the API | No for v1 | Extra complexity; densify still lands on SQLite until cutover. |

Verification after copy (do not invent amounts — compare stored values):

- Counts per table
- `COUNT(DISTINCT fund_identifier)` vs live `/funds` total (5,614 on probe day)
- Checksum of `(upsert_key, amount, as_of, publication_stage)` for a fixture set (AGTHX, FBGRX, DODIX, VFIAX, SGENX, …)
- Replay `GET /funds?q=AGTHX`, `q=Balanced`, `GET /funds/lookup?ticker=ZZZZZ` (404), `GET /coverage` lookback_5y totals

### 6.5 Dual-run sketch

```
Soft beta (now)          Dual-run (after greenlight)         Official launch
──────────────           ──────────────────────────          ──────────────
Render SQLite disk  -->  SQLite still serves prod      -->   Postgres internal URL
WEB_CONCURRENCY=1        Preview API + empty-then-copied PG  WEB_CONCURRENCY=2
Densify waves OK         Densify continues on SQLite         Re-copy, then cut over
Weekly Action isolated   Preview validates Search            Action → same PG (external)
```

Freeze / ping rules: [§5](#5-schema-freeze). Do not cut over on a stale snapshot.

---

## 7. Draft Render plan (do not apply)

Render MCP `list_workspaces` returned **unauthorized** in this environment. Live settings below are from `render.yaml` + public HTTP + README. Confirm in Dashboard before any future implementation PR.

### 7.1 Recommended first Postgres (lean)

| Choice | Recommendation | Why |
|---|---|---|
| Instance | **Basic-1gb** (~$19/mo, 0.5 CPU, 1 GB RAM, 100 connections) | 32k rows + JSONB payloads + weekly ingest. **Basic-256mb ($6)** is the leaner option only after a local copy proves working-set + `EXPLAIN` stay comfortable. Free Postgres expires in 30 days — not for launch. |
| Storage | **1 GB included** (then $0.30/GB-mo) | Book is tens–hundreds of MB, not GB. Cannot shrink later. |
| Region | **Same region as `aftertax-data-api`** | Internal URL, no TLS hop. |
| Version | Current Render default PG 16+ | Immutable after create. |
| HA / replicas | **Off** at launch | Cost; not needed for this size. |
| Pooler | **None** (Render has no managed pooler) | App QueuePool is enough. Add PgBouncer only if approaching 100 connections or many instances. |

Do **not** point production at this database until the cutover checklist is executed.

### 7.2 Web service + workers

| Setting | Soft beta (keep) | Official launch (proposed) |
|---|---|---|
| Plan | Starter $7 / 512 MB | **Stay Starter** if 2 workers + delta seed stay off OOM; **Standard $25 / 2 GB** if boot or workers RSS is tight |
| Instances | 1 (disk forces this) | **1** at cutover. Disk must be removed before a second instance is legal. |
| `WEB_CONCURRENCY` | `1` | **`2`** on Starter; **`2–4`** on Standard |
| Disk | `/var/data` 1 GB | **Detach after cutover** — unlocks zero-downtime deploys + later horizontal scale |
| `DATABASE_URL` | sqlite file on disk | **Internal** `postgresql+psycopg://…` via `fromDatabase.connectionString` + rewrite |
| `SEED_ON_START` | `true` (delta) | Keep `true`; densify writes Postgres. **`SEED_FORCE_FULL=false`** |
| Health | `/health` | unchanged |

Starter + 2 workers is the lean launch. If RSS after two uvicorn processes + SQLAlchemy pools is close to 512 MB, bump the **web** plan, not Postgres RAM.

### 7.3 Env vars (implementation PR — not this spike)

```
DATABASE_URL=<internal fromDatabase connectionString, rewritten to postgresql+psycopg>
WEB_CONCURRENCY=2
SEED_ON_START=true
SEED_FORCE_FULL=false
FETCH_MODE=fixture          # until weekly Action writes the same PG
SQLALCHEMY_POOL_SIZE=5      # optional; can hardcode in db.py
SQLALCHEMY_MAX_OVERFLOW=5
```

Drop SQLite-only assumptions when URL is Postgres: no WAL PRAGMAs, no NullPool, no `_ensure_sqlite_dir`.

GitHub Action secret (later): **external** URL with `sslmode=require`, same logical database. Never commit it.

### 7.4 Optional Redis / CDN — not justified for launch

| Add-on | Launch? | Reason |
|---|---|---|
| Render Key Value (Redis/Valkey) | **No** | Search is already 0.13–0.34s after #118. Postgres indexes + optional `pg_trgm` fix the remaining name-scan. Redis ($10 Starter) is a third moving part before official traffic exists. Revisit if multi-instance + hot tickers show cacheable p95. |
| Edge/CDN cache on the API | **No** | `/funds`, `/illustrate`, `/coverage` are request-specific and must not serve stale estimates. Website already sits on Vercel. |

### 7.5 Example Blueprint

See [`render.postgres-launch.example.yaml`](./render.postgres-launch.example.yaml). **Do not apply it to the live service.** It is a preview/staging sketch for the implementation PR.

---

## 8. Rough monthly cost (Render list prices — estimates)

Prices from [render.com/pricing](https://render.com/pricing) as of **2026-09-10**. Prorated per second; bandwidth / build minutes extra. **Not a quote.**

### Current soft beta (as designed in `render.yaml`)

| Line | List (est.) |
|---|---|
| Hobby workspace | $0 |
| Web Starter | $7 |
| Persistent disk 1 GB × $0.25/GB | $0.25 |
| **Total** | **~$7 / mo** |

### Recommended official-launch lean stack

| Line | List (est.) |
|---|---|
| Hobby workspace | $0 |
| Web Starter (2 workers, 1 instance) | $7 |
| Postgres Basic-1gb + 1 GB storage | $19 |
| Disk removed after cutover | $0 |
| Redis / CDN | $0 |
| **Total** | **~$26 / mo** |

### If Starter OOMs with 2 workers

| Line | List (est.) |
|---|---|
| Web Standard | $25 |
| Postgres Basic-1gb | $19 |
| **Total** | **~$44 / mo** |

### Lean-extreme alternative (only after a measured copy)

Web Starter $7 + Postgres **Basic-256mb** $6 ≈ **$13 / mo**. Reject if `EXPLAIN` / ingest / connection spikes look tight.

### Later (not launch)

| Add | Est. |
|---|---|
| Second web instance (after disk removal) | +$7 (Starter) or +$25 (Standard) |
| Key Value Starter | +$10 |
| Pro workspace (autoscaling, etc.) | +$25 workspace — **not needed** for one API |
| Postgres Pro / HA / replicas | **not needed** at this book size |

---

## 9. Eng-day breakdown (after Eric greenlights)

Implementation is a **follow-up PR series**, not this spike. Calendar-time estimates aside: this is **about 6–8 focused eng-days**.

| # | Task | Days | Notes |
|---|---|---|---|
| 1 | Dialect-aware engine + `psycopg[binary]` in image + URL rewrite | 1 | NullPool/WAL only for SQLite; QueuePool knobs for PG. No prod env change. |
| 2 | Alembic 0001 + pre-deploy `upgrade head` on a **preview** service | 1 | Keep SQLite `create_all` for pytest. |
| 3 | Local `docker compose` Postgres + pytest on PG (skip SQLite-only EXPLAIN) | 1 | Gate Search / upsert / seed / concurrent `/funds`. |
| 4 | Copy script (SQLAlchemy) + count/checksum verify | 1 | Snapshot from `/var/data` (Eric SSH or disk copy) — **not** a live cutover. |
| 5 | Preview Render: Basic-1gb + preview web, internal URL, `WEB_CONCURRENCY=2` | 1 | Replay Search / coverage / illustrate against copied book. |
| 6 | Optional `pg_trgm` only if name Search regresses; pool/RSS tune | 0.5 | Skip if ticker + page latency stay ≤ current. |
| 7 | Weekly Action → psycopg3 + external URL; README / Blueprint example → real yaml | 0.5–1 | Still no prod cutover until checklist. |
| 8 | Cutover rehearsal + rollback drill (disk still mounted, URL flip ready) | 0.5–1 | Execute only after greenlight. |

**Out of scope for those days:** inventing estimates, relaxing [§2](#2-locked-data--engineering-coordination-do-not-relax) accuracy rules, category-table migration, Redis, multi-region, HA Postgres, changing Website contracts.

---

## 10. Dual-run / cutover checklist (execute later — not now)

Print and tick only after implementation PRs land and Eric says go.

### Dual-run (preview)

- [ ] Create Postgres **Basic-1gb** in the **same region** as the API. Do not attach it to production `DATABASE_URL` yet.
- [ ] Stand up a **preview** web service (or PR preview) with internal `DATABASE_URL`, `WEB_CONCURRENCY=2`, no prod DNS.
- [ ] `alembic upgrade head` on preview.
- [ ] Copy a **frozen snapshot** of `/var/data/distributions.db` (service SSH / disk file). Production keeps serving SQLite.
- [ ] Verify counts + fixture checksums + Search / lookup / coverage / illustrate.
- [ ] Accuracy sample: AGTHX `awaiting_estimate` vs a live `estimate_announced` ticker; lookback missing years stay Undisclosed (not $0); historical `%` uses dist-day NAV; live `%` uses weekly NAV; announced `amount=0` still stores if present.
- [ ] Dist rows still expose `nav_on_distribution_day*` (joined from `fund_nav_history`, not weekly NAV). `publication_stage` + `amount_unit` values unchanged.
- [ ] Watch preview RSS and PG `active_connections` under an 8-way `/funds` burst.
- [ ] Leave production `WEB_CONCURRENCY=1` and sqlite URL untouched.

### Cutover window (short; densify paused or immediately re-copied)

- [ ] Announce a short freeze on fixture densify / Manual Deploy that would rewrite the book.
- [ ] Final copy (or replay ingest) so Postgres matches SQLite.
- [ ] Pre-deploy migrations already at head.
- [ ] Set production `DATABASE_URL` to **internal** rewritten URL.
- [ ] Set `WEB_CONCURRENCY=2` (or 2–4 on Standard).
- [ ] Confirm NullPool/WAL path is not used (app branch with dialect-aware engine).
- [ ] Health 200, `GET /funds?q=AGTHX` 200, lookup miss 404, coverage totals match snapshot.
- [ ] Point GitHub `DATABASE_URL` secret at **external** URL; run a dry `workflow_dispatch` after DNS/traffic is stable — or keep Action off until the first weekly slot.
- [ ] **Then** detach `/var/data` (enables zero-downtime + later scale-out). Keep the old file until one successful week.
- [ ] Only after disk detach: consider `numInstances: 2` if one instance + 2 workers is not enough.

### Rollback

- [ ] Flip `DATABASE_URL` back to `sqlite:////var/data/distributions.db` **only if the disk is still mounted**.
- [ ] Set `WEB_CONCURRENCY=1`.
- [ ] If disk was already detached, restore from the kept SQLite file or PG backup — decide **before** detach which rollback you still have.
- [ ] Do not delete the Postgres instance until SQLite rollback is abandoned.

### Explicit non-goals of this spike

- No production Render setting, secret, or traffic change.
- No fund/distribution amount invention or “estimated coverage %” beyond live `/coverage` lookback_5y.
- No Redis/CDN purchase.
- No apply of `docs/render.postgres-launch.example.yaml`.

---

## 11. Implementation files (greenlit PR)

| File | Role |
|---|---|
| `docs/postgres-scale-spike.md` | This plan (coordination rules, **confirmed** entity list, freeze, Render/cost). |
| `docs/CUTOVER.md` | Dual-run + Manual Deploy checklist. Eric-owned production flips. |
| `docs/render.postgres-launch.example.yaml` | Proposed Blueprint. **Not wired to the live service.** |
| `alembic/` | Revision `0001_initial` — seven tables + indexes. Pre-deploy: `alembic upgrade head`. |
| `scripts/copy_sqlite_to_postgres.py` | SQLAlchemy two-engine copy + count/checksum. Never invents amounts. |
| `scripts/schema_inventory.py` | Prints SQLAlchemy tables/indexes locally. Does not connect to Render. |

No production `DATABASE_URL` rewrite in live `render.yaml`.

---

## 12. Open items for Eric

1. ~~Data | Engineering confirm §3 entity list~~ — **Confirmed (2026-09-10)**; honor [§3.9](#39-non-blocking-migrate-constraints-confirmed).
2. ~~Greenlight **Basic-1gb**~~ — **Greenlit.** Create the instance at cutover; do not attach production `DATABASE_URL` until [CUTOVER.md](./CUTOVER.md).
3. ~~Stay **Starter + 2 workers**~~ — **Greenlit.** Bump web to Standard only if preview RSS OOMs.
4. Snapshot `/var/data/distributions.db` (SSH / disk file) — this agent must not touch live disks.
5. Point weekly ingest at the shared Postgres **external** URL at cutover (recommended) or stay fixture-only until later.
6. Align weekly cron to locked **Sunday 6:00 CT** (today Sun+Mon 14:00 UTC ≈ 9:00 CT) — **follow-up after cutover.** Action driver is now psycopg3; schedule unchanged so soft beta does not break.
7. ICI parser drops announced `$0` (`app/sources/ici.py`) while the locked rule says keep $0 — Data decision; not a scale cutover blocker.
8. Confirm workspace is Hobby (assumed from lean ops). Pro workspace ($25) is not required for this plan.
