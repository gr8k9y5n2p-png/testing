import { SAMPLE_FUNDS } from "@/data/seed";
import { positiveNav, type NavLookup } from "@/lib/illustrate/compare-request";

/**
 * Share-class aliases onto SAMPLE_FUNDS tickers. AMCAP (F-2) uses AMCPX NAV
 * when search metadata does not send its own price.
 */
const TICKER_NAV_ALIASES: Record<string, string> = {
  AMCAP: "AMCPX",
};

/**
 * Portfolio smoke tickers that are not in SAMPLE_FUNDS. Values are illustrative
 * seed NAVs (> 0) so `/illustrate/portfolio/compare` can price per_share
 * `paid_history` rows. Never store 0 here — Data 422s `gt=0`.
 */
export const PORTFOLIO_SEED_NAV: Record<string, number> = {
  DODIX: 12.8,
  DODGX: 273.16,
  CGHM: 25.18,
};

function seedNavForTicker(ticker: string): number | undefined {
  const fund = SAMPLE_FUNDS.find(
    (row) => row.ticker.toUpperCase() === ticker.toUpperCase(),
  );
  return positiveNav(fund?.nav) ?? positiveNav(PORTFOLIO_SEED_NAV[ticker]);
}

/** Search/seed NAV by ticker. Used when illustrate/compare callers omit nav_per_share. */
export const seedNavLookup: NavLookup = (ticker) => {
  const key = ticker.trim().toUpperCase();
  if (!key) return undefined;
  return (
    seedNavForTicker(key) ??
    seedNavForTicker(TICKER_NAV_ALIASES[key] ?? "")
  );
};
