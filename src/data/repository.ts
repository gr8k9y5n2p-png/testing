import { getFacets, getHighlights, searchFunds, withPeerContext } from "./queries";
import { paginateViews, type FundPageQuery, type FundPageResult } from "./pagination";
import { SAMPLE_FUNDS } from "./seed";
import type {
  DistributionRepository,
  Facets,
  FundEstimateView,
  HighlightSets,
  SearchFilters,
} from "./types";
import { loadFundsFromDataApi } from "@/lib/data-api/distributions";
import { loadFundPageFromDataApi } from "@/lib/data-api/funds-page";

/**
 * In-memory repository. Prefers GET /distributions from the Data API
 * (NEXT_PUBLIC_DATA_API_URL) when that host is up; seed fills tickers the
 * API does not yet return.
 */
export class SeedDistributionRepository implements DistributionRepository {
  private readonly views: FundEstimateView[];

  constructor(funds: FundEstimateView[]) {
    this.views = funds;
  }

  async search(filters: SearchFilters = {}): Promise<FundEstimateView[]> {
    return searchFunds(this.views, filters);
  }

  async searchPage(query: FundPageQuery = {}): Promise<FundPageResult> {
    const live = await loadFundPageFromDataApi(query);
    if (live) return live;
    return paginateViews(this.views, query);
  }

  async highlights(limit = 5): Promise<HighlightSets> {
    return getHighlights(this.views, limit);
  }

  async facets(): Promise<Facets> {
    return getFacets(this.views);
  }

  async getById(id: string): Promise<FundEstimateView | null> {
    return this.views.find((fund) => fund.id === id) ?? null;
  }
}

function mergeFunds(
  apiFunds: FundEstimateView[],
  seedFunds: FundEstimateView[],
): FundEstimateView[] {
  const seedByTicker = new Map(
    seedFunds.map((fund) => [fund.ticker.toUpperCase(), fund]),
  );
  const mergedApi = apiFunds.map((fund) => {
    const seed = seedByTicker.get(fund.ticker.toUpperCase());
    if (!seed) return fund;
    return {
      ...fund,
      nav: fund.nav > 0 ? fund.nav : seed.nav,
      category: fund.category !== "—" ? fund.category : seed.category,
      recordDate: fund.recordDate ?? seed.recordDate,
      exDate: fund.exDate ?? seed.exDate,
      payableDate: fund.payableDate ?? seed.payableDate,
      paidHistory: fund.paidHistory.length ? fund.paidHistory : seed.paidHistory,
    };
  });
  const tickers = new Set(mergedApi.map((fund) => fund.ticker.toUpperCase()));
  return [
    ...mergedApi,
    ...seedFunds.filter((fund) => !tickers.has(fund.ticker.toUpperCase())),
  ];
}

export async function getDistributionRepository(): Promise<DistributionRepository> {
  const seed = withPeerContext(SAMPLE_FUNDS);
  const apiFunds = await loadFundsFromDataApi();
  if (apiFunds?.length) {
    return new SeedDistributionRepository(mergeFunds(apiFunds, seed));
  }
  return new SeedDistributionRepository(seed);
}
