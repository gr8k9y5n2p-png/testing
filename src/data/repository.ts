import { getFacets, getHighlights, searchFunds } from "./queries";
import {
  clampOffset,
  clampPageSize,
  paginateViews,
  type FundPageQuery,
  type FundPageResult,
} from "./pagination";
import type {
  DistributionRepository,
  Facets,
  FundEstimateView,
  HighlightSets,
  SearchFilters,
} from "./types";
import { loadFundsFromDataApi } from "@/lib/data-api/distributions";
import { isRemoteDataApi } from "@/lib/data-api/config";
import { loadFundPageFromDataApi } from "@/lib/data-api/funds-page";

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

  async searchPage(query: FundPageQuery = {}): Promise<FundPageResult> {
    const live = await loadFundPageFromDataApi(query);
    if (live) return live;
    // Remote /funds 404 or down: empty page. Never dump /distributions rows
    // into unique funds for Sample Estimates.
    if (isRemoteDataApi()) {
      return {
        items: [],
        total: 0,
        limit: clampPageSize(query.limit),
        offset: clampOffset(query.offset),
      };
    }
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
