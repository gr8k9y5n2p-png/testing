/**
 * Portfolio compare request validation. Import-free so Node tests can load it.
 * One filled book is enough — Current-only or Proposed-only.
 */
import type {
  PortfolioCompareRequest,
  PortfolioHoldingIn,
} from "./portfolio-compare-types.ts";

export function resolveHoldingDollars(
  holding: PortfolioHoldingIn,
  sideBook: number | null | undefined,
): number | null {
  if (holding.holding_dollars != null && holding.holding_dollars > 0) {
    return holding.holding_dollars;
  }
  if (holding.weight_pct == null || !(holding.weight_pct > 0)) return null;
  const book = sideBook ?? holding.book_dollars ?? null;
  if (book == null || !(book > 0)) return null;
  return (holding.weight_pct / 100) * book;
}

export function isPortfolioCompareRequestValid(body: PortfolioCompareRequest): string | null {
  if (!body.current || !body.proposed) {
    return "current and proposed sides are required";
  }

  const currentHoldings = body.current.holdings ?? [];
  const proposedHoldings = body.proposed.holdings ?? [];
  if (!currentHoldings.length && !proposedHoldings.length) {
    return "current.holdings or proposed.holdings is required";
  }

  for (const [sideName, side] of [
    ["current", { ...body.current, holdings: currentHoldings }],
    ["proposed", { ...body.proposed, holdings: proposedHoldings }],
  ] as const) {
    for (const [index, holding] of side.holdings.entries()) {
      const hasLookup = Boolean(
        holding.ticker ||
          holding.fund_identifier ||
          holding.fund_name ||
          holding.distribution_ids?.length,
      );
      if (!hasLookup) {
        return `${sideName}.holdings[${index}] needs ticker and/or fund_identifier`;
      }
      const dollars = resolveHoldingDollars(holding, side.book_dollars);
      if (dollars == null || !(dollars > 0)) {
        return `${sideName}.holdings[${index}] needs holding_dollars, or weight_pct with book_dollars`;
      }
    }
  }
  return null;
}
