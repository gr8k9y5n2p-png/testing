import { getFacets, getHighlights, searchFunds } from "./queries";
import type {
  DistributionRepository,
  Facets,
  FundEstimateView,
  HighlightSets,
  SearchFilters,
} from "./types";
import { loadFundsFromDataApi } from "@/lib/data-api/distributions";

/**
 * In-memory repository over a fund list. Live Search / Sample Estimates /
 * highlights load this from GET /distributions only — never from seed.ts.
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

/** Build the live Search repo. Null / empty API → empty list, never seed. */
export function repositoryFromApiFunds(
  apiFunds: FundEstimateView[] | null | undefined,
): DistributionRepository {
  return new SeedDistributionRepository(apiFunds ?? []);
}

/**
 * Live Search / Sample Estimates / homepage highlights.
 * Uses GET /distributions (`NEXT_PUBLIC_DATA_API_URL`) only.
 * Down, empty, or uncovered → empty list. Never merge or fall back to seed.ts.
 */
export async function getDistributionRepository(): Promise<DistributionRepository> {
  const apiFunds = await loadFundsFromDataApi();
  return repositoryFromApiFunds(apiFunds);
}
