import type { FundEstimateView } from "../../data/types.ts";
import { MAX_GROWTH_FUNDS } from "../charts/series-colors.ts";
import { trailingCalendarPeriods } from "./compare-request.ts";
import type { CompareIllustration, CompareResponse } from "./compare-types.ts";
import { UI_DEFAULT_TAX_RATES, type TaxRates } from "./types.ts";
import {
  upcomingDistDollarsFromPerShare,
  upcomingPctOfNavFromPerShare,
} from "./portfolio-compare-copy.ts";
import {
  publicationBucket,
  type UpcomingRow,
} from "./publication-stage.ts";
import {
  comparePeriodCalendarYear,
  illustrationIsUnmatched,
  toTaxDragPeriods,
} from "./tax-drag-map.ts";

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

export type CompareAnnualRow = {
  key: string;
  ticker: string;
  kind: "tax" | "distribution";
  label: string;
  cells: Array<number | null>;
};

export type CompareAnnualTableModel = {
  years: number[];
  groups: {
    ticker: string;
    rows: CompareAnnualRow[];
  }[];
};

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

export function compareHistoryYears(nowYear = new Date().getUTCFullYear()): number[] {
  return trailingCalendarPeriods(nowYear)
    .map((period) => period.year)
    .sort((a, b) => b - a);
}

function numericOrNull(value: unknown): number | null {
  if (value == null || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function illustrationCalendarYear(illustration: CompareIllustration | null | undefined): number {
  if (!illustration) return 0;
  const extra = illustration as CompareIllustration & { year?: unknown; as_of?: unknown };
  return (
    comparePeriodCalendarYear({ year: extra.year, as_of: extra.as_of, label: illustration.label }) ||
    0
  );
}

function distributionFromIllustration(
  illustration: CompareIllustration | null | undefined,
): number | null {
  if (!illustration || illustrationIsUnmatched(illustration)) return null;
  return numericOrNull(illustration.totals?.distribution_dollars);
}

/** Calendar-year distribution $. Unmatched / missing → null (N/A), never $0. */
export function toDistributionPeriods(response: CompareResponse | null): Array<{
  year: number;
  value: number | null;
}> {
  if (!response) return [];
  const byYear = new Map<number, number | null>();
  const write = (year: number, value: number | null) => {
    if (!Number.isFinite(year) || year <= 0) return;
    const prior = byYear.get(year);
    if (prior != null && value == null) return;
    byYear.set(year, value);
  };

  for (const period of response.periods) {
    const periodYear = comparePeriodCalendarYear(period);
    const leftValue = distributionFromIllustration(period.left);
    const rightValue = distributionFromIllustration(period.right);
    if (response.mode !== "yoy") {
      write(periodYear, leftValue);
      continue;
    }
    const olderFromLabel = illustrationCalendarYear(period.left);
    const newerFromLabel = illustrationCalendarYear(period.right);
    const calendarRow =
      periodYear > 0 && olderFromLabel === periodYear && newerFromLabel === periodYear;
    if (calendarRow) {
      write(periodYear, rightValue ?? leftValue);
      continue;
    }
    const olderYear = olderFromLabel || (periodYear > 1 ? periodYear - 1 : 0);
    const newerYear = newerFromLabel || periodYear;
    if (olderYear > 0) write(olderYear, leftValue);
    if (newerYear > 0) write(newerYear, rightValue);
  }

  return [...byYear.entries()]
    .map(([year, value]) => ({ year, value }))
    .sort((a, b) => a.year - b.year);
}

export function buildCompareAnnualTable(
  loaded: Array<{ ticker: string; tax: CompareResponse | null }>,
  years: number[] = compareHistoryYears(),
): CompareAnnualTableModel {
  return {
    years,
    groups: loaded.map((item) => {
      const taxByYear = new Map(
        (item.tax ? toTaxDragPeriods(item.tax, "tax_dollars", "auto") : []).map((point) => [
          point.year,
          point.value,
        ]),
      );
      const distByYear = new Map(
        toDistributionPeriods(item.tax).map((point) => [point.year, point.value]),
      );
      return {
        ticker: item.ticker,
        rows: [
          {
            key: `${item.ticker}-tax`,
            ticker: item.ticker,
            kind: "tax" as const,
            label: "Tax $",
            cells: years.map((year) => (taxByYear.has(year) ? (taxByYear.get(year) ?? null) : null)),
          },
          {
            key: `${item.ticker}-dist`,
            ticker: item.ticker,
            kind: "distribution" as const,
            label: "Dist $",
            cells: years.map((year) => (distByYear.has(year) ? (distByYear.get(year) ?? null) : null)),
          },
        ],
      };
    }),
  };
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

/** has_estimate false is never Upcoming — every fund, not a per-ticker exception. */
function catalogIsUnpaidAnnounced(fund?: FundEstimateView | null): boolean {
  if (!fund || fund.hasEstimate === false || fund.bucket !== "upcoming") {
    return false;
  }
  return (
    publicationBucket(
      {
        distribution_dollars: null,
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
