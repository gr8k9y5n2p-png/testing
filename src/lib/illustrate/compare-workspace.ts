import type { FundEstimateView } from "../../data/types.ts";
import { MAX_GROWTH_FUNDS } from "../charts/series-colors.ts";
import { UI_DEFAULT_TAX_RATES, type TaxRates } from "./types.ts";
import {
  upcomingDistDollarsFromPerShare,
  upcomingPctOfNavFromPerShare,
} from "./portfolio-compare-copy.ts";
import {
  publicationBucket,
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

export const COMPARE_SLOT_COUNT = MAX_GROWTH_FUNDS;

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
 * Prefers `tickers` / `ticker`, then legacy `left` / `right`. Unique, max 6.
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
 * Upcoming rows for Compare tickers. Unpaid announced only.
 * Catalog dates attach only when the live row is still upcoming — never from paidHistory.
 */
export function upcomingRowsFromCompareTickers(
  loaded: Array<{
    ticker: string;
    fund?: FundEstimateView | null;
    upcoming?: CompareUpcomingHint | null;
    holdingDollars?: number | null;
    navPerShare?: number | null;
  }>,
): UpcomingRow[] {
  return loaded.map((item, index) =>
    upcomingRowForCompareTicker({
      ticker: item.ticker,
      fund: item.fund,
      upcoming: item.upcoming,
      holdingDollars: item.holdingDollars,
      navPerShare: item.navPerShare,
      index,
    }),
  );
}

export function upcomingRowForCompareTicker(input: {
  ticker: string;
  fund?: FundEstimateView | null;
  upcoming?: CompareUpcomingHint | null;
  index: number;
  holdingDollars?: number | null;
  navPerShare?: number | null;
}): UpcomingRow {
  const ticker = normalizeTicker(input.ticker) || input.ticker;
  const fund = input.fund ?? null;
  const catalogUpcoming = catalogIsUnpaidAnnounced(fund);
  const announced = Boolean(input.upcoming?.announced);
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
    distributionPerShare: perShare,
    ordinaryPerShare,
    capitalGainsPerShare,
    estimatedTax: announced ? (input.upcoming?.dollars ?? null) : null,
    asOf: catalogUpcoming ? fund?.asOfDate ?? null : input.upcoming?.asOf ?? null,
    announcedDate: catalogUpcoming
      ? fund?.publishedAt ?? fund?.asOfDate ?? null
      : input.upcoming?.asOf ?? null,
    recordDate: catalogUpcoming ? fund?.recordDate ?? null : null,
    exDate: catalogUpcoming ? fund?.exDate ?? null : null,
    payableDate: catalogUpcoming ? fund?.payableDate ?? null : null,
    stage: catalogUpcoming
      ? fund?.publicationStage ?? null
      : input.upcoming?.publicationStage ?? null,
    bucket: available ? "upcoming" : "paid_history",
    heat: 0,
    available,
    covered: announced && input.upcoming?.dollars != null,
  };
}

/**
 * Unpaid future announcement only. Do not use `isUpcomingFund` here — that
 * gate drops manager-published $0 as a catalog leftover. Advisors want
 * announced zeros. Identity / paid / final / past-event rows still fail
 * `publicationBucket`. Undisclosed only when there is no unpaid publish.
 */
function catalogIsUnpaidAnnounced(fund?: FundEstimateView | null): boolean {
  if (!fund) return false;
  return (
    publicationBucket(
      {
        distribution_dollars: fund.estimatedDistributionAmount,
        estimated_tax: null,
        as_of: fund.asOfDate,
        announced_date: fund.publishedAt,
        record_date: fund.recordDate,
        ex_date: fund.exDate,
        payable_date: fund.payableDate,
        publication_stage: fund.publicationStage,
      },
    ) === "upcoming"
  );
}
