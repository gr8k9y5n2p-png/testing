import { toPaidEvent } from "./distribution-bucket.ts";
import type { PaidDistributionEvent } from "./distribution-bucket.ts";
import type { FundEstimate, FundEstimateView } from "./types.ts";

/**
 * `GET /funds.has_estimate` is unpaid Upcoming / manager prelim only.
 * Paid / final YE history must never be hidden just because that flag is false.
 */
export function hideUpcomingAmounts(
  fund: Pick<FundEstimate, "bucket" | "hasEstimate">,
): boolean {
  return fund.bucket !== "paid" && fund.hasEstimate === false;
}

/** Paid / final rows plus extras. Upcoming-only funds return paidHistory as-is. */
export function paidEventsForFund(
  fund: Pick<
    FundEstimate,
    | "bucket"
    | "asOfDate"
    | "recordDate"
    | "exDate"
    | "payableDate"
    | "publicationStage"
    | "estimatedDistributionAmount"
    | "estimatedOrdinaryIncome"
    | "estimatedCapitalGains"
    | "estimatedDistributionPctNav"
    | "distributionYear"
    | "paidHistory"
  >,
): PaidDistributionEvent[] {
  const extras = fund.paidHistory ?? [];
  if (fund.bucket !== "paid") return extras;
  const own = toPaidEvent({
    asOfDate: fund.asOfDate,
    recordDate: fund.recordDate,
    exDate: fund.exDate,
    payableDate: fund.payableDate,
    publicationStage: fund.publicationStage,
    estimatedDistributionAmount: fund.estimatedDistributionAmount,
    estimatedOrdinaryIncome: fund.estimatedOrdinaryIncome,
    estimatedCapitalGains: fund.estimatedCapitalGains,
    estimatedDistributionPctNav: fund.estimatedDistributionPctNav,
    distributionYear: fund.distributionYear,
  });
  const seen = new Set(
    extras.map(
      (event) =>
        `${event.asOfDate}|${event.exDate ?? ""}|${event.payableDate ?? ""}|${event.estimatedDistributionAmount}`,
    ),
  );
  const ownKey = `${own.asOfDate}|${own.exDate ?? ""}|${own.payableDate ?? ""}|${own.estimatedDistributionAmount}`;
  return seen.has(ownKey) ? extras : [own, ...extras];
}

function indexKey(fund: Pick<FundEstimate, "ticker" | "id">): string[] {
  const keys: string[] = [];
  const ticker = fund.ticker.trim().toUpperCase();
  if (ticker && ticker !== "—") keys.push(`ticker:${ticker}`);
  if (fund.id) keys.push(`id:${fund.id}`);
  const ident = fund.id.startsWith("fund:")
    ? fund.id.slice("fund:".length)
    : fund.id.startsWith("api:")
      ? fund.id.slice("api:".length)
      : "";
  if (ident) keys.push(`ident:${ident.toUpperCase()}`);
  return keys;
}

export function indexFundsByIdentity<T extends Pick<FundEstimate, "ticker" | "id">>(
  funds: T[],
): Map<string, T> {
  const map = new Map<string, T>();
  for (const fund of funds) {
    for (const key of indexKey(fund)) {
      if (!map.has(key)) map.set(key, fund);
    }
  }
  return map;
}

export function findHydratedFund<T extends Pick<FundEstimate, "ticker" | "id">>(
  fund: Pick<FundEstimate, "ticker" | "id">,
  index: Map<string, T>,
): T | undefined {
  for (const key of indexKey(fund)) {
    const match = index.get(key);
    if (match) return match;
  }
  return undefined;
}

function catalogBucket(fund: Pick<FundEstimate, "hasEstimate" | "bucket">): FundEstimate["bucket"] {
  if (fund.hasEstimate === false) return "paid";
  return fund.bucket === "paid" ? "paid" : "upcoming";
}

/**
 * Overlay `GET /distributions` aggregation onto a unique `GET /funds` row.
 * Upcoming amounts stay unpaid-only. Paid / final YE never becomes Upcoming.
 * A miss does **not** invent Upcoming from `latest_as_of`.
 */
export function mergeFundWithDistributions(
  fund: FundEstimateView,
  fromDists?: FundEstimate | FundEstimateView | null,
): FundEstimateView {
  if (!fromDists) {
    return {
      ...fund,
      paidHistory: [],
      bucket: catalogBucket(fund),
      hasEstimate: fund.hasEstimate === true,
    };
  }

  const hasUpcoming = fromDists.bucket === "upcoming";
  return {
    ...fund,
    cusip: fund.cusip || fromDists.cusip,
    shareClass: fund.shareClass || fromDists.shareClass,
    nav: fromDists.nav || fund.nav,
    estimatedDistributionAmount: fromDists.estimatedDistributionAmount,
    estimatedOrdinaryIncome: fromDists.estimatedOrdinaryIncome,
    estimatedCapitalGains: fromDists.estimatedCapitalGains,
    estimatedDistributionPctNav: fromDists.estimatedDistributionPctNav,
    publishedAt: fromDists.publishedAt || fund.publishedAt,
    asOfDate: fromDists.asOfDate || fund.asOfDate,
    recordDate: fromDists.recordDate,
    exDate: fromDists.exDate,
    payableDate: fromDists.payableDate,
    publicationStage: fromDists.publicationStage,
    bucket: fromDists.bucket,
    paidHistory: fromDists.paidHistory,
    distributionYear: fromDists.distributionYear,
    hasEstimate: hasUpcoming,
    categoryAveragePctNav:
      "categoryAveragePctNav" in fromDists
        ? fromDists.categoryAveragePctNav
        : fund.categoryAveragePctNav,
    vsCategoryPctNav:
      "vsCategoryPctNav" in fromDists
        ? fromDists.vsCategoryPctNav
        : fund.vsCategoryPctNav,
  };
}

function fundListKey(fund: Pick<FundEstimate, "ticker" | "id">): string {
  const ticker = fund.ticker.trim().toUpperCase();
  return ticker && ticker !== "—" ? `ticker:${ticker}` : fund.id;
}

function hydrationScore(fund: FundEstimateView): number {
  let score = 0;
  if ((fund.paidHistory?.length ?? 0) > 0) score += 3;
  if (fund.estimatedDistributionAmount) score += 3;
  if (fund.publicationStage) score += 1;
  if (fund.recordDate || fund.exDate || fund.payableDate) score += 1;
  if (fund.bucket === "paid" && fund.hasEstimate !== true) score += 1;
  return score;
}

export function mergeFundLists(
  primary: FundEstimateView[],
  extra: FundEstimateView[],
): FundEstimateView[] {
  const map = new Map<string, FundEstimateView>();
  const order: string[] = [];
  for (const fund of [...extra, ...primary]) {
    const key = fundListKey(fund);
    const prev = map.get(key);
    if (!prev) {
      map.set(key, fund);
      order.push(key);
      continue;
    }
    if (hydrationScore(fund) > hydrationScore(prev)) {
      map.set(key, fund);
    }
  }
  return order.map((key) => map.get(key)!);
}
