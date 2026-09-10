import { mergeFundLists } from "./hydrate-funds.ts";
import { searchFunds } from "./queries.ts";
import type { FundEstimateView } from "./types.ts";

const PICKER_MATCH_LIMIT = 8;

/**
 * Search a fund matches: local catalog plus GET /api/funds hits.
 * Do not require Upcoming / has_estimate — paid-only identity rows
 * (AGTHX: has_estimate=false, bucket=paid) must still be selectable.
 * The homepage SSR book is Upcoming-only; AGTHX is never in that list.
 */
export function fundPickerMatches(
  funds: FundEstimateView[],
  remoteFunds: FundEstimateView[],
  query: string,
): FundEstimateView[] {
  const q = query.trim();
  if (!q) return [];
  const local = searchFunds(funds, { query: q });
  // Remote identity wins a miss against the Upcoming-only homepage book.
  // Never splitFundsByBucket / hasEstimate-gate autocomplete.
  return mergeFundLists(local, remoteFunds).slice(0, PICKER_MATCH_LIMIT);
}
