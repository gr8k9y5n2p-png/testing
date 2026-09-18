import type { FundEstimateView } from "../../data/types.ts";
import type { CompareResponse } from "./compare-types.ts";
import { UI_DEFAULT_TAX_RATES, type TaxRates } from "./types.ts";
import {
  upcomingDistDollarsFromPerShare,
  upcomingPctOfNavFromPerShare,
} from "./portfolio-compare-copy.ts";
import {
  announcedDateOf,
  isFutureAnnouncedDate,
  publicationBucket,
  utcToday,
  type UpcomingRow,
} from "./publication-stage.ts";

export type CompareGrowthFund = {
  ticker: string;
  label?: string;
  fundIdentifier?: string;
  fundFamily?: string;
  fundName?: string;
  navPerShare?: number | null;
};

export type CompareUpcomingHint = {
  dollars: number | null;
  announced: boolean;
  asOf?: string | null;
  publicationStage?: string | null;
};

/** Eric lock 2026-09-17: Compare caps at 4 tickers. Portfolio holdings stay separate. */
export const COMPARE_SLOT_COUNT = 4;

/** Visible placeholder for Compare slot N (0-based). First box is "Ticker 1". */
export function compareSlotPlaceholder(index: number): string {
  return `Ticker ${index + 1}`;
}

/** Shared Compare holding. Default $10,000 — one input drives every $ module. */
export const COMPARE_DEFAULT_HOLDING_DOLLARS = 10_000;

/** Parse the shared dollars-invested field. Invalid / ≤ 0 keeps the prior holding. */
export function parseCompareHoldingDollars(
  raw: string,
  fallback = COMPARE_DEFAULT_HOLDING_DOLLARS,
): number {
  const parsed = Number(String(raw).replace(/[$,\s]/g, ""));
  if (!Number.isFinite(parsed) || parsed <= 0) return fallback;
  return Math.round(parsed * 100) / 100;
}

/** Locked Compare starting rates — same top-bracket set as Dollar Illustration. */
export const COMPARE_DEFAULT_TAX_RATES: TaxRates = UI_DEFAULT_TAX_RATES;

export const COMPARE_DEFAULT_COMBINE_STATE = true;

/** Slot confirm is already committed — keep this short so modules start together. */
export const COMPARE_FETCH_DEBOUNCE_MS = 50;

export type CompareLoadedTicker = {
  ticker: string;
  fund: FundEstimateView | null;
  tax: CompareResponse | null;
  needsNav?: boolean;
};

/** Keep already-filled tickers on screen while a new slot loads. */
export function keepFreshCompareRows(
  current: CompareLoadedTicker[],
  tickers: string[],
): CompareLoadedTicker[] {
  const want = new Set(tickers);
  return current.filter((row) => want.has(row.ticker));
}

/** Progressive Upcoming / prefetch: merge one ticker without dropping the others. */
export function mergeCompareLoadedRows(
  current: CompareLoadedTicker[],
  incoming: CompareLoadedTicker,
  order: string[],
): CompareLoadedTicker[] {
  const byTicker = new Map(current.map((row) => [row.ticker, row]));
  byTicker.set(incoming.ticker, incoming);
  return order
    .map((ticker) => byTicker.get(ticker))
    .filter((row): row is CompareLoadedTicker => Boolean(row));
}

function fundViewTicker(fund: FundEstimateView): string {
  return fund.ticker.trim().toUpperCase();
}

/** Merge per-ticker identity / unpaid hydrate without dropping other slots. */
export function mergeCompareFundViews(
  current: FundEstimateView[],
  incoming: FundEstimateView,
  order: string[] = [],
): FundEstimateView[] {
  const key = fundViewTicker(incoming);
  if (!key) return current;
  const byTicker = new Map(
    current.map((fund) => [fundViewTicker(fund), fund]),
  );
  byTicker.set(key, incoming);
  const keys = order.length ? order : [...byTicker.keys()];
  const seen = new Set<string>();
  const next: FundEstimateView[] = [];
  for (const raw of keys) {
    const ticker = raw.trim().toUpperCase();
    if (!ticker || seen.has(ticker)) continue;
    seen.add(ticker);
    const fund = byTicker.get(ticker);
    if (fund) next.push(fund);
  }
  return next;
}

/** Exact ticker hit from `/api/funds`. Null when the page has no identity row. */
export function pickFundViewFromSearch(
  items: unknown[],
  ticker: string,
): FundEstimateView | null {
  const key = ticker.trim().toUpperCase();
  if (!key) return null;
  for (const item of items) {
    if (!item || typeof item !== "object") continue;
    const row = item as Partial<FundEstimateView>;
    if (String(row.ticker ?? "").trim().toUpperCase() !== key) continue;
    if (!row.fundName && !row.id) continue;
    return row as FundEstimateView;
  }
  return null;
}

export function taxRatesEqual(left: TaxRates, right: TaxRates): boolean {
  return (
    left.ordinary_income === right.ordinary_income &&
    left.long_term_capital_gains === right.long_term_capital_gains &&
    left.short_term_capital_gains === right.short_term_capital_gains &&
    left.qualified_dividend === right.qualified_dividend &&
    left.state === right.state
  );
}

/** True when calendar-year / pair fetches still match the on-screen holding + rates. */
export function compareInputsMatch(
  loaded: { holdingDollars: number; taxRates: TaxRates; combine: boolean },
  holdingDollars: number,
  taxRates: TaxRates,
  combine: boolean,
): boolean {
  return (
    loaded.holdingDollars === holdingDollars &&
    loaded.combine === combine &&
    taxRatesEqual(loaded.taxRates, taxRates)
  );
}

function normalizeTicker(value: string | null | undefined): string {
  return value?.trim().toUpperCase() ?? "";
}

export function emptyCompareSlots(): string[] {
  return Array.from({ length: COMPARE_SLOT_COUNT }, () => "");
}

export type CompareQueryParams = {
  tickers?: string | string[];
  ticker?: string | string[];
  left?: string | string[];
  right?: string | string[];
};

/** Split `AGTHX,AMCPX` or repeated query values into tickers. */
export function splitCompareTickerList(
  value: string | string[] | undefined | null,
): string[] {
  const parts = Array.isArray(value) ? value : value != null ? [value] : [];
  const tickers: string[] = [];
  for (const part of parts) {
    for (const raw of String(part).split(/[,\s]+/)) {
      const ticker = normalizeTicker(raw);
      if (ticker) tickers.push(ticker);
    }
  }
  return tickers;
}

/**
 * Deep-link tickers for Compare slots.
 * Prefers `tickers` / `ticker`, then legacy `left` / `right`. Unique, max 4.
 */
export function parseCompareQueryTickers(params: CompareQueryParams = {}): string[] {
  return filledCompareTickers([
    ...splitCompareTickerList(params.tickers),
    ...splitCompareTickerList(params.ticker),
    ...splitCompareTickerList(params.left),
    ...splitCompareTickerList(params.right),
  ]).slice(0, COMPARE_SLOT_COUNT);
}

/** `/compare?tickers=AGTHX` or `/compare` when empty. */
export function compareTickersPath(
  tickers: Array<string | undefined | null> = [],
): string {
  const filled = parseCompareQueryTickers({
    tickers: tickers.filter((ticker): ticker is string => Boolean(ticker)),
  });
  if (filled.length === 0) return "/compare";
  return `/compare?tickers=${filled.map(encodeURIComponent).join(",")}`;
}

/** Query params may prefill the first slots. A plain /compare visit stays empty. */
export function padCompareSlots(tickers: Array<string | undefined | null> = []): string[] {
  const slots = emptyCompareSlots();
  const seen = new Set<string>();
  let index = 0;
  for (const raw of tickers) {
    if (index >= COMPARE_SLOT_COUNT) break;
    const ticker = normalizeTicker(raw);
    if (!ticker || seen.has(ticker)) continue;
    seen.add(ticker);
    slots[index] = ticker;
    index += 1;
  }
  return slots;
}

export function filledCompareTickers(slots: string[]): string[] {
  const seen = new Set<string>();
  const next: string[] = [];
  for (const slot of slots) {
    const ticker = normalizeTicker(slot);
    if (!ticker || seen.has(ticker)) continue;
    seen.add(ticker);
    next.push(ticker);
    if (next.length >= COMPARE_SLOT_COUNT) break;
  }
  return next;
}

export function setCompareSlot(
  slots: string[],
  index: number,
  ticker: string,
): string[] {
  if (index < 0 || index >= COMPARE_SLOT_COUNT) return slots;
  const next = [...slots];
  const key = normalizeTicker(ticker);
  if (key && next.some((slot, slotIndex) => slotIndex !== index && normalizeTicker(slot) === key)) {
    return slots;
  }
  next[index] = key;
  return next;
}

export function growthFundsFromSlots(
  slots: string[],
  funds: FundEstimateView[] = [],
): CompareGrowthFund[] {
  return filledCompareTickers(slots).map((ticker) => {
    const match = funds.find((fund) => fund.ticker.toUpperCase() === ticker);
    return {
      ticker,
      label: ticker,
      fundIdentifier: match?.ticker ?? ticker,
      fundFamily: match?.family,
      fundName: match?.fundName,
      navPerShare: match && match.nav > 0 ? match.nav : undefined,
    };
  });
}

/**
 * Upcoming rows for Compare tickers. Unpaid announced with a future
 * Announced date only. Past / blank announced holdings are omitted —
 * never an Awaiting Estimate placeholder, never from paidHistory.
 */
export function upcomingRowsFromCompareTickers(
  loaded: Array<{
    ticker: string;
    fund?: FundEstimateView | null;
    upcoming?: CompareUpcomingHint | null;
    holdingDollars?: number | null;
    navPerShare?: number | null;
  }>,
  today = utcToday(),
): UpcomingRow[] {
  return loaded
    .map((item, index) =>
      upcomingRowForCompareTicker({
        ticker: item.ticker,
        fund: item.fund,
        upcoming: item.upcoming,
        holdingDollars: item.holdingDollars,
        navPerShare: item.navPerShare,
        index,
        today,
      }),
    )
    .filter((row) => row.available);
}

export function upcomingRowForCompareTicker(input: {
  ticker: string;
  fund?: FundEstimateView | null;
  upcoming?: CompareUpcomingHint | null;
  index: number;
  holdingDollars?: number | null;
  navPerShare?: number | null;
  today?: string;
}): UpcomingRow {
  const ticker = normalizeTicker(input.ticker) || input.ticker;
  const fund = input.fund ?? null;
  const today = input.today ?? utcToday();
  const catalogUpcoming = catalogIsUnpaidAnnounced(fund, today);
  // Live compare summary has no ex-date. Do not keep a row in Upcoming after
  // catalog ex-date has passed (payable may still be ahead).
  const liveAnnouncedDate = input.upcoming?.asOf ?? null;
  const announced =
    Boolean(input.upcoming?.announced) &&
    !catalogExHasPassed(fund, today) &&
    isFutureAnnouncedDate(liveAnnouncedDate, today);
  const available = announced || catalogUpcoming;
  const holdingDollars =
    input.holdingDollars != null && input.holdingDollars > 0
      ? input.holdingDollars
      : null;
  const nav =
    input.navPerShare != null && input.navPerShare > 0
      ? input.navPerShare
      : fund != null && fund.nav > 0
        ? fund.nav
        : null;
  // Manager unpaid prelim $/share only. Paid/final catalog amounts stay off Upcoming.
  const perShare =
    catalogUpcoming && fund && Number.isFinite(fund.estimatedDistributionAmount)
      ? fund.estimatedDistributionAmount
      : null;
  const ordinaryPerShare =
    catalogUpcoming && fund && Number.isFinite(fund.estimatedOrdinaryIncome)
      ? fund.estimatedOrdinaryIncome
      : null;
  const capitalGainsPerShare =
    catalogUpcoming && fund && Number.isFinite(fund.estimatedCapitalGains)
      ? fund.estimatedCapitalGains
      : null;
  const distDollars = upcomingDistDollarsFromPerShare(perShare, holdingDollars, nav);

  return {
    key: `compare-${ticker}-${input.index}`,
    ticker,
    fundName: fund?.fundName || ticker,
    side: "current",
    sideLabel: "Compare",
    distributionDollars: distDollars,
    distributionDollarsMin: null,
    distributionDollarsMax: null,
    holdingDollars,
    pctOfNav: upcomingPctOfNavFromPerShare(perShare, nav),
    navPerShare: nav,
    navAsOf: fund?.navAsOf ?? null,
    navOnDistributionDay: null,
    distributionPerShare: perShare,
    ordinaryPerShare,
    capitalGainsPerShare,
    estimatedTax: announced ? (input.upcoming?.dollars ?? null) : null,
    asOf: available
      ? catalogUpcoming
        ? fund?.asOfDate ?? null
        : input.upcoming?.asOf ?? null
      : null,
    announcedDate: available
      ? catalogUpcoming
        ? fund?.publishedAt ?? fund?.asOfDate ?? null
        : liveAnnouncedDate
      : null,
    recordDate: catalogUpcoming ? fund?.recordDate ?? null : null,
    exDate: catalogUpcoming ? fund?.exDate ?? null : null,
    payableDate: catalogUpcoming ? fund?.payableDate ?? null : null,
    stage: catalogUpcoming
      ? fund?.publicationStage ?? null
      : available
        ? input.upcoming?.publicationStage ?? null
        : null,
    bucket: available ? "upcoming" : "paid_history",
    heat: 0,
    available,
    covered: announced && input.upcoming?.dollars != null,
    inUniverse: Boolean(fund),
  };
}

/**
 * Unpaid future announcement only. Do not use `isUpcomingFund` here — that
 * gate drops manager-published $0 as a catalog leftover. Advisors want
 * announced zeros. Identity / paid / final / past-event / past-or-blank
 * announced rows still fail. Awaiting Estimate copy is the empty module
 * state — never a per-ticker placeholder row.
 */
function catalogDistributionRow(fund: FundEstimateView) {
  return {
    distribution_dollars: fund.estimatedDistributionAmount,
    estimated_tax: null,
    as_of: fund.asOfDate,
    announced_date: fund.publishedAt,
    record_date: fund.recordDate,
    ex_date: fund.exDate,
    payable_date: fund.payableDate,
    publication_stage: fund.publicationStage,
  };
}

function catalogIsUnpaidAnnounced(
  fund?: FundEstimateView | null,
  today = utcToday(),
): boolean {
  if (!fund) return false;
  const row = catalogDistributionRow(fund);
  return (
    publicationBucket(row, today) === "upcoming" &&
    isFutureAnnouncedDate(announcedDateOf(row), today)
  );
}

/** True when catalog dates say the unpaid announce already went ex. */
function catalogExHasPassed(
  fund?: FundEstimateView | null,
  today = utcToday(),
): boolean {
  if (!fund) return false;
  return publicationBucket(catalogDistributionRow(fund), today) === "paid_history";
}
