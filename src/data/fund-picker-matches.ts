import { mergeFundLists } from "./hydrate-funds.ts";
import { searchFunds } from "./queries.ts";
import type { FundEstimateView } from "./types.ts";

const PICKER_MATCH_LIMIT = 8;

/**
 * Search a fund matches: local catalog plus GET /api/funds hits.
 * Do not require Upcoming / has_estimate — identity rows must still be
 * selectable so Dollar Illustration can open (FBGRX).
 */
export function fundPickerMatches(
  funds: FundEstimateView[],
  remoteFunds: FundEstimateView[],
  query: string,
): FundEstimateView[] {
  const q = query.trim();
  if (!q) return [];
  return mergeFundLists(searchFunds(funds, { query: q }), remoteFunds).slice(
    0,
    PICKER_MATCH_LIMIT,
  );
}
