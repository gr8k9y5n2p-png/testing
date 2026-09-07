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
- `POST /illustrate/portfolio` — book-level review with coverage % and explicit gaps
- Top-40 US-advisor fund-family adapters (`GET /fund-families`, `GET /coverage`) plus `POST /coverage/gaps` when a portfolio ticker is missing
- Partner ingest (`POST /ingest/distributions`) remains the escape hatch for uncovered names

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
```

`POST /ingest/fetch` with `"fund_family":"all"` runs every **implemented** adapter (all 40 registered families in fixture mode).

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
  }' | jq '{coverage, gaps, totals, warnings, holdings: [.holdings[] | {ticker, fund_identifier, covered, publication_stage_used, gap_reason, warnings}]}'
```

On the American Funds fixtures: $1.25M covered / $150k uncovered → `coverage_pct` ≈ 89.3%. AMCAP uses the latest preliminary (3–5% NAV → $40,000 / $10,000 tax at 20%+5%). CGHM matches paid midyear rows but warns that NAV is missing. `XYZAX` is a gap.

## Multi-year history and estimate → actual

The upsert key includes `as_of` and `ex_date`, so a September preliminary, a December update, and a January final are **separate rows**. Do not collapse them.

`GET /distributions` already supports `as_of_from` / `as_of_to`, `publication_stage`, and `fund_identifier` (exact slug or ticker identity).

**Compare estimate vs paid for one fund:**

1. `GET /distributions?fund_identifier=amcap-fund&publication_stage=preliminary_estimate` — % of NAV ranges (often `total_capital_gains`).
2. `GET /distributions?fund_identifier=amcap-fund&publication_stage=final` — year-end per-share LTCG/STCG.
3. `GET /distributions?fund_identifier=amcap-fund&as_of_from=2024-01-01&as_of_to=2024-12-31` — one tax year’s publication window.
4. Units differ (`percent_of_nav` vs `per_share`); convert with NAV before subtracting. Illustration uses `as_of` or `prefer_publication_stages` so you do not add estimate + final.

Fixture packs today:

| Family | Years in fixtures | Live archive notes |
| --- | --- | --- |
| American Funds | 2024 prelim + 2024 final, 2025 prelim + 2025 final, 2026 midyear paid | 2025 YE + 2026 midyear HTML are public. 2024 advisor YE URL 302s to login (transcribed fixture). Per-fund tool: https://www.capitalgroup.com/individual/investments/historicaldistributions/ |
| T. Rowe Price | 2023, 2024, 2025 year-end HTML | Same public path with the year in the filename (verified 2026-09-07) |

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

## Coverage (portfolio review)

Sparse family coverage makes Aftertax-style portfolio analytics wrong: a book that is 40% Vanguard / iShares / Fidelity looks like it has no taxable distributions if those adapters are stubs. The registry is the **top 40 US-advisor-relevant firms** (AUM ranks 1–40). `GET /coverage` returns `implemented_pct` (today 40/40 fixture parsers) so the website can later compute *% of portfolio dollars covered*.

`GET /fund-families` includes `coverage_tier` (`implemented` | `stub`), `aum_rank` (1 = largest / highest priority), and `priority`.

When a holding’s ticker or family is not in the store, Website Engineering should call `POST /coverage/gaps` with `{ticker or fund_name, fund_family?, holding_dollars?}`. The API logs the gap in SQLite and returns:

| `suggested_next_step` | Meaning |
| --- | --- |
| `fetch_adapter` | A registered parser exists — run `POST /ingest/fetch` for that slug, then search. If the ticker is still missing, partner-ingest the row. |
| `queued` | Slug is registered but not implemented (none of the top 40 today). |
| `manual_ingest` | Unknown family — `POST /ingest/distributions` is the escape hatch. |

| Rank | Slug | Display name | Parser | Live HTML | Public source (verified 2026-09-07) |
| --- | --- | --- | --- | --- | --- |
| 1 | `blackrock` (alias `ishares`) | BlackRock / iShares | implemented | yes | https://www.ishares.com/us/capital-gains-distributions |
| 2 | `vanguard` | Vanguard | implemented | JS SPA — fixture fallback | https://advisors.vanguard.com/tax-center/year-end-distributions |
| 3 | `fidelity` | Fidelity | implemented | yes | https://institutional.fidelity.com/app/tabbed/products/FIIS_SP52_DPL6.html?navId=324 |
| 4 | `state_street` (aliases `spdr`, `ssga`) | State Street / SPDR | implemented | Angular — fixture fallback | https://www.ssga.com/us/en/individual/resources/documents/etf-capital-gain-distributions |
| 5 | `jpmorgan` (alias `jpm`) | J.P. Morgan AM | implemented | PDF / no HTML grid | Section 19a PDFs under am.jpmorgan.com `.../section-19-notices/` |
| 6 | `goldman_sachs` (aliases `gs`, `gsam`) | Goldman Sachs AM | implemented | 403 / PDF library | https://www.gsam.com/content/gsam/us/en/advisors/literature-and-forms/forms-and-tax-center.html |
| 7 | `american_funds` (alias `capital_group`) | American Funds | implemented | yes | Capital Group individual tax center (see below) |
| 8 | `pimco` | PIMCO | implemented | PDF / notices | https://www.pimco.com/us/en/resources/tax-center |
| 9 | `invesco` | Invesco | implemented | PDF + PR | https://www.invesco.com/content/dam/invesco/us/en/documents/tax-centre/2025%20Invesco%20Estimated%20Capital%20Gains%20pdf.pdf |
| 10 | `t_rowe_price` (alias `trp`) | T. Rowe Price | implemented | yes | https://www.troweprice.com/personal-investing/resources/planning/tax/dividend-distributions/mutual-funds/2025-year-end-distributions.html |
| 11 | `ubs` | UBS Asset Management | implemented | price-page HTML / PDF | https://www.ubs.com/us/en/assetmanagement/funds/mutual-fund-price.html (paid PWTAX); estimate PDF from the mutual-fund product hub |
| 12 | `franklin_templeton` (aliases `franklin`, `templeton`, `putnam`) | Franklin Templeton | implemented | JS SPA + 19(a) PDF | https://www.franklintempleton.com/tools-and-resources/tax-center ; CEF 19(a) e.g. `.../ft-section-19-notice-12-31-2025` |
| 13 | `bny_mellon` (aliases `bny`, `dreyfus`) | BNY Mellon / Dreyfus | implemented | PDF | https://www.bny.com/assets/investments/im/documents/manual/tax-forms/2025-Estimated-capital-gains.pdf |
| 14 | `nuveen` (alias `tiaa`) | Nuveen / TIAA | implemented | PDF viewer | https://documents.nuveen.com/Documents/Nuveen/Default.aspx?uniqueId=3c3be13d-d800-48e2-a537-c251162ab9f4 |
| 15 | `northern_trust` (aliases `nt`, `ntam`) | Northern Trust | implemented | PDF | https://ntam.northerntrust.com/content/dam/ntam/us/en/documents/account-resources/tax-center/all-investor/estimated-capital-gains-2025.pdf |
| 16 | `morgan_stanley` (aliases `msim`, `ms`) | Morgan Stanley IM | implemented | PDF (often Akamai-walled) | https://www.morganstanley.com/im/publication/forms/tax/2025_etf_year_end_distributions.pdf |
| 17 | `schwab` (alias `charles_schwab`) | Charles Schwab IM | implemented | JS family page; product HTML | https://www.schwabassetmanagement.com/resource/schwab-funds-actual-annual-distributions-2025 |
| 18 | `dimensional` (alias `dfa`) | Dimensional | implemented | PDF | https://www.dimensional.com/chmedia/440098/source/download/2025-capital-gain-distribution-estimates.pdf |
| 19 | `columbia_threadneedle` (aliases `columbia`, `ameriprise`) | Columbia Threadneedle | implemented | PDF | https://www.columbiathreadneedleus.com/binaries/content/assets/cti/public/2025-mid-year-cap-gain-estimates-all-funds.pdf |
| 20 | `amundi` (alias `pioneer`) | Amundi US / Pioneer | implemented | PDF | https://pioneerinvestments.com/content/dam/pioneer/en/documents/resources/tax-center/2025/10152025-mutual-funds-2025-capital-gain-estimates.pdf |
| 21 | `allspring` (aliases `wells_fargo`, `wfam`) | Allspring | implemented | product-page HTML / gated PDF | https://www.allspringglobal.com/resources/product-alerts/ ; paid history e.g. `.../special-mid-cap-value/` |
| 22 | `janus_henderson` (alias `janus`) | Janus Henderson | implemented | PDF | https://www.janushenderson.com/en-us/advisor/annual-distributions-supplemental-tax-documents-mutual-funds/ ; 2025 estimates on the rackcdn `distribution-tax` path |
| 23 | `american_century` | American Century | implemented | JS hub + PDF | https://res.americancentury.com/docs/estimated-distributions-november-retail.pdf |
| 24 | `dodge_cox` (aliases `dodge`, `dodgx`) | Dodge & Cox | implemented | PDF | https://www.dodgeandcox.com/content/dam/dc/us/en/pdf/dc-us-estimated-distributions-1Q2026.pdf |
| 25 | `mfs` | MFS Investment Management | implemented | PDF | https://www.mfs.com/content/dam/mfs-enterprise/mfscom/backlot/mfs_cg_fly.pdf |
| 26 | `lord_abbett` (alias `lord`) | Lord Abbett | implemented | PDF (no-pay list) | https://www.lordabbett.com/content/dam/lordabbett-captivate/documents/TaxCenter/UnitedStates/Funds-with-Losses.pdf |
| 27 | `ab` (aliases `alliancebernstein`, `alliance_bernstein`) | AllianceBernstein | implemented | PDF | https://www.alliancebernstein.com/content/dam/alliancebernstein/us-retail/us-retail-pdfs/tax-center/Final_GEN-5796-1025.pdf |
| 28 | `federated_hermes` (alias `federated`) | Federated Hermes | implemented | JS tax center + 19(a) PDF | https://www.federatedhermes.com/siteassets/documents/regulatory/19a-notices/g85307-06.pdf |
| 29 | `virtus` | Virtus | implemented | PDF | https://www.virtus.com/assets/files/abi/cap_gains_estimate_6-26_8569.pdf |
| 30 | `eaton_vance` (alias `ev`) | Eaton Vance | implemented | CEF 19(b) PDF | https://www.eatonvance.com/content/dam/im/assets/publication/thought-leadership/press-release/combined19bpressreleasemarch2025.pdf |
| 31 | `john_hancock` (aliases `manulife`, `jh`) | John Hancock / Manulife | implemented | PDF | https://www.jhinvestments.com/content/dam/jhi-investments/JHINV/public/Corporate/News/CorporatePressReleases/estimated-capital-gain-and-income-distribution-press-release-2025-jhi.pdf |
| 32 | `principal` | Principal | implemented | product-page HTML / viewer PDF | https://www.principalam.com/us/fund/pqiax ; tax hub https://www.principal.com/help/help-individuals/tax-center/dividends-capital-gains-distributions |
| 33 | `thrivent` | Thrivent | implemented | yes | https://www.thriventfunds.com/support/tax-resource-center/capital-gains.html |
| 34 | `hartford` | Hartford Funds | implemented | PDF | https://www.hartfordfunds.com/dam/en/docs/pub/funddocuments/regulatorydocument/Tax%20Center/HMFCapitalGains_December2025EstimateMemo.pdf |
| 35 | `macquarie` (aliases `delaware`, `delaware_funds`) | Macquarie / Delaware Funds | implemented | PDF | https://mim.fgsfulfillment.com/download.aspx?sku=CGE-RET |
| 36 | `first_eagle` (alias `fei`) | First Eagle | implemented | PDF | https://www.firsteagle.com/sites/default/files/fei-documents/FEF_Ordinary_Income_Gains_Estimates.pdf |
| 37 | `gmo` | GMO | implemented | PDF | https://www.gmo.com/globalassets/documents---manually-loaded/documents/distribution-estimates-and-dates/gmo-trust-funds---july-2026-distribution-estimate.pdf |
| 38 | `artisan` (alias `artisan_partners`) | Artisan Partners | implemented | paid HTML / no estimate PDF | https://www.artisanpartners.com/individual-investors/resources/tax-center/distributions.html |
| 39 | `calamos` | Calamos | implemented | PDF | https://www.calamos.com/globalassets/media/documents/tax-center/2025-calamos-estimated-capital-gains.pdf |
| 40 | `wasatch` | Wasatch | implemented | PDF | https://wasatchglobal.com/wp-content/uploads/2025/11/WGI_2025_Yr_End_Dist_Estimates.pdf |

**Wellington:** skipped. Wellington Management is primarily a subadvisor / institutional manager and does not publish public US retail distribution-estimate pages that we can register as a `FundSource`. Holdings in Wellington-subadvised sleeves should use the **distributing** family’s slug (or `POST /ingest/distributions`).

**Geode:** skipped. Geode Capital is the Fidelity index subadvisor and does not publish a separate US retail mutual-fund/ETF capital-gains estimate book. Use the `fidelity` adapter.

**Legal & General:** skipped. LGIM America is institutional / SMA-oriented; no public US open-end mutual-fund capital-gains estimate HTML or PDF was found on 2026-09-07.

**PGIM / Prudential:** skipped for this tier. The individual tax center (`https://www.pgim.com/us/en/individual/resources/account-services/tax-center`) links a preliminary-estimate PDF through an AEM viewer (`pidoc?pdfId=8912A02F28CF4802A2CA39479A521E39`). Automated GETs receive the attestation/viewer shell, not the table, and no second public HTML grid or direct DAM PDF was found. Use `POST /ingest/distributions` until a partner file or scrapeable reprint exists.

**Eaton Vance vs Morgan Stanley:** MSIM open-end/ETF year-end PDFs stay on `morgan_stanley`. `eaton_vance` is registered separately because Eaton Vance still publishes distinct public CEF Section 19(b) estimated-source notices.

**Putnam:** skipped as a distinct `FundSource`. Putnam.com now redirects to Franklin Templeton; the remaining Putnam tax-center pages are 1099 samples and per-fund distribution calendars, not a Putnam-branded family estimate book. Use the `franklin_templeton` adapter (alias `putnam`). `wasatch` is the rank-40 replacement.

**Baron:** skipped. The public tax center (`https://www.baroncapitalgroup.com/tax-center`) publishes a 2026 distribution *calendar* only — no per-share capital-gains estimate or paid-amount table.

**Live honesty:** Vanguard and State Street pages are still client-rendered as of 2026-09-07 (static GET parses 0 rows → fixture fallback). JPM, Goldman, PIMCO, and Invesco still publish estimates as PDFs or login-walled docs — no new scrapeable HTML grids were found on re-check. Ranks 11–20 are the same pattern: BNY, Nuveen, Northern Trust, Dimensional, Columbia, and Pioneer/Amundi are public PDFs; Franklin’s family estimate tool is a JS SPA (fixture uses a public CEF 19(a)); UBS and Schwab have some public HTML but fund-name/class layout or SPA shells keep live parse unreliable. Ranks 21–30 continue that pattern: Janus, American Century, Dodge & Cox, MFS, AB, and Virtus are public PDFs; Lord Abbett’s only public 2025 estimate document is a no-pay list; Federated’s family tax-center grids are JS (fixture uses a public 19(a)); Allspring’s family estimate PDF is gated/image-based (fixture uses public product-page paid rows); Eaton Vance open-end HTML was not found (fixture uses a public CEF 19(b)). Ranks 31–40: John Hancock, Hartford, Macquarie/Delaware, First Eagle, GMO, Calamos, and Wasatch are public PDFs; Thrivent’s paid capital-gains table is public HTML; Principal’s family estimate PDF is a GetFile viewer (fixture uses public product-page paid rows); Artisan’s tax-center HTML is paid YTD income (no family estimate PDF). Do not treat fixture rows as a complete live book. `POST /ingest/distributions` is always valid for an advisor-uploaded notice.

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

### Other registered families (ranks 1–40 except American Funds)

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

Coverage includes HTML normalization (American Funds plus top-40 family fixtures), multi-year history filters, upsert idempotency, search filters, tax illustration math, portfolio coverage, and coverage-gap logging.

## Layout

```
app/
  main.py              FastAPI app
  api.py               HTTP routes
  models.py / schemas.py / crud.py
  sources/             FundSource adapters + HTML parser
  services/ingest.py   Fetch + upsert orchestration
  services/illustrate.py  Tax-impact illustration
  services/coverage.py Coverage snapshot + gap logging
  cli.py               seed / fetch / families
fixtures/<family>/     HTML fixtures (American Funds + top 40)
tests/
```
