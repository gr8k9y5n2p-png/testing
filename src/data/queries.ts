import { splitFundsByBucket } from "./distribution-bucket.ts";
import { preferFinalPaidEvents } from "./hydrate-funds.ts";
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
    const key = categoryPeerKey(fund);
    const bucket = buckets.get(key) ?? { sum: 0, count: 0 };
    bucket.sum += fund.estimatedDistributionPctNav;
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
    const categoryAveragePctNav = averages.get(categoryPeerKey(fund)) ?? 0;
    return {
      ...fund,
      categoryAveragePctNav: roundTo(categoryAveragePctNav, 4),
      vsCategoryPctNav: roundTo(
        fund.estimatedDistributionPctNav - categoryAveragePctNav,
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
  const years = [...new Set(funds.map((fund) => fund.distributionYear))].sort(
    (a, b) => b - a,
  );
  return { families, categories, years };
}

function hasPaidHistorySignal(fund: FundEstimateView): boolean {
  if ((fund.paidHistory?.length ?? 0) > 0) return true;
  if (fund.estimatedDistributionAmount) return true;
  if (fund.recordDate || fund.exDate || fund.payableDate) return true;
  const stage = (fund.publicationStage ?? "").trim().toLowerCase();
  return stage === "paid" || stage === "final";
}

export function paidHistoryViews(funds: FundEstimateView[]): FundEstimateView[] {
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
  return rows.sort((a, b) => {
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
    distributionYear: event.distributionYear,
    paidHistory: [],
  };
}

export function getHighlights(
  funds: FundEstimateView[],
  limit = 5,
): HighlightSets {
  const { upcoming } = splitFundsByBucket(funds);
  const pool = upcoming;
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
      const byPct = b.estimatedDistributionPctNav - a.estimatedDistributionPctNav;
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
