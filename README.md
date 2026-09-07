# Fund Distribution Estimates API

Backend service that ingests **taxable distribution estimates** published by fund managers and stores them in a searchable database for an Asset Management / Financial Advisor website.

The default demo uses **SQLite** and bundled Capital Group HTML fixtures so the pipeline runs offline. The same SQLAlchemy models work with **Postgres** by changing `DATABASE_URL`.

## What you get

- Normalized data model for distribution estimates (family, fund, ticker, share class, type, amount + unit, tax dates, source URL, raw JSON audit payload)
- `POST /ingest/distributions` for partner/manual feeds
- `POST /ingest/fetch` to run a pluggable `FundSource` adapter (`fixture` or `live`)
- Idempotent upserts on `(fund_family, fund identifier, share class, estimate type, as_of, ex-date)`
- Search API with filters, text search, and pagination
- `POST /illustrate` — server-side tax-impact math for a dollar holding (Website Engineering owns the UI)
- American Funds / Capital Group HTML parser plus stubs for Vanguard, Fidelity, and T. Rowe Price

## Quick start

Requires Python 3.12+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

mkdir -p data
python -m app.cli seed          # load fixtures and print a search example
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open interactive docs at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### Docker

```bash
docker compose up --build
```

The API listens on port 8000. SQLite is stored in the `dist-data` volume.

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
curl -s 'http://127.0.0.1:8000/fund-families' | jq
curl -s http://127.0.0.1:8000/distributions/<id> | jq
```

`POST /ingest/fetch` with `"fund_family":"all"` runs every **implemented** adapter (currently American Funds).

Live fetch (hits public Capital Group pages; may change or rate-limit):

```bash
curl -s -X POST http://127.0.0.1:8000/ingest/fetch \
  -H 'Content-Type: application/json' \
  -d '{"fund_family":"american_funds","mode":"live"}'
```

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
| `per_share` | `shares = shares` or `holding_dollars / nav_per_share`; `distribution_dollars = shares * amount`. **HTTP 422** if neither `nav_per_share` nor `shares` is provided |
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
| `publication_stage` | `preliminary_estimate`, `updated_estimate`, `final`, `paid` |
| `source_url` | Page or partner URL |
| `raw_payload` | Original row/page context for audit (list endpoints omit it unless `include_raw=true`) |
| `ingested_at` | Server timestamp of last upsert |

Re-running the **same** source document updates the existing row. A new `as_of` (September preliminary vs December update vs January final) inserts a new snapshot.

## Source adapters

`FundSource.fetch(mode=...)` returns normalized records. Register new families in `app/sources/registry.py`.

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

### Stubs

`vanguard`, `fidelity`, and `t_rowe_price` are registered so `/fund-families` shows them. Fetching a stub returns HTTP 400 until you add a parser.

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
3. Replace the stub in `app/sources/registry.py` with your class (and add aliases if useful).
4. Add a parser test that reads the fixture.
5. `POST /ingest/fetch` with `"fund_family":"vanguard"`.

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

Coverage includes HTML normalization, upsert idempotency, search filters, and tax illustration math (`percent_of_nav`, `per_share`, rate overrides, validation).

## Layout

```
app/
  main.py              FastAPI app
  api.py               HTTP routes
  models.py / schemas.py / crud.py
  sources/             FundSource adapters + HTML parser
  services/ingest.py   Fetch + upsert orchestration
  services/illustrate.py  Tax-impact illustration
  cli.py               seed / fetch / families
fixtures/american_funds/
tests/
```
