import type {
  ComparePeriodIn,
  CompareRequest,
  CompareSelectors,
  CompareSideIn,
} from "./compare-types.ts";
import { PORTFOLIO_COMPARE_YEARS } from "./portfolio-compare-years.ts";
import {
  UI_DEFAULT_TAX_RATES,
  type IllustrateRequest,
  type TaxRates,
} from "./types.ts";

/**
 * Data `TaxRates` (`additionalProperties: false`).
 * UI rate-strip aliases ordinary/ltcg/stcg/qdi 422 the live API.
 */
export const DATA_API_TAX_RATE_KEYS = [
  "ordinary_income",
  "long_term_capital_gains",
  "short_term_capital_gains",
  "qualified_dividend",
  "state",
] as const;

const TAX_RATE_ALIASES: Record<string, keyof TaxRates> = {
  ordinary_income: "ordinary_income",
  ordinary: "ordinary_income",
  long_term_capital_gains: "long_term_capital_gains",
  ltcg: "long_term_capital_gains",
  long_term: "long_term_capital_gains",
  short_term_capital_gains: "short_term_capital_gains",
  stcg: "short_term_capital_gains",
  short_term: "short_term_capital_gains",
  qualified_dividend: "qualified_dividend",
  qdi: "qualified_dividend",
  qualified: "qualified_dividend",
  state: "state",
};

function rateNumber(value: unknown): number | undefined {
  if (value == null || value === "") return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

/**
 * Map UI rate-strip fields onto the Data API schema and drop extra keys.
 * Long names win when both an alias and the schema key are present.
 */
export function toDataApiTaxRates(
  incoming?: Partial<TaxRates> | Record<string, unknown> | null,
): TaxRates {
  const rates: TaxRates = { ...UI_DEFAULT_TAX_RATES };
  if (!incoming || typeof incoming !== "object") return rates;

  const apply = (canonicalOnly: boolean) => {
    for (const [key, value] of Object.entries(incoming)) {
      const mapped = TAX_RATE_ALIASES[key];
      if (!mapped) continue;
      const isCanonical = DATA_API_TAX_RATE_KEYS.includes(
        key as (typeof DATA_API_TAX_RATE_KEYS)[number],
      );
      if (canonicalOnly !== isCanonical) continue;
      const parsed = rateNumber(value);
      if (parsed == null) continue;
      rates[mapped] = parsed;
    }
  };
  apply(false);
  apply(true);
  return rates;
}

/** Locked Compare tax payload. Empty `{}` is never sent — UI always posts rates. */
export function compareTaxRequestFields(input?: {
  taxRates?: Partial<TaxRates> | Record<string, unknown> | null;
  combineStateWithFederal?: boolean;
}): {
  tax_rates: TaxRates;
  combine_state_with_federal: boolean;
} {
  return {
    tax_rates: toDataApiTaxRates(input?.taxRates),
    combine_state_with_federal: input?.combineStateWithFederal ?? true,
  };
}

export type NavLookup = (ticker: string) => number | undefined;
export type FundNameLookup = (ticker: string) => string | undefined;

/**
 * Data `_filter_stmt` ANDs every populated selector. Catalog `fund_name`
 * values (e.g. "American Funds Growth Fund of America") miss Data's product
 * name ("The Growth Fund of America") and return `matched: false` / N/A
 * for every vintage. Ticker is unique — never send `fund_name`.
 */
export function sanitizeCompareSelectors(
  selectors?: CompareSelectors | null,
): CompareSelectors | undefined {
  if (!selectors) return undefined;
  const next: CompareSelectors = { ...selectors };
  // Data `_filter_stmt` ANDs every populated selector. Catalog labels like
  // "American Funds Growth Fund of America" miss "The Growth Fund of America"
  // and return matched:false / N/A for every vintage. Ticker is unique.
  delete next.fund_name;
  return next;
}

export function compareSelectorsFromFund(fund: {
  ticker: string;
  fundName?: string;
  family?: string;
  fundIdentifier?: string;
}): CompareSelectors {
  const ticker = fund.ticker.trim().toUpperCase();
  const identifier = fund.fundIdentifier?.trim() || ticker;
  const family = fund.family?.trim();
  return (
    sanitizeCompareSelectors({
      ticker,
      fund_identifier: identifier,
      ...(family ? { fund_family: family } : {}),
      fund_name: fund.fundName,
    }) ?? { ticker, fund_identifier: identifier }
  );
}

/**
 * Data's CompareRequest / CompareSideIn mark `nav_per_share` and `shares` as
 * `gt=0`. Sending 0 or a negative value 422s the whole compare.
 */
export function positiveNav(value: unknown): number | undefined {
  if (value == null || value === "") return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : undefined;
}

export function tickerFromSelectors(
  selectors?: CompareSelectors | null,
): string | undefined {
  const raw = selectors?.ticker || selectors?.fund_identifier;
  const ticker = raw?.trim().toUpperCase();
  return ticker || undefined;
}

/**
 * Prefer an explicit NAV (search / fund metadata), then an optional ticker
 * lookup (seed / catalog). Unknown tickers stay undefined so the request is
 * holding_dollars-only (% of NAV path — Data does not need NAV for those rows).
 */
export function navFromFundMetadata(
  ticker?: string | null,
  fallback?: unknown,
  lookup?: NavLookup,
): number | undefined {
  const explicit = positiveNav(fallback);
  if (explicit != null) return explicit;
  const key = ticker?.trim().toUpperCase();
  if (!key) return undefined;
  return positiveNav(lookup?.(key));
}

/**
 * Dist $ uses live weekly / catalog `nav_per_share`, never SAMPLE seed when
 * a live print exists. AGTHX seed $72.14 must not win over weekly $88.42.
 *
 * Proven live catalog (differs from seed) wins. Otherwise weekly NAV, then
 * catalog, then seed as last resort.
 */
export function preferLiveWeeklyNav(input: {
  ticker?: string | null;
  catalogNav?: unknown;
  weeklyNav?: unknown;
  lookup?: NavLookup;
}): number | undefined {
  const catalog = positiveNav(input.catalogNav);
  const weekly = positiveNav(input.weeklyNav);
  const seed = navFromFundMetadata(input.ticker, undefined, input.lookup);
  if (catalog != null && seed != null && catalog !== seed) return catalog;
  if (weekly != null) return weekly;
  return catalog ?? seed;
}

export const PER_SHARE_NAV_REQUIRED =
  "Enter NAV per share to illustrate $ / share amounts.";

/**
 * Dollar Illustration NAV for every fund: typed input first, then
 * search/fund metadata (catalog NAV or ticker lookup). Live `/funds`
 * often hydrates `nav: 0` — that is not a price; fall through to lookup.
 */
export function illustrationRequestNav(
  typedInput: unknown,
  ticker?: string | null,
  fundNav?: unknown,
  lookup?: NavLookup,
): number | undefined {
  return positiveNav(typedInput) ?? navFromFundMetadata(ticker, fundNav, lookup);
}

/** `$ / share` only errors when NAV is genuinely unavailable. */
export function perShareNavError(
  unit: string,
  requestNav: number | undefined,
): string | null {
  return unit === "per_share" && requestNav == null
    ? PER_SHARE_NAV_REQUIRED
    : null;
}

export function compareSideFromFund(
  fund: {
    ticker: string;
    fundName?: string;
    family?: string;
    nav?: number | null;
    label?: string;
    fundIdentifier?: string;
  },
  lookup?: NavLookup,
): CompareSideIn {
  const ticker = fund.ticker.trim().toUpperCase();
  const nav = navFromFundMetadata(ticker, fund.nav, lookup);
  return {
    label: fund.label ?? fund.fundName ?? ticker,
    selectors: compareSelectorsFromFund(fund),
    ...(nav != null ? { nav_per_share: nav } : {}),
  };
}

/**
 * Locked paid-history window for POST /illustrate/compare.
 * Data AGTHX / AMCPX YoY finals are 2021–2025 — same years as Portfolio.
 * Do not roll into the current calendar year (2026) or the request can 422
 * / return no matched rows while the table axis looks empty.
 */
export function trailingCalendarPeriods(
  _nowYear = new Date().getUTCFullYear(),
): ComparePeriodIn[] {
  return PORTFOLIO_COMPARE_YEARS.map((year) => ({ year }));
}

/**
 * Homepage Growth + tax-drag YoY body. One fund, calendar-year periods.
 * `left.label` stays the ticker (chart series id); Data still zips vintages
 * and sets `period.year` to the newer year.
 */
export function yoyTaxDragCompareRequest(input: {
  ticker: string;
  label?: string;
  fundIdentifier?: string;
  fundFamily?: string;
  fundName?: string;
  holdingDollars: number;
  navPerShare?: number | null;
  periods: ComparePeriodIn[];
  taxRates?: TaxRates;
  combineStateWithFederal?: boolean;
}): CompareRequest {
  const ticker = input.ticker.trim().toUpperCase();
  const selectors = compareSelectorsFromFund({
    ticker,
    fundIdentifier: input.fundIdentifier ?? ticker,
    family: input.fundFamily,
    fundName: input.fundName,
  });
  const nav = positiveNav(input.navPerShare);
  return {
    mode: "yoy",
    holding_dollars: input.holdingDollars,
    ...compareTaxRequestFields(input),
    latest_as_of_only: true,
    ...(nav != null ? { nav_per_share: nav } : {}),
    selectors,
    left: {
      label: input.label ?? ticker,
      holding_dollars: input.holdingDollars,
      ...(nav != null ? { nav_per_share: nav } : {}),
      selectors,
    },
    periods: input.periods,
  };
}

function withSideNav(
  side: CompareSideIn | null | undefined,
  lookup?: NavLookup,
): CompareSideIn | undefined {
  if (!side) return undefined;
  const {
    nav_per_share: givenNav,
    shares: givenShares,
    selectors: givenSelectors,
    ...rest
  } = side;
  const selectors = sanitizeCompareSelectors(givenSelectors);
  const ticker = tickerFromSelectors(selectors);
  const nav = navFromFundMetadata(ticker, givenNav, lookup);
  const shares = positiveNav(givenShares);
  return {
    ...rest,
    ...(selectors ? { selectors } : {}),
    ...(nav != null ? { nav_per_share: nav } : {}),
    ...(shares != null ? { shares } : {}),
  };
}

/**
 * Locked Data compare body (`tests/test_api_compare.py`, PR #2 schemas):
 *
 * - `left` / `right` selectors + `holding_dollars`
 * - `nav_per_share` / `shares` only when > 0 (per_share math)
 * - omit NAV for the % of NAV / holding_dollars-only path
 *
 * Without NAV, Data 422s per_share illustrations and compare maps that to
 * `matched: false` + $0. Enrich from search/seed metadata so AGTHX vs VIGAX
 * (and similar covered pairs) still compute.
 */
export function toDataApiCompareBody(
  request: CompareRequest,
  lookup?: NavLookup,
): CompareRequest {
  const left = withSideNav(request.left, lookup);
  const right = withSideNav(request.right, lookup);
  const yoyTicker =
    tickerFromSelectors(request.selectors) ?? tickerFromSelectors(left?.selectors);
  const topNav =
    positiveNav(request.nav_per_share) ??
    (request.mode === "yoy"
      ? (left?.nav_per_share ?? navFromFundMetadata(yoyTicker, undefined, lookup))
      : undefined);
  const shares = positiveNav(request.shares);

  const rest: CompareRequest = { ...request };
  delete rest.nav_per_share;
  delete rest.shares;
  delete rest.left;
  delete rest.right;
  const selectors = sanitizeCompareSelectors(rest.selectors);
  if (selectors) rest.selectors = selectors;
  else delete rest.selectors;

  return {
    ...rest,
    tax_rates: toDataApiTaxRates(rest.tax_rates),
    combine_state_with_federal: rest.combine_state_with_federal !== false,
    ...(left ? { left } : {}),
    ...(right ? { right } : {}),
    ...(topNav != null ? { nav_per_share: topNav } : {}),
    ...(shares != null ? { shares } : {}),
  };
}

/**
 * Locked POST /illustrate body. Attach `nav_per_share` from the request or
 * search/seed metadata (same pattern as compare) so holding dollars can
 * convert to shares on per_share snapshots. Do not invent a NAV.
 */
export function toDataApiIllustrateBody(
  request: IllustrateRequest,
  lookup?: NavLookup,
): Record<string, unknown> {
  const { selector, nav_per_share, ...rest } = request;
  const ticker = selector?.ticker ?? selector?.fund_identifier;
  const nav = navFromFundMetadata(ticker, nav_per_share, lookup);
  const body: Record<string, unknown> = { ...rest };
  if (selector) {
    body.selector = selector;
    body.selectors = {
      fund_family: selector.fund_family,
      fund_identifier: selector.fund_identifier,
      ticker: selector.ticker ?? selector.fund_identifier,
    };
  }
  if (nav != null) body.nav_per_share = nav;
  body.latest_as_of_only = true;
  return body;
}

/**
 * Data `_filter_stmt` ANDs `fund_name`. Prefer the search/seed product name
 * (AGTHX → "The Growth Fund of America") and never send the ticker as the name.
 */
export function sanitizeHoldingFundName(
  ticker?: string | null,
  fundName?: string | null,
  lookup?: FundNameLookup,
): string | undefined {
  const key = ticker?.trim().toUpperCase();
  const seed = key ? lookup?.(key)?.trim() : undefined;
  if (seed) return seed;
  const given = fundName?.trim();
  if (!given || (key && given.toUpperCase() === key)) return undefined;
  return given;
}

/**
 * Portfolio holding NAV + selector for POST /illustrate/portfolio/compare.
 * Same rules as fund compare: search/seed metadata, never send 0.
 */
export function withPortfolioHoldingNav<T extends {
  ticker?: string | null;
  fund_identifier?: string | null;
  fund_name?: string | null;
  nav_per_share?: number | null;
  shares?: number | null;
}>(holding: T, lookup?: NavLookup, fundNameLookup?: FundNameLookup): T {
  const ticker = holding.ticker || holding.fund_identifier;
  const nav = navFromFundMetadata(ticker, holding.nav_per_share, lookup);
  const shares = positiveNav(holding.shares);
  const fundName = sanitizeHoldingFundName(
    ticker,
    holding.fund_name,
    fundNameLookup,
  );
  const rest = { ...holding };
  delete rest.nav_per_share;
  delete rest.shares;
  delete rest.fund_name;
  return {
    ...rest,
    ...(fundName ? { fund_name: fundName } : {}),
    ...(nav != null ? { nav_per_share: nav } : {}),
    ...(shares != null ? { shares } : {}),
  };
}
