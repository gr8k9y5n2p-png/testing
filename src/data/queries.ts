import type {
  Facets,
  FundEstimate,
  FundEstimateView,
  HighlightSets,
  SearchFilters,
} from "./types";

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

export function getHighlights(
  funds: FundEstimateView[],
  limit = 5,
): HighlightSets {
  const mostRecent = [...funds]
    .sort((a, b) => {
      const byPublished = b.publishedAt.localeCompare(a.publishedAt);
      if (byPublished !== 0) return byPublished;
      return a.fundName.localeCompare(b.fundName);
    })
    .slice(0, limit);

  const largest = [...funds]
    .sort((a, b) => {
      const byPct = b.estimatedDistributionPctNav - a.estimatedDistributionPctNav;
      if (byPct !== 0) return byPct;
      return a.fundName.localeCompare(b.fundName);
    })
    .slice(0, limit);

  const aboveCategory = funds
    .filter((fund) => fund.vsCategoryPctNav >= OUTLIER_THRESHOLD_PP)
    .sort((a, b) => b.vsCategoryPctNav - a.vsCategoryPctNav)
    .slice(0, limit);

  const belowCategory = funds
    .filter((fund) => fund.vsCategoryPctNav <= -OUTLIER_THRESHOLD_PP)
    .sort((a, b) => a.vsCategoryPctNav - b.vsCategoryPctNav)
    .slice(0, limit);

  return { mostRecent, largest, aboveCategory, belowCategory };
}
