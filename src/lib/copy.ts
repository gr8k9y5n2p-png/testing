/**
 * Locked GTM copy for Aftertax. Do not paraphrase in the UI.
 * Disclaimer and legal chrome are user-facing. Do not paraphrase.
 */
export { HOST, PRODUCTION_HOST, STAGING_HOST } from "@/lib/hosts";
export { CONTACT_EMAIL } from "./legal-copy";

import {
  CONTACT_EMAIL,
  LEGAL_BETA,
  LEGAL_COMPACT,
  LEGAL_DISCLAIMER,
} from "./legal-copy";

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
  disclaimer: LEGAL_DISCLAIMER,
  compactDisclaimer: LEGAL_COMPACT,
  betaBanner: LEGAL_BETA,
  contactEmail: CONTACT_EMAIL,
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

/** Locked Search Upcoming / Announced module chrome (Modules). */
export const SEARCH_UPCOMING_HEADING = "Upcoming / Announced";
export const SEARCH_UPCOMING_DETAIL =
  "Announced distributions that have not gone ex yet. After ex-date (America/Chicago) they move to Paid History below — do not wait for payable.";
export const SEARCH_UPCOMING_KICKER = "unpaid announced · not paid history";
export const SEARCH_PAID_HISTORY_HEADING = "Paid History";
export const SEARCH_PAID_HISTORY_DETAIL =
  "Paid and final distributions from GET /distributions for the selected calendar year. Prior-year rows drop off when the year ends. Never invented from Upcoming.";
export const SEARCH_PAID_HISTORY_KICKER = "past · not upcoming";
export const ILLUSTRATION_PAID_HISTORY_DETAIL =
  "Final and paid distributions from GET /distributions for the last 5 completed calendar years plus the current year. 2026 cells show Awaiting when no unpaid announced estimate has arrived — never invented from history or Upcoming.";
export const ILLUSTRATION_PAID_HISTORY_KICKER = "5-year lookback · not upcoming";
export const AWAITING_ESTIMATE = "Awaiting Estimate";
export const ADD_TO_UNIVERSE = "Add to universe";
export const DATA_API_UNAVAILABLE =
  "Data API is unavailable. Try again — this is not an empty catalog.";

/** Lists tab — ticker paste list + unpaid announced estimates. */
export const LISTS_HEADING = "Lists";
export const LISTS_DETAIL =
  "Paste or type tickers. Upcoming / announced estimates only — unpaid, never invented from paid history.";
export const LISTS_EMPTY =
  "Paste or type tickers to build a list. Separate with commas, spaces, or new lines.";
export const LISTS_INPUT_PLACEHOLDER = "FBGRX, AGTHX, ABALX";
export const LISTS_ADD = "Add";
export const LISTS_NOT_FOUND = "Not found";
export const LISTS_NAV_COLUMN = "NAV";
export const LISTS_DIST_COLUMN = "Estimated $ Distribution/share";
export const LISTS_PCT_COLUMN = "Distribution % of NAV";
export const LISTS_ANNOUNCED_COLUMN = "Announced Date";
export const LISTS_RECORD_COLUMN = "Record Date";
export const LISTS_EX_COLUMN = "Ex-Date";

export { TICKER_REQUEST } from "@/lib/data-api/request-ticker";

export const FREE_SEARCH_LIMIT = 3;

export function freeSearchLabel(remaining: number): string {
  if (remaining <= 0) return "0 free searches left";
  if (remaining === 1) return "1 of 3 free searches left";
  if (remaining === 2) return "2 of 3 free searches left";
  return `${remaining} of 3 free searches left`;
}
