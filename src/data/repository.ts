import { getFacets, getHighlights, searchFunds, withPeerContext } from "./queries";
import { SAMPLE_FUNDS } from "./seed";
import type {
  DistributionRepository,
  Facets,
  FundEstimateView,
  HighlightSets,
  SearchFilters,
} from "./types";

/**
 * In-memory repository backed by seeded sample estimates.
 * Prefer GET /distributions from the Data API (NEXT_PUBLIC_DATA_API_URL) when
 * that service is aggregated into this table model; until then the seed remains.
 */
export class SeedDistributionRepository implements DistributionRepository {
  private readonly views: FundEstimateView[];

  constructor(funds = SAMPLE_FUNDS) {
    this.views = withPeerContext(funds);
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

let singleton: SeedDistributionRepository | undefined;

export function getDistributionRepository(): DistributionRepository {
  singleton ??= new SeedDistributionRepository();
  return singleton;
}
