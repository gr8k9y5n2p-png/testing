import { pctOfNavForFund } from "../lib/illustrate/nav-math.ts";
import {
  chicagoTodayIso,
  isoDate,
  normalizePublicationStage,
  splitFundsByBucket,
} from "./distribution-bucket.ts";
import {
  mergeFundLists,
  mergeFundWithDistributions,
  paidEventsForFund,
  preferFinalPaidEvents,
} from "./hydrate-funds.ts";
import { collectTaxYearsFromFunds } from "./tax-years.ts";
import type {
  DistributionBucket,
  Facets,
  FundEstimate,
  FundEstimateView,
  HighlightSets,
  PaidDistributionEvent,
  SearchFilters,
} from "./types";

export { splitFundsByBucket } from "./distribution-bucket.ts";

/** Absolute percentage-point gap vs. category average to qualify as an outlier. */
export const OUTLIER_THRESHOLD_PP = 2.25;

/**
 * Minimum unpaid announced funds in one calendar year before Highlights
 * uses that year. Fewer is a soft empty — never invent or backfill
 * another year's paid / YE rows.
 */
export const HIGHLIGHTS_MIN_YEAR_PEERS = 2;

export function emptyHighlightSets(): HighlightSets {
  return {
    mostRecent: [],
    largest: [],
    aboveCategory: [],
    belowCategory: [],
  };
}

/**
 * Market / calendar year for Highlights scoping. Ex/record/payable are the
 * distribution year; `as_of` and stored `distributionYear` are fallbacks.
 * Never invent a year.
 */
export function highlightsCalendarYear(
  fund: Pick<
    FundEstimate,
    "exDate" | "recordDate" | "payableDate" | "asOfDate" | "distributionYear"
  >,
): number {
  const raw =
    isoDate(fund.exDate) ??
    isoDate(fund.recordDate) ??
    isoDate(fund.payableDate) ??
    isoDate(fund.asOfDate);
  const year = Number((raw ?? "").slice(0, 4));
  return year || fund.distributionYear;
}

/**
 * Latest calendar year with enough unpaid announced peers. Years with
 * only a singleton (or nothing) are not mixed in — callers soft-empty.
 */
export function pickHighlightsCalendarYear<T extends FundEstimate>(
  funds: T[],
  minPeers = HIGHLIGHTS_MIN_YEAR_PEERS,
): number | null {
  const counts = new Map<number, number>();
  for (const fund of funds) {
    const year = highlightsCalendarYear(fund);
    if (!Number.isFinite(year) || year <= 0) continue;
    counts.set(year, (counts.get(year) ?? 0) + 1);
  }
  const years = [...counts.keys()].sort((a, b) => b - a);
  for (const year of years) {
    if ((counts.get(year) ?? 0) >= minPeers) return year;
  }
  return null;
}

export function roundTo(value: number, decimals: number): number {
  const factor = 10 ** decimals;
  return Math.round(value * factor) / factor;
}

export function categoryPeerKey(fund: Pick<FundEstimate, "category" | "distributionYear">): string {
  return `${fund.distributionYear}|${fund.category}`;
}

export function computeCategoryAverages(
  funds: FundEstimate[],
): Map<string, number> {
  const buckets = new Map<string, { sum: number; count: number }>();

  for (const fund of funds) {
    const pct = pctOfNavForFund(fund);
    if (pct == null) continue;
    const key = categoryPeerKey(fund);
    const bucket = buckets.get(key) ?? { sum: 0, count: 0 };
    bucket.sum += pct;
    bucket.count += 1;
    buckets.set(key, bucket);
  }

  const averages = new Map<string, number>();
  for (const [key, bucket] of buckets) {
    averages.set(key, bucket.count === 0 ? 0 : bucket.sum / bucket.count);
  }
  return averages;
}

export function withPeerContext(funds: FundEstimate[]): FundEstimateView[] {
  const averages = computeCategoryAverages(funds);
  return funds.map((fund) => {
    const pct = pctOfNavForFund(fund);
    const categoryAveragePctNav = averages.get(categoryPeerKey(fund)) ?? 0;
    return {
      ...fund,
      estimatedDistributionPctNav: pct ?? fund.estimatedDistributionPctNav,
      categoryAveragePctNav: roundTo(categoryAveragePctNav, 4),
      vsCategoryPctNav: roundTo(
        (pct ?? fund.estimatedDistributionPctNav) - categoryAveragePctNav,
        4,
      ),
    };
  });
}

export function searchFunds(
  funds: FundEstimateView[],
  filters: SearchFilters = {},
): FundEstimateView[] {
  const query = filters.query?.trim().toLowerCase();
  const tokens = query ? query.split(/\s+/).filter(Boolean) : [];

  return funds.filter((fund) => {
    if (filters.family && fund.family !== filters.family) return false;
    if (filters.category && fund.category !== filters.category) return false;
    if (filters.year && fund.distributionYear !== filters.year) return false;

    if (tokens.length === 0) return true;

    const haystack = [
      fund.fundName,
      fund.ticker,
      fund.cusip,
      fund.family,
      fund.category,
      String(fund.distributionYear),
      fund.shareClass,
    ]
      .join(" ")
      .toLowerCase();

    return tokens.every((token) => haystack.includes(token));
  });
}

export function getFacets(funds: FundEstimate[]): Facets {
  const families = [...new Set(funds.map((fund) => fund.family))].sort();
  const categories = [...new Set(funds.map((fund) => fund.category))].sort();
  return { families, categories, years: collectTaxYearsFromFunds(funds) };
}

function hasPaidHistorySignal(fund: FundEstimateView): boolean {
  if ((fund.paidHistory?.length ?? 0) > 0) return true;
  if (fund.estimatedDistributionAmount) return true;
  if (fund.recordDate || fund.exDate || fund.payableDate) return true;
  const stage = (fund.publicationStage ?? "").trim().toLowerCase();
  return stage === "paid" || stage === "final";
}

/** Calendar year for a paid / final row. Ex, else payable, else record, else as_of. */
export function paidHistoryYearOf(
  event: Pick<
    PaidDistributionEvent,
    "exDate" | "payableDate" | "recordDate" | "asOfDate" | "distributionYear"
  >,
): number {
  const raw = event.exDate ?? event.payableDate ?? event.recordDate ?? event.asOfDate;
  const year = Number((raw ?? "").slice(0, 4));
  return year || event.distributionYear;
}

/** Chicago calendar year for Search Paid History default / year-end wipe. */
export function currentPaidHistoryYear(now = new Date()): number {
  return Number(chicagoTodayIso(now).slice(0, 4));
}

/** Dollar Illustration Paid History is the prior Chicago calendar year only. */
export function priorPaidHistoryYear(now = new Date()): number {
  return currentPaidHistoryYear(now) - 1;
}

/**
 * Finals / paid from `/distributions` for the prior calendar year.
 * The calendar-year matrix includes the current year separately
 * (Awaiting / — until an unpaid announced estimate arrives).
 */
export function illustrationPriorYearPaidEvents(
  fund: Parameters<typeof paidEventsForFund>[0],
  now = new Date(),
): ReturnType<typeof paidEventsForFund> {
  const year = priorPaidHistoryYear(now);
  return paidEventsForFund(fund).filter((event) => {
    const stage = normalizePublicationStage(event.publicationStage);
    if (stage !== "final" && stage !== "paid") return false;
    return paidHistoryYearOf(event) === year;
  });
}

/**
 * Search table book: Upcoming is the full unpaid announced universe.
 * A selected ticker hydrates in place for detail / Paid History — it must
 * never replace or filter away the rest of the unpaid set.
 */
export function buildSearchTableFunds(
  catalog: FundEstimateView[],
  pageItems: FundEstimateView[] = [],
  filters: SearchFilters = {},
  selectedTicker?: string,
): FundEstimateView[] {
  const family = filters.family;
  const category = filters.category;
  const upcoming = splitFundsByBucket(
    mergeFundLists(pageItems, catalog),
  ).upcoming.filter((fund) => {
    if (family && fund.family !== family) return false;
    if (category && fund.category !== category) return false;
    return true;
  });

  const hydratedPage = pageItems.map((item) => {
    const fromCatalog = catalog.find(
      (fund) =>
        fund.ticker.trim().toUpperCase() === item.ticker.trim().toUpperCase() &&
        item.ticker.trim() &&
        item.ticker !== "—",
    );
    return fromCatalog ? mergeFundWithDistributions(item, fromCatalog) : item;
  });

  const selectedKey = selectedTicker?.trim().toUpperCase();
  const focused = selectedKey
    ? [...pageItems, ...catalog].filter(
        (fund) => fund.ticker.trim().toUpperCase() === selectedKey,
      )
    : [];

  return mergeFundLists(hydratedPage, [...upcoming, ...focused]);
}

export function paidHistoryViews(
  funds: FundEstimateView[],
  year?: number,
): FundEstimateView[] {
  const rows: FundEstimateView[] = [];
  for (const fund of funds) {
    const extras = preferFinalPaidEvents(fund.paidHistory ?? []);
    if (fund.bucket === "paid") {
      if (hasPaidHistorySignal(fund)) rows.push(fund);
      for (const event of extras) {
        rows.push(fundFromPaidEvent(fund, event));
      }
      continue;
    }
    for (const event of extras) {
      rows.push(fundFromPaidEvent(fund, event));
    }
  }
  const scoped =
    year == null
      ? rows
      : rows.filter((row) => paidHistoryYearOf(row) === year);
  return scoped.sort((a, b) => {
    const byDate = (b.payableDate ?? b.exDate ?? b.asOfDate).localeCompare(
      a.payableDate ?? a.exDate ?? a.asOfDate,
    );
    if (byDate !== 0) return byDate;
    return a.ticker.localeCompare(b.ticker);
  });
}

export function fundFromPaidEvent(
  fund: FundEstimateView,
  event: PaidDistributionEvent,
): FundEstimateView {
  return {
    ...fund,
    id: `${fund.id}:paid:${event.asOfDate}:${event.exDate ?? ""}`,
    asOfDate: event.asOfDate,
    publishedAt: event.asOfDate,
    recordDate: event.recordDate,
    exDate: event.exDate,
    payableDate: event.payableDate,
    publicationStage: event.publicationStage,
    bucket: "paid" satisfies DistributionBucket,
    estimatedDistributionAmount: event.estimatedDistributionAmount,
    estimatedOrdinaryIncome: event.estimatedOrdinaryIncome,
    estimatedCapitalGains: event.estimatedCapitalGains,
    estimatedDistributionPctNav: event.estimatedDistributionPctNav,
    publishedPctOfNav: event.publishedPctOfNav ?? null,
    navOnDistributionDay: event.navOnDistributionDay ?? null,
    navOnDistributionDayAsOf: event.navOnDistributionDayAsOf ?? null,
    navOnDistributionDaySource: event.navOnDistributionDaySource ?? null,
    distributionYear: event.distributionYear,
    paidHistory: [],
  };
}

function highlightRowsFromPool(
  pool: FundEstimateView[],
  limit: number,
): HighlightSets {
  // Largest / Most Recent live in a fixed-height scroller. Keep enough
  // same-day weekly filings to scroll; Versus-category stays at `limit`.
  const scrollerLimit = Math.max(limit, 60);
  const mostRecent = [...pool]
    .sort((a, b) => {
      const byPublished = b.asOfDate.localeCompare(a.asOfDate);
      if (byPublished !== 0) return byPublished;
      return a.fundName.localeCompare(b.fundName);
    })
    .slice(0, scrollerLimit);

  const largest = [...pool]
    .sort((a, b) => {
      const byPct =
        (pctOfNavForFund(b) ?? Number.NEGATIVE_INFINITY) -
        (pctOfNavForFund(a) ?? Number.NEGATIVE_INFINITY);
      if (byPct !== 0) return byPct;
      return a.fundName.localeCompare(b.fundName);
    })
    .slice(0, scrollerLimit);

  const aboveCategory = pool
    .filter((fund) => fund.vsCategoryPctNav >= OUTLIER_THRESHOLD_PP)
    .sort((a, b) => b.vsCategoryPctNav - a.vsCategoryPctNav)
    .slice(0, limit);

  const belowCategory = pool
    .filter((fund) => fund.vsCategoryPctNav <= -OUTLIER_THRESHOLD_PP)
    .sort((a, b) => a.vsCategoryPctNav - b.vsCategoryPctNav)
    .slice(0, limit);

  return { mostRecent, largest, aboveCategory, belowCategory };
}

/**
 * Search Highlights: unpaid future announced only, one calendar year
 * per module. Category-avg deltas are recomputed on that unpaid
 * same-year peer set — paid history and other years never mix in.
 */
export function getHighlights(
  funds: FundEstimateView[],
  limit = 5,
): HighlightSets {
  const { upcoming } = splitFundsByBucket(funds);
  const year = pickHighlightsCalendarYear(upcoming);
  if (year == null) return emptyHighlightSets();
  const scoped = upcoming.filter(
    (fund) => highlightsCalendarYear(fund) === year,
  );
  if (scoped.length < HIGHLIGHTS_MIN_YEAR_PEERS) return emptyHighlightSets();
  const pool = withPeerContext(scoped);
  return highlightRowsFromPool(pool, limit);
}
