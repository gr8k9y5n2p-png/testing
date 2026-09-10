# Postgres cutover checklist (Eric — Manual Deploy)

This branch prepares the **lean Postgres path**. It does **not** change production Render env, live secrets, or traffic.

Live Blueprint (`render.yaml`) stays **SQLite + `/var/data` + `WEB_CONCURRENCY=1`**.  
Gated launch sketch: [`render.postgres-launch.example.yaml`](./render.postgres-launch.example.yaml).  
Coordination / freeze: [`postgres-scale-spike.md`](./postgres-scale-spike.md).

**Never invent fund estimates.** Copy compares stored values only (null ≠ 0).

---

## Already in this PR (engineering)

- [x] Dialect-aware engine: file SQLite keeps NullPool + WAL; Postgres uses QueuePool `5` / overflow `5` / pre-ping / recycle `1800`
- [x] `postgres://` and `postgresql://` rewritten to `postgresql+psycopg://` at config time
- [x] `psycopg[binary]` + Alembic in `requirements.txt` / Docker image
- [x] Alembic `0001_initial` = seven tables + current indexes/uniques (JSONB on PG; `VARCHAR(36)` PKs)
- [x] SQLite `create_all` + `_ensure_*` kept for soft-beta / pytest
- [x] Local `docker compose --profile postgres` + documented `DATABASE_URL`
- [x] `scripts/copy_sqlite_to_postgres.py` + count/checksum verify
- [x] Weekly Action aligned to **psycopg3** (no schedule change — still Sun+Mon 14:00 UTC)
- [x] Example Blueprint + this checklist — **not** wired into live `render.yaml`

## Dual-run (preview — no prod DNS)

- [ ] Create Render Postgres **Basic-1gb** in the **same region** as `aftertax-data-api`. Do not attach it to production `DATABASE_URL`.
- [ ] Stand up a **preview** web service (or apply the example Blueprint as a *new* preview name). Internal `DATABASE_URL` + `WEB_CONCURRENCY=2`. No disk.
- [ ] Pre-deploy: `alembic upgrade head` (cancels the release if it fails).
- [ ] Snapshot `/var/data/distributions.db` (SSH / disk file). Production keeps serving SQLite.
- [ ] Copy snapshot → preview PG:

      python scripts/copy_sqlite_to_postgres.py \
        --source sqlite:////path/to/distributions.db \
        --dest 'postgresql+psycopg://USER:PASS@HOST/distributions?sslmode=require'

- [ ] Verify script exit 0 (counts + estimate checksum). Spot-check AGTHX / FBGRX / DODIX / VFIAX / SGENX stored amounts — do not invent.
- [ ] Replay `GET /funds?q=AGTHX`, `q=Balanced`, `GET /funds/lookup?ticker=ZZZZZ` (404), `GET /coverage` lookback_5y.
- [ ] Dist rows still expose `nav_on_distribution_day*` (join from `fund_nav_history`). `publication_stage` + `amount_unit` unchanged.
- [ ] Watch preview RSS and PG `active_connections` under an 8-way `/funds` burst.
- [ ] Leave production `WEB_CONCURRENCY=1` and sqlite URL untouched.

## Cutover window (Eric: Merge + Manual Deploy)

- [ ] Announce a short freeze on fixture densify / Manual Deploys that would rewrite the book.
- [ ] Final copy (or replay ingest) so Postgres matches the latest SQLite snapshot.
- [ ] Confirm preview migrations are already at head.
- [ ] Set production `DATABASE_URL` to the **internal** URL (app rewrites `postgres://` → `postgresql+psycopg://`).
- [ ] Set `WEB_CONCURRENCY=2`. Keep Web **Starter**. `SEED_ON_START=true`, `SEED_FORCE_FULL=false`.
- [ ] Manual Deploy. Health 200, `GET /funds?q=AGTHX` 200, lookup miss 404, coverage totals match snapshot.
- [ ] Point GitHub `DATABASE_URL` secret at the **external** URL (`sslmode=require`). Dry `workflow_dispatch` after traffic is stable — or keep the Action off until the first weekly slot.
- [ ] **Then** detach `/var/data` (unlocks zero-downtime + later scale-out). Keep the old SQLite file until one successful week.
- [ ] Only after disk detach: consider a second instance if one Starter + 2 workers is not enough.

## Rollback (only while the disk is still mounted)

- [ ] Flip `DATABASE_URL` back to `sqlite:////var/data/distributions.db`.
- [ ] Set `WEB_CONCURRENCY=1`.
- [ ] If the disk was already detached, restore from the kept SQLite file or a PG backup — decide **before** detach.
- [ ] Do not delete the Postgres instance until SQLite rollback is abandoned.

## Explicit non-goals of this PR

- No production Render setting, secret, or traffic change from this agent.
- No Redis / CDN.
- No native UUID PK change.
- No weekly cron flip to Sunday 06:00 CT (document only; align after cutover).
- Friends / soft-beta SQLite path still works (`docker compose up`, live `render.yaml`).
