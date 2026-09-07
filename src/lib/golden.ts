import { SAMPLE_FUNDS } from "@/data/seed";

/**
 * Golden-test priority: Capital Group live fixtures first.
 * More hero tickers will be added later — do not treat non-CG families as golden.
 */
export const GOLDEN_LIVE_FAMILY = "Capital Group";

/** Seed family label for Capital Group products. */
export const GOLDEN_SEED_FAMILY = "American Funds";

/** First hero fixtures for QA / illustrate against Data PR #2. */
export const GOLDEN_HERO_TICKERS = ["AMCPX", "AGTHX"] as const;

export const CAPITAL_GROUP_GOLDEN_TICKERS = SAMPLE_FUNDS.filter(
  (fund) => fund.family === GOLDEN_SEED_FAMILY,
).map((fund) => fund.ticker);
