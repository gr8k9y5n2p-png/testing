import { SAMPLE_FUNDS } from "@/data/seed";
import { positiveNav, type NavLookup } from "@/lib/illustrate/compare-request";

/** Search/seed NAV by ticker. Used when illustrate/compare callers omit nav_per_share. */
export const seedNavLookup: NavLookup = (ticker) => {
  const fund = SAMPLE_FUNDS.find(
    (row) => row.ticker.toUpperCase() === ticker.toUpperCase(),
  );
  return positiveNav(fund?.nav);
};
