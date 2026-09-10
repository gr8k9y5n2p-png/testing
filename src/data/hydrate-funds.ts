import {
  hasDisclosedUpcomingAmount,
  normalizePublicationStage,
  toPaidEvent,
  UPCOMING_STAGES,
} from "./distribution-bucket.ts";
import type { PaidDistributionEvent } from "./distribution-bucket.ts";
import type { FundEstimate, FundEstimateView } from "./types.ts";

/**
 * `GET /funds.has_estimate` is unpaid Upcoming / manager prelim only.
 * Paid / final YE history must never be hidden just because that flag is false.
 */
export function hideUpcomingAmounts(
  fund: Pick<FundEstimate, "bucket" | "hasEstimate"> &
    Partial<
      Pick<
        FundEstimate,
        | "estimatedDistributionAmount"
        | "estimatedDistributionPctNav"
        | "estimatedOrdinaryIncome"
        | "estimatedCapitalGains"
      >
    >,
): boolean {
  if (fund.bucket === "paid") return false;
  if (fund.hasEstimate === false) return true;
  return !hasDisclosedUpcomingAmount(fund);
}

function isFinalOrPaidStage(stage: string | null | undefined): boolean {
  const key = normalizePublicationStage(stage);
  return key === "final" || key === "paid";
}

function isEstimateStage(stage: string | null | undefined): boolean {
  const key = normalizePublicationStage(stage);
  return Boolean(key && UPCOMING_STAGES.has(key));
}

function hasPaidEventSignal(
  event: Pick<
    PaidDistributionEvent,
    | "estimatedDistributionAmount"
    | "recordDate"
    | "exDate"
    | "payableDate"
    | "publicationStage"
  >,
): boolean {
  if (event.estimatedDistributionAmount) return true;
  if (event.recordDate || event.exDate || event.payableDate) return true;
  return isFinalOrPaidStage(event.publicationStage);
}

/** Event year for YE collapse: payable, else ex, else record, else as_of year. */
function paidEventYear(event: PaidDistributionEvent): number {
  const eventDate = event.payableDate ?? event.exDate ?? event.recordDate ?? event.asOfDate;
  const year = Number((eventDate ?? "").slice(0, 4));
  return year || event.distributionYear;
}

/**
 * Same-year Paid history: keep `final` / `paid`. Drop prelim/updated rows
 * once a final exists for that year. Past-dated estimates stay when no final.
 */
export function preferFinalPaidEvents(
  events: PaidDistributionEvent[],
): PaidDistributionEvent[] {
  const yearsWithFinal = new Set(
    events
      .filter((event) => isFinalOrPaidStage(event.publicationStage))
      .map(paidEventYear),
  );
  return events.filter((event) => {
    if (!isEstimateStage(event.publicationStage)) return true;
    return !yearsWithFinal.has(paidEventYear(event));
  });
}

/** Paid / final rows from `/distributions`. Never illustration / tax-on-holding $. */
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
    | "publishedPctOfNav"
    | "navOnDistributionDay"
    | "navOnDistributionDayAsOf"
    | "navOnDistributionDaySource"
    | "distributionYear"
    | "paidHistory"
  >,
): PaidDistributionEvent[] {
  const extras = fund.paidHistory ?? [];
  if (fund.bucket !== "paid") return preferFinalPaidEvents(extras);
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
    publishedPctOfNav: fund.publishedPctOfNav,
    navOnDistributionDay: fund.navOnDistributionDay,
    navOnDistributionDayAsOf: fund.navOnDistributionDayAsOf,
    navOnDistributionDaySource: fund.navOnDistributionDaySource,
    distributionYear: fund.distributionYear,
  });
  if (!hasPaidEventSignal(own)) return preferFinalPaidEvents(extras);
  const seen = new Set(
    extras.map(
      (event) =>
        `${event.asOfDate}|${event.exDate ?? ""}|${event.payableDate ?? ""}|${event.estimatedDistributionAmount}`,
    ),
  );
  const ownKey = `${own.asOfDate}|${own.exDate ?? ""}|${own.payableDate ?? ""}|${own.estimatedDistributionAmount}`;
  return preferFinalPaidEvents(seen.has(ownKey) ? extras : [own, ...extras]);
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

function catalogBucket(): FundEstimate["bucket"] {
  // GET /funds identity is never Upcoming. A true unpaid future announcement
  // has to come from /distributions — do not invent $0 UPDATED ESTIMATE rows.
  return "paid";
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
      bucket: catalogBucket(),
      hasEstimate: fund.hasEstimate === true,
    };
  }

  // Every fund: catalog `has_estimate: false` means unpaid Upcoming = none.
  // Do not let paid/final YE rows, stale announced-only dates, or $0
  // placeholders flip any ticker into Upcoming.
  const hasUpcoming =
    fromDists.bucket === "upcoming" &&
    fund.hasEstimate !== false &&
    hasDisclosedUpcomingAmount(fromDists);
  return {
    ...fund,
    cusip: fund.cusip || fromDists.cusip,
    shareClass: fund.shareClass || fromDists.shareClass,
    // Weekly NAV is GET /funds. Do not let a 0 from /distributions overwrite it.
    nav: fund.nav > 0 ? fund.nav : fromDists.nav,
    navAsOf: fund.navAsOf ?? fromDists.navAsOf ?? null,
    navSource: fund.navSource ?? fromDists.navSource ?? null,
    navOnDistributionDay:
      fromDists.navOnDistributionDay ?? fund.navOnDistributionDay ?? null,
    navOnDistributionDayAsOf:
      fromDists.navOnDistributionDayAsOf ?? fund.navOnDistributionDayAsOf ?? null,
    navOnDistributionDaySource:
      fromDists.navOnDistributionDaySource ??
      fund.navOnDistributionDaySource ??
      null,
    publishedPctOfNav: fromDists.publishedPctOfNav ?? fund.publishedPctOfNav ?? null,
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
    bucket: hasUpcoming ? "upcoming" : "paid",
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
  // Weekly / dist-day NAV from GET /funds + /distributions. A distributions-only
  // duplicate must not win a tie and drop the live print.
  if (fund.nav > 0) score += 2;
  if (fund.navAsOf) score += 1;
  if (fund.navOnDistributionDay != null && fund.navOnDistributionDay > 0) score += 1;
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
