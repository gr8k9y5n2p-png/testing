import { aggregateDistributions, type DataDistribution } from "@/data/aggregate-distributions";
import { withPeerContext } from "@/data/queries";
import type { FundEstimateView } from "@/data/types";
import { fetchDataApi } from "@/lib/data-api/fetch";

export type { DataDistribution } from "@/data/aggregate-distributions";
export { aggregateDistributions } from "@/data/aggregate-distributions";

const DISTRIBUTION_PAGE_SIZE = 200;
const DISTRIBUTION_MAX_PAGES = 5;

export async function loadFundsFromDataApi(): Promise<FundEstimateView[] | null> {
  try {
    const items: DataDistribution[] = [];
    for (let page = 1; page <= DISTRIBUTION_MAX_PAGES; page += 1) {
      const response = await fetchDataApi(
        `/distributions?page_size=${DISTRIBUTION_PAGE_SIZE}&page=${page}`,
      );
      if (!response.ok) {
        return items.length ? withPeerContext(aggregateDistributions(items)) : null;
      }
      const payload = (await response.json()) as {
        items?: DataDistribution[];
        total?: number;
      };
      const pageItems = Array.isArray(payload.items) ? payload.items : [];
      items.push(...pageItems);
      if (pageItems.length < DISTRIBUTION_PAGE_SIZE) break;
      if (typeof payload.total === "number" && items.length >= payload.total) break;
    }
    if (!items.length) return null;
    return withPeerContext(aggregateDistributions(items));
  } catch {
    return null;
  }
}
