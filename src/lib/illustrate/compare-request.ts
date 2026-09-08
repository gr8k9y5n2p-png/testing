import type {
  CompareRequest,
  CompareSelectors,
  CompareSideIn,
} from "@/lib/illustrate/compare-types";
import type { IllustrateRequest } from "@/lib/illustrate/types";

export type NavLookup = (ticker: string) => number | undefined;

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
  },
  lookup?: NavLookup,
): CompareSideIn {
  const ticker = fund.ticker.trim().toUpperCase();
  const nav = navFromFundMetadata(ticker, fund.nav, lookup);
  return {
    label: fund.label ?? fund.fundName ?? ticker,
    selectors: {
      ticker,
      fund_identifier: ticker,
      fund_family: fund.family,
      fund_name: fund.fundName ?? fund.label,
    },
    ...(nav != null ? { nav_per_share: nav } : {}),
  };
}

function withSideNav(
  side: CompareSideIn | null | undefined,
  lookup?: NavLookup,
): CompareSideIn | undefined {
  if (!side) return undefined;
  const { nav_per_share: givenNav, shares: givenShares, ...rest } = side;
  const ticker = tickerFromSelectors(side.selectors);
  const nav = navFromFundMetadata(ticker, givenNav, lookup);
  const shares = positiveNav(givenShares);
  return {
    ...rest,
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
