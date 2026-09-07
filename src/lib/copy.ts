/**
 * Locked GTM draft copy for Aftertax. Iterate later; do not paraphrase in the UI.
 * Canonical host: getaftertax.com
 */
export const COPY = {
  hero: "See the taxable impact in dollars — before the meeting ends.",
  sub: "Live fund comparisons for wholesalers. Portfolio import for advisors.",
  trust: "Illustrative estimates only. Not tax, legal, or investment advice.",
  searchCta: "Search a fund",
  importCta: "Import a portfolio",
  paywallHeadline: "Keep going with Aftertax",
  paywallBody:
    "Unlimited fund searches plus portfolio aggregation — see dollar taxable impact across the full book.",
  paywallPrice: "$39 / user / month. Cancel anytime.",
  paywallCta: "Unlock Aftertax",
  continueFree: "Continue with free searches",
  disclaimer:
    "Tax impact figures are estimates for illustration and educational use only. They are not tax advice, do not reflect your or your client’s specific situation, and may omit state, local, AMT, wash-sale, holding-period, and other rules. Consult a qualified tax professional. Aftertax is not a broker-dealer or RIA.",
} as const;

/** Aftertax website owns Stripe Checkout Sessions against this price. */
export const STRIPE = {
  productId: "prod_VDXGeprN4QkxsM",
  priceId: "price_1UD6C0RqA7bY5N5qVleZso0d",
  accountId: "acct_1UD66TRqA7bY5N5q",
} as const;

export const HOST = "getaftertax.com";
export const FREE_SEARCH_LIMIT = 3;

export function freeSearchLabel(remaining: number): string {
  if (remaining <= 0) return "0 free searches left";
  if (remaining === 1) return "1 of 3 free searches left";
  if (remaining === 2) return "2 of 3 free searches left";
  return `${remaining} of 3 free searches left`;
}
