/**
 * Data GET /funds/lookup?ticker= — coverage_status + Add to universe.
 * 200 found (awaiting_estimate | estimate_announced). 404 not_in_universe.
 */

import { fetchDataApi } from "@/lib/data-api/fetch";
import {
  parseFundLookupResponse,
  type FundLookupResult,
} from "@/lib/data-api/fund-lookup-parse";
import { normalizeTickerSymbol } from "@/lib/data-api/request-ticker";

export type {
  FundLookupFound,
  FundLookupMiss,
  FundLookupResult,
  FundLookupUnavailable,
} from "@/lib/data-api/fund-lookup-parse";
export { parseFundLookupResponse } from "@/lib/data-api/fund-lookup-parse";

export async function loadFundLookupFromDataApi(
  ticker: string,
): Promise<FundLookupResult> {
  const key = normalizeTickerSymbol(ticker);
  if (!key) {
    return {
      kind: "not_in_universe",
      ticker: "",
      addToUniverse: "POST /request/ticker",
    };
  }
  try {
    const response = await fetchDataApi(
      `/funds/lookup?ticker=${encodeURIComponent(key)}`,
    );
    const body = await response.json().catch(() => null);
    return parseFundLookupResponse(response.status, body, key);
  } catch {
    return { kind: "unavailable" };
  }
}
