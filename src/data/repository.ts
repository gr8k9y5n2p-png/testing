import { getFacets, getHighlights, searchFunds, withPeerContext } from "./queries";
import { SAMPLE_FUNDS } from "./seed";
import type {
  DistributionRepository,
  Facets,
  FundEstimateView,
  HighlightSets,
  SearchFilters,
} from "./types";
import { loadFundsFromDataApi } from "@/lib/data-api/distributions";

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
  const tickers = new Set(apiFunds.map((fund) => fund.ticker.toUpperCase()));
  return [...apiFunds, ...seedFunds.filter((fund) => !tickers.has(fund.ticker.toUpperCase()))];
}

export async function getDistributionRepository(): Promise<DistributionRepository> {
  const seed = withPeerContext(SAMPLE_FUNDS);
  const apiFunds = await loadFundsFromDataApi();
  if (apiFunds?.length) {
    return new SeedDistributionRepository(mergeFunds(apiFunds, seed));
  }
  return new SeedDistributionRepository(seed);
}
