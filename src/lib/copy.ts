/**
 * Locked GTM copy for Aftertax. Do not paraphrase in the UI.
 * Disclaimer is QA-final unless Eric edits.
 */
export { HOST, PRODUCTION_HOST, STAGING_HOST } from "@/lib/hosts";

export const COPY = {
  hero: "See the taxable impact in dollars — before the meeting ends.",
  sub: "Live fund comparisons for wholesalers. Portfolio import for advisors.",
  trust: "Illustrative estimates only. Not tax, legal, or investment advice.",
  searchCta: "Search a fund",
  compareCta: "Fund Comparison",
  importCta: "Import a portfolio",
  paywallHeadline: "Keep going with Aftertax",
  paywallBody:
    "Unlimited fund searches plus portfolio aggregation — see dollar taxable impact across the full book.",
  paywallPrice: "$39 / user / month. Cancel anytime.",
  paywallCta: "Unlock Aftertax",
  continueFree: "Continue with free searches",
  disclaimer:
    "Illustrative estimates only. Not tax, legal, or investment advice. Figures may omit state, local, AMT, wash-sale, holding-period, and other rules. Consult a qualified tax professional. Aftertax is not a broker-dealer or RIA.",
} as const;

/** Aftertax website owns Stripe Checkout. Test mode later; do not block on live keys. */
export const STRIPE = {
  productId: "prod_VDXGeprN4QkxsM",
  priceId: "price_1UD6C0RqA7bY5N5qVleZso0d",
  accountId: "acct_1UD66TRqA7bY5N5q",
} as const;

/** Sample Estimates Upcoming empty state. Never present a miss as $0. */
export const UPCOMING_UNAVAILABLE_HEADLINE = "Not available / undisclosed";
export const UPCOMING_UNAVAILABLE_DETAIL =
  "No unpaid announced estimates from the Data API.";
export const PAID_HISTORY_EMPTY = "No paid history from the Data API.";

export const FREE_SEARCH_LIMIT = 3;

export function freeSearchLabel(remaining: number): string {
  if (remaining <= 0) return "0 free searches left";
  if (remaining === 1) return "1 of 3 free searches left";
  if (remaining === 2) return "2 of 3 free searches left";
  return `${remaining} of 3 free searches left`;
}
