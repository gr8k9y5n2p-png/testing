/**
 * Confirmed-ticker identity helpers. Import-free so node:test can load them.
 */

export type PortfolioIdentityHint = {
  ticker: string;
  fundName: string;
  family?: string;
  nav?: number | null;
};

/** Merge identity/NAV hints without dropping earlier confirmations. */
export function mergePortfolioFundOptions(
  current: readonly PortfolioIdentityHint[],
  incoming: readonly PortfolioIdentityHint[],
): PortfolioIdentityHint[] {
  const byTicker = new Map<string, PortfolioIdentityHint>();
  for (const fund of [...current, ...incoming]) {
    const ticker = fund.ticker.trim().toUpperCase();
    if (!ticker) continue;
    const prev = byTicker.get(ticker);
    byTicker.set(ticker, {
      ticker,
      fundName: fund.fundName || prev?.fundName || ticker,
      family: fund.family || prev?.family,
      nav: fund.nav ?? prev?.nav ?? null,
    });
  }
  return [...byTicker.values()];
}

function holdingHasIdentity(holding: {
  fundName?: string;
  nav?: number | null;
}): boolean {
  return Boolean(holding.fundName?.trim()) || (holding.nav != null && holding.nav > 0);
}

/** Confirmed holdings + seed catalog tickers for Upcoming / Export universe. */
export function universeTickersFromHoldings(
  holdings: ReadonlyArray<{
    ticker?: string | null;
    fundName?: string;
    nav?: number | null;
  }>,
  extra: Iterable<string> = [],
): Set<string> {
  const tickers = new Set<string>();
  for (const raw of extra) {
    const ticker = raw.trim().toUpperCase();
    if (ticker) tickers.add(ticker);
  }
  for (const holding of holdings) {
    const ticker = (holding.ticker ?? "").trim().toUpperCase();
    if (!ticker || !holdingHasIdentity(holding)) continue;
    tickers.add(ticker);
  }
  return tickers;
}
