import type { CompareUpcomingDistribution } from "./compare-types.ts";

export const DEFAULT_NORMALIZED_HOLDING_DOLLARS = 10_000;

/**
 * Pair summaries stay normalized to `normalized_holding_dollars` ($10k).
 * Compare rescales $ deltas to the shared dollars-invested holding.
 */
export function scaleNormalizedHoldingDollars(
  dollars: number,
  holdingDollars: number,
  normalizedHoldingDollars = DEFAULT_NORMALIZED_HOLDING_DOLLARS,
): number {
  if (!(normalizedHoldingDollars > 0)) return dollars;
  return dollars * (holdingDollars / normalizedHoldingDollars);
}

export function scaleUpcomingToHolding(
  upcoming: CompareUpcomingDistribution | null | undefined,
  holdingDollars: number,
  normalizedHoldingDollars = DEFAULT_NORMALIZED_HOLDING_DOLLARS,
): CompareUpcomingDistribution | null | undefined {
  if (!upcoming) return upcoming;
  const scale = (value: number | null | undefined) =>
    value == null
      ? value
      : scaleNormalizedHoldingDollars(value, holdingDollars, normalizedHoldingDollars);
  return {
    ...upcoming,
    left_dollars: scale(upcoming.left_dollars) ?? null,
    right_dollars: scale(upcoming.right_dollars) ?? null,
    delta_dollars: scale(upcoming.delta_dollars) ?? null,
  };
}
