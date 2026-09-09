/**
 * Single-book vs compare helpers. Import-free so Node tests can load them.
 */

export function portfolioBookFilled(allocation: {
  holdings: readonly unknown[];
}): boolean {
  return allocation.holdings.length > 0;
}

/** Compare deltas only when both books have holdings. One book is not a compare. */
export function canComparePortfolioBooks(result: {
  current: { holdings: readonly unknown[] };
  proposed: { holdings: readonly unknown[] };
}): boolean {
  return portfolioBookFilled(result.current) && portfolioBookFilled(result.proposed);
}
