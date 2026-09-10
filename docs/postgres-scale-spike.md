# SPIKE ONLY — Postgres + multi-worker scale plan

**Status:** design notes. Do **not** migrate production, change live Render env, cut traffic, or apply the example Blueprint to `aftertax-data-api`.

**Audience:** Eric (greenlight before any implementation).  
**Source branch:** `cursor/fund-distribution-ingest-api-85ed` @ `60aefca` (includes #117 / #118).  
**Live API probed this spike (2026-09-10, read-only):** https://aftertax-data-api.onrender.com  
**This PR does not invent fund or distribution amounts.**

Friends / soft beta can stay on SQLite. Cutover is for official public / paid scale — after this plan is approved and the implementation tickets below are done.

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

## 2. Inventory (verified in repo + live `/health` / `/funds`)

### 2.1 Live book snapshot (2026-09-10, public GET only)

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

### 2.2 SQLAlchemy engine (`app/db.py`)

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

### 2.3 Models / tables (`app/models.py`)

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

### 2.4 Boot / seed / paths

| Knob | Where | Live Blueprint value |
|---|---|---|
| `SEED_ON_START` | `app/config.py`, `app/main.py` lifespan | `true` — background thread after `init_db()` |
| `SEED_FORCE_FULL` | env + settings | `false` — warm `/var/data` densifies missing families / changed fixture files only |
| SQLite dir create | `app/main.py` `_ensure_sqlite_dir`, `app/cli.py` `_ensure_db` | mkdir parent of sqlite path |
| Fetch mode | `FETCH_MODE` | `fixture` on Render |
| Health | `GET /health` | liveness: 200 once HTTP listens; `health.db` may be `busy:…`; `health.seed` is `running` then `complete` |

Warm-disk densify (`app/services/boot_seed.py`) is the **supported** way the live book grows. A Manual Deploy must not rebuild ~32k rows.

### 2.5 Render / Docker / start command

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

### 2.6 Weekly ingest + driver mismatch (hypothesis verified in files)

`.github/workflows/weekly-ingest.yml`:

- If repo secret `DATABASE_URL` is set → install **`psycopg2-binary`** and use that URL.
- Else → `sqlite:///./data/distributions.db` on the GitHub runner (ephemeral).

README / `.env.example` / `pyproject.toml` document **`postgresql+psycopg://`** (psycopg3). The workflow installs **psycopg2**. SQLAlchemy URLs:

| URL | Driver |
|---|---|
| `postgresql+psycopg://…` | psycopg3 — matches app docs |
| `postgresql://…` or `postgresql+psycopg2://…` | psycopg2 — matches the Action today |

**Hypothesis (not contradicted by the repo; Render MCP was unauthorized so Dashboard secrets were not inspected):** the weekly Action is **not** updating the live Render SQLite disk. Production durability is the Starter disk + fixture densify on boot. After Postgres, the Action *can* write the same database — but only if the driver and URL dialect are aligned and the secret is the **external** URL (`sslmode=require`).

### 2.7 Migrations state

- **No `alembic/`**, no `alembic.ini`.
- Production schema = `create_all` + two `_ensure_*` helpers aimed at existing SQLite disks.
- README already says: “For production, swap that for Alembic migrations.”

---

## 3. Draft Postgres schema + migration approach

### 3.1 Proposed table / type changes

Keep the **same seven tables and unique keys** so a row-for-row copy is possible and densify upserts stay stable.

| Current | Postgres recommendation | Why |
|---|---|---|
| `String(36)` UUID PKs | Keep as `VARCHAR(36)` for copy simplicity. Optional later: native `UUID`. | Avoids rewrite of every FK-less id during cutover. |
| `sqlalchemy.JSON` | **`JSONB`** (`JSONB` TypeDecorator or `postgresql.JSONB`) | `raw_payload` is audit HTML/JSON; JSONB is smaller / indexable if we ever query it. Search must keep **not** selecting this column (#118). |
| `Boolean` / `DEFAULT 0` | native `BOOLEAN` default `false` | `_ensure_quality_columns` SQLite SQL is not the PG path. |
| `Numeric(18,6)` / `Date` / `Text` | unchanged | Portable. |
| `DateTime(timezone=True)` | `TIMESTAMPTZ` | Copy must preserve UTC. SQLite stores text. |
| Existing btree indexes | recreate with the same names | Ticker equality path (#118) must keep hitting `ix_dist_ticker` / `ix_dist_fund_identifier` / covering `ix_dist_fund_search`. |
| Name / family `ILIKE '%q%'` | **optional** `pg_trgm` GIN on `fund_name`, `fund_family` | Only if name Search p95 is a problem after cutover. Not required for ticker path. |
| Categories | stay in Python for v1 | Moving them into SQL is a product change, not a cutover requirement. |

Do **not** change `upsert_key` / `make_upsert_key` during migration. That is the idempotency contract.

### 3.2 Alembic plan

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

### 3.3 Engine behavior after Postgres

| URL | Pool | Notes |
|---|---|---|
| file SQLite (beta / local) | keep **NullPool** + WAL PRAGMAs + `WEB_CONCURRENCY=1` | Soft beta unchanged. |
| `postgresql+psycopg://` | **QueuePool** `pool_size=5`, `max_overflow=5`, `pool_pre_ping=True`, `pool_recycle=1800` | Drop NullPool. 2 workers × 10 = 20 connections; Basic plans allow 100. |
| sqlite memory tests | StaticPool | unchanged |

Install `psycopg[binary]` in the Docker image (or `requirements.txt`), not only the optional extra. Align the weekly Action on **psycopg3** + `postgresql+psycopg://`.

Render internal URLs are typically `postgres://…`. SQLAlchemy 2 needs an explicit driver: rewrite `postgres://` / `postgresql://` → `postgresql+psycopg://` at config time. Do not store secrets in git.

### 3.4 Data copy strategy

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

### 3.5 Dual-run and what stays frozen on SQLite

```
Soft beta (now)          Dual-run (after greenlight)         Official launch
──────────────           ──────────────────────────          ──────────────
Render SQLite disk  -->  SQLite still serves prod      -->   Postgres internal URL
WEB_CONCURRENCY=1        Preview API + empty-then-copied PG  WEB_CONCURRENCY=2
Densify waves OK         Densify continues on SQLite         Re-copy, then cut over
Weekly Action isolated   Preview validates Search            Action → same PG (external)
```

**Frozen until cutover (so the copy stays valid):**

- `upsert_key` algorithm and unique constraint
- Table/column renames or PK type change
- Dropping `raw_payload` / search covering index
- Production `DATABASE_URL`, `WEB_CONCURRENCY`, disk mount, Render secrets

**Not frozen — keep going on SQLite:**

- Fixture / parser / adapter densify (5y lookback is 19.8%; waves can continue)
- `SEED_ON_START` warm-disk behavior
- Website contracts (`/funds`, `/illustrate`, `/performance`)
- Soft-beta traffic on the live SQLite API

**Re-copy rule:** any densify that lands on SQLite after the last copy must be **re-copied** (or replayed via `POST /ingest/fetch` against Postgres) before traffic moves. Do not cut over on a stale snapshot.

---

## 4. Draft Render plan (do not apply)

Render MCP `list_workspaces` returned **unauthorized** in this environment. Live settings below are from `render.yaml` + public HTTP + README. Confirm in Dashboard before any future implementation PR.

### 4.1 Recommended first Postgres (lean)

| Choice | Recommendation | Why |
|---|---|---|
| Instance | **Basic-1gb** (~$19/mo, 0.5 CPU, 1 GB RAM, 100 connections) | 32k rows + JSONB payloads + weekly ingest. **Basic-256mb ($6)** is the leaner option only after a local copy proves working-set + `EXPLAIN` stay comfortable. Free Postgres expires in 30 days — not for launch. |
| Storage | **1 GB included** (then $0.30/GB-mo) | Book is tens–hundreds of MB, not GB. Cannot shrink later. |
| Region | **Same region as `aftertax-data-api`** | Internal URL, no TLS hop. |
| Version | Current Render default PG 16+ | Immutable after create. |
| HA / replicas | **Off** at launch | Cost; not needed for this size. |
| Pooler | **None** (Render has no managed pooler) | App QueuePool is enough. Add PgBouncer only if approaching 100 connections or many instances. |

Do **not** point production at this database until the cutover checklist is executed.

### 4.2 Web service + workers

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

### 4.3 Env vars (implementation PR — not this spike)

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

### 4.4 Optional Redis / CDN — not justified for launch

| Add-on | Launch? | Reason |
|---|---|---|
| Render Key Value (Redis/Valkey) | **No** | Search is already 0.13–0.34s after #118. Postgres indexes + optional `pg_trgm` fix the remaining name-scan. Redis ($10 Starter) is a third moving part before official traffic exists. Revisit if multi-instance + hot tickers show cacheable p95. |
| Edge/CDN cache on the API | **No** | `/funds`, `/illustrate`, `/coverage` are request-specific and must not serve stale estimates. Website already sits on Vercel. |

### 4.5 Example Blueprint

See [`render.postgres-launch.example.yaml`](./render.postgres-launch.example.yaml). **Do not apply it to the live service.** It is a preview/staging sketch for the implementation PR.

---

## 5. Rough monthly cost (Render list prices — estimates)

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

## 6. Eng-day breakdown (after Eric greenlights)

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

**Out of scope for those days:** inventing estimates, category-table migration, Redis, multi-region, HA Postgres, changing Website contracts.

---

## 7. Dual-run / cutover checklist (execute later — not now)

Print and tick only after implementation PRs land and Eric says go.

### Dual-run (preview)

- [ ] Create Postgres **Basic-1gb** in the **same region** as the API. Do not attach it to production `DATABASE_URL` yet.
- [ ] Stand up a **preview** web service (or PR preview) with internal `DATABASE_URL`, `WEB_CONCURRENCY=2`, no prod DNS.
- [ ] `alembic upgrade head` on preview.
- [ ] Copy a **frozen snapshot** of `/var/data/distributions.db` (service SSH / disk file). Production keeps serving SQLite.
- [ ] Verify counts + fixture checksums + Search / lookup / coverage / illustrate.
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

## 8. Helper stubs in this PR

| File | Role |
|---|---|
| `docs/postgres-scale-spike.md` | This plan. |
| `docs/render.postgres-launch.example.yaml` | Proposed Blueprint. **Not wired to the live service.** |
| `scripts/schema_inventory.py` | Prints SQLAlchemy tables/indexes locally. Does not connect to Render. |

No cutover code, no production `DATABASE_URL` rewrite in `render.yaml`.

---

## 9. Open items for Eric

1. Greenlight **Basic-1gb** (~+$19) vs try **Basic-256mb** first on a preview copy.
2. Stay **Starter + 2 workers** vs budget **Standard** if boot RSS is scary.
3. Who can copy `/var/data/distributions.db` (SSH) for the snapshot — this agent must not touch live disks.
4. Whether weekly ingest should write the shared Postgres at cutover (recommended) or stay fixture-only until later.
5. Confirm workspace is Hobby (assumed from lean ops). Pro workspace ($25) is not required for this plan.
