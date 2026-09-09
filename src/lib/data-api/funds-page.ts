import { mapFundsApiItem, type FundsApiItem } from "@/data/funds-list";
import {
  clampOffset,
  clampPageSize,
  fundPageSearchParams,
  type FundPageQuery,
  type FundPageResult,
} from "@/data/pagination";
import { isRemoteDataApi } from "@/lib/data-api/config";
import { fetchDataApi } from "@/lib/data-api/fetch";

export { mapFundsApiItem, type FundsApiItem } from "@/data/funds-list";

/**
 * Sample Estimates / Search unique-fund pages: Data `GET /funds` only.
 *
 *   GET /funds?limit=50&offset=0&q=&fund_family=
 *   → `{ items, limit, offset, total }`
 *
 * Do **not** client-aggregate `GET /distributions` into unique funds.
 * `/distributions` is distribution **rows**:
 *   GET /distributions?page=1&page_size=50
 *   → `{ items, page, page_size, total }` (max page_size 200)
 * Mapping if a row view needs it: limit ≡ page_size,
 * offset ≡ (page - 1) * page_size. Filters: q, fund_family, ticker,
 * publication_stage, dates. 404 / down → empty page (honest), not a dump.
 */
type PagePayload = {
  items?: unknown[];
  data?: unknown[];
  total?: number;
  count?: number;
  limit?: number;
  offset?: number;
};

function isFundsApiItem(row: unknown): row is FundsApiItem {
  if (!row || typeof row !== "object") return false;
  const record = row as Record<string, unknown>;
  return (
    "fund_name" in record ||
    "fund_identifier" in record ||
    "fundName" in record ||
    "ticker" in record
  );
}

export async function loadFundPageFromDataApi(
  query: FundPageQuery = {},
): Promise<FundPageResult | null> {
  if (!isRemoteDataApi()) return null;
  const params = fundPageSearchParams(query);
  try {
    const response = await fetchDataApi(`/funds?${params.toString()}`, {
      fallbackPath: `/funds?${params.toString()}`,
    });
    if (!response.ok) return null;
    const payload = (await response.json()) as PagePayload;
    const raw = Array.isArray(payload.items)
      ? payload.items
      : Array.isArray(payload.data)
        ? payload.data
        : [];
    if (!raw.every(isFundsApiItem)) return null;
    const items = raw.map((row) => mapFundsApiItem(row));
    const limit = clampPageSize(payload.limit ?? query.limit);
    const offset = clampOffset(payload.offset ?? query.offset);
    const total =
      typeof payload.total === "number"
        ? payload.total
        : typeof payload.count === "number"
          ? payload.count
          : items.length;
    return { items, total, limit, offset };
  } catch {
    return null;
  }
}
