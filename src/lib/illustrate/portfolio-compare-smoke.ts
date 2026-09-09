/**
 * PortfolioCompare initial books. Friends beta starts empty — advisors
 * add tickers via + Add holding. Keep this module import-free so Node
 * tests can load it without `@/` aliases.
 */

/** Current book — empty until the user adds a holding. */
export const SMOKE_CURRENT_TICKERS = [] as const;

/** Proposed book — empty until the user adds a holding. */
export const SMOKE_PROPOSED_TICKERS = [] as const;

/** Default weight when a caller builds a holding via the catalog helpers. */
export const SMOKE_WEIGHT_PCT = 25;
