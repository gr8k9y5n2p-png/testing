import { parsePositiveNav } from "../lib/illustrate/nav-math.ts";
import { isoDate } from "./distribution-bucket.ts";
import type { FundEstimateView } from "./types.ts";

/** GET /funds item. Unique fund, not a raw distribution row. */
export type FundsApiItem = {
  ticker?: string | null;
  fund_name?: string | null;
  fund_family?: string | null;
  fund_identifier?: string | null;
  latest_as_of?: string | null;
  has_estimate?: boolean | null;
  fundName?: string | null;
  family?: string | null;
  category?: string | null;
  cusip?: string | null;
  share_class?: string | null;
  /** Weekly NAV from Data #74 / GET /funds. Soft-null when absent. */
  nav_per_share?: number | string | null;
  nav?: number | string | null;
  nav_as_of?: string | null;
  nav_source?: string | null;
};

export function mapFundsApiItem(row: FundsApiItem): FundEstimateView {
  const ticker = (row.ticker ?? "").trim().toUpperCase();
  const identifier = (row.fund_identifier ?? ticker ?? "").trim();
  const asOf = (row.latest_as_of ?? "").slice(0, 10);
  const year = Number(asOf.slice(0, 4)) || new Date().getUTCFullYear();
  // Unpaid Upcoming only. `latest_as_of` is the newest distribution as_of
  // (often a paid YE date) — never an Upcoming announce by itself.
  const hasEstimate = Boolean(row.has_estimate);
  return {
    id: `fund:${identifier || ticker || row.fund_name || "unknown"}`,
    fundName: (row.fund_name ?? row.fundName ?? "—").trim() || "—",
    ticker: ticker || "—",
    cusip: row.cusip ?? "",
    family: (row.fund_family ?? row.family ?? "—").trim() || "—",
    category: (row.category ?? "—").trim() || "—",
    shareClass: row.share_class ?? "",
    nav: parsePositiveNav(row.nav_per_share) ?? parsePositiveNav(row.nav) ?? 0,
    navAsOf: isoDate(row.nav_as_of),
    navSource: row.nav_source ?? null,
    estimatedDistributionAmount: 0,
    estimatedOrdinaryIncome: 0,
    estimatedCapitalGains: 0,
    estimatedDistributionPctNav: 0,
    publishedAt: asOf || new Date().toISOString().slice(0, 10),
    asOfDate: asOf || new Date().toISOString().slice(0, 10),
    recordDate: null,
    exDate: null,
    payableDate: null,
    publicationStage: hasEstimate ? "updated_estimate" : null,
    bucket: hasEstimate ? "upcoming" : "paid",
    paidHistory: [],
    distributionYear: year,
    categoryAveragePctNav: 0,
    vsCategoryPctNav: 0,
    hasEstimate,
  };
}
