import type {
  ComparePeriodIn,
  CompareRequest,
  CompareSelectors,
  CompareSideIn,
} from "@/lib/illustrate/compare-types";
import type { IllustrateRequest } from "@/lib/illustrate/types";

export type NavLookup = (ticker: string) => number | undefined;

/**
 * Data `_filter_stmt` ANDs every populated selector. `fund_name=AMCPX`
 * looks for ILIKE '%AMCPX%' on "AMCAP Fund" / "The Growth Fund of America"
 * and returns no rows → `matched: false` / N/A for every vintage.
 * Never send the ticker (or a blank) as `fund_name`.
 */
export function sanitizeCompareSelectors(
  selectors?: CompareSelectors | null,
): CompareSelectors | undefined {
  if (!selectors) return undefined;
  const ticker = tickerFromSelectors(selectors);
  const fundName = selectors.fund_name?.trim();
  const next: CompareSelectors = { ...selectors };
  if (!fundName || (ticker && fundName.toUpperCase() === ticker)) {
    delete next.fund_name;
  } else {
    next.fund_name = fundName;
  }
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
 * Last five calendar years through today (2022–2026 in 2026).
 * Live compare covers this window for AMCPX / AGTHX; do not hardcode 2021–2025.
 */
export function trailingCalendarPeriods(
  nowYear = new Date().getUTCFullYear(),
): ComparePeriodIn[] {
  return [0, 1, 2, 3, 4].map((offset) => ({ year: nowYear - 4 + offset }));
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
    combine_state_with_federal: true,
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
    tax_rates: {},
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
 * Portfolio holding NAV for POST /illustrate/portfolio/compare.
 * Same rules as fund compare: search/seed metadata, never send 0.
 */
export function withPortfolioHoldingNav<T extends {
  ticker?: string | null;
  fund_identifier?: string | null;
  nav_per_share?: number | null;
  shares?: number | null;
}>(holding: T, lookup?: NavLookup): T {
  const nav = navFromFundMetadata(
    holding.ticker || holding.fund_identifier,
    holding.nav_per_share,
    lookup,
  );
  const shares = positiveNav(holding.shares);
  const rest = { ...holding };
  delete rest.nav_per_share;
  delete rest.shares;
  return {
    ...rest,
    ...(nav != null ? { nav_per_share: nav } : {}),
    ...(shares != null ? { shares } : {}),
  };
}
