export type DistributionBucket = "upcoming" | "paid";

export type PaidDistributionEvent = {
  asOfDate: string;
  recordDate: string | null;
  exDate: string | null;
  payableDate: string | null;
  publicationStage: string | null;
  estimatedDistributionAmount: number;
  estimatedOrdinaryIncome: number;
  estimatedCapitalGains: number;
  estimatedDistributionPctNav: number;
  distributionYear: number;
  /** Issuer-published percent_of_nav characters only. Null when none. */
  publishedPctOfNav?: number | null;
  /** NAV on ex/payable. Historical % of NAV only — never weekly NAV. */
  navOnDistributionDay?: number | null;
  navOnDistributionDayAsOf?: string | null;
  navOnDistributionDaySource?: string | null;
};

export const UPCOMING_STAGES = new Set(["preliminary_estimate", "updated_estimate"]);
export const PAID_STAGES = new Set(["paid"]);

export type DistributionDateFields = {
  asOfDate?: string | null;
  recordDate?: string | null;
  exDate?: string | null;
  payableDate?: string | null;
  publicationStage?: string | null;
};

export function utcTodayIso(now = new Date()): string {
  return now.toISOString().slice(0, 10);
}

/** Search Upcoming / Paid History cutover calendar (Eric: America/Chicago). */
export function chicagoTodayIso(now = new Date()): string {
  return now.toLocaleDateString("en-CA", { timeZone: "America/Chicago" });
}

export function isoDate(value: unknown): string | null {
  if (value == null || value === "") return null;
  const raw = String(value).trim();
  if (/^\d{4}-\d{2}-\d{2}/.test(raw)) return raw.slice(0, 10);
  return null;
}

/**
 * Best available event date: payable, else ex, else record. Never invents a day.
 * `as_of` is announcement, not an event date.
 */
export function eventDateOf(
  dates: Pick<DistributionDateFields, "payableDate" | "exDate" | "recordDate">,
): string | null {
  return isoDate(dates.payableDate) ?? isoDate(dates.exDate) ?? isoDate(dates.recordDate);
}

/**
 * Event date in the past. `as_of` is announcement for estimates and does not
 * make a preliminary/updated row paid. Past `final` rows fall back to `as_of`
 * when payable/ex/record are missing (year-end 2025 finals with only as_of).
 * Unpaid prelims cut over on **ex_date** (not payable): once ex < today the
 * row is Paid History even if payable is still ahead.
 */
export function isPastDistribution(
  dates: DistributionDateFields,
  today = chicagoTodayIso(),
): boolean {
  const stage = normalizePublicationStage(dates.publicationStage);
  if (isUnpaidPrelimStage(stage)) {
    const ex = isoDate(dates.exDate);
    if (ex != null) return ex < today;
    const cutoff = eventDateOf(dates);
    return cutoff != null && cutoff < today;
  }
  const cutoff =
    eventDateOf(dates) ?? (stage === "final" ? isoDate(dates.asOfDate) : null);
  return cutoff != null && cutoff < today;
}

/**
 * Announced (`as_of`) already passed and no remaining unpaid event date.
 * Sell-before-record still uses record/ex/payable when those exist — a past
 * announcement of a future YE event stays unpaid. Catalog `latest_as_of`
 * alone (Oct 2023 / Oct 2025 placeholders) is not Upcoming.
 */
export function isStaleAnnouncedOnly(
  dates: DistributionDateFields,
  today = chicagoTodayIso(),
): boolean {
  if (eventDateOf(dates)) return false;
  const announced = isoDate(dates.asOfDate);
  const stage = normalizePublicationStage(dates.publicationStage);
  if (stage === "final" || (stage && PAID_STAGES.has(stage))) return false;
  return announced != null && announced < today && isUnpaidPrelimStage(stage);
}

export function normalizePublicationStage(stage: string | null | undefined): string | null {
  if (stage == null || stage === "") return null;
  const key = stage.trim().toLowerCase().replace(/[\s-]+/g, "_");
  if (key === "preliminary" || key === "announced") return "preliminary_estimate";
  if (key === "updated") return "updated_estimate";
  return key;
}

function isUnpaidPrelimStage(stage: string | null): boolean {
  return Boolean(stage && UPCOMING_STAGES.has(stage));
}

/**
 * Shared Upcoming / Fund Manager Estimated Distributions classifier for
 * every fund (not ticker-specific). Upcoming = unpaid preliminary_estimate
 * or updated_estimate only, and only when payable/ex/record are not already
 * past. `final` and `paid` are Paid history — never Upcoming, even with
 * future event dates or holding-scaled illustration dollars.
 * A future event date without a prelim/estimate stage does not invent Upcoming.
 * Identity / `latest_as_of`-only rows stay paid history. `$0` catalog
 * leftovers are dropped by `isUpcomingFund`, not by treating as_of as paid.
 */
export function distributionBucket(
  dates: DistributionDateFields,
  today = chicagoTodayIso(),
): DistributionBucket {
  const stage = normalizePublicationStage(dates.publicationStage);
  if (
    stage === "final" ||
    (stage && PAID_STAGES.has(stage)) ||
    isPastDistribution(dates, today)
  ) {
    return "paid";
  }
  if (isUnpaidPrelimStage(stage)) return "upcoming";
  return "paid";
}

type UpcomingAmountFields = {
  estimatedDistributionAmount?: number;
  estimatedDistributionPctNav?: number;
  estimatedOrdinaryIncome?: number;
  estimatedCapitalGains?: number;
};

function upcomingAmountFields(fund: UpcomingAmountFields): Array<number | null | undefined> {
  return [
    fund.estimatedDistributionAmount,
    fund.estimatedDistributionPctNav,
    fund.estimatedOrdinaryIncome,
    fund.estimatedCapitalGains,
  ];
}

export function hasPositiveUpcomingAmount(fund: UpcomingAmountFields): boolean {
  return upcomingAmountFields(fund).some((value) => value != null && value > 0);
}

/**
 * Manager-published Upcoming characters, including announced **$0**.
 * Soft — / undisclosed only when every amount field is missing.
 * Partial classifier rows with no amount fields still follow bucket + flag.
 */
export function hasDisclosedUpcomingAmount(fund: UpcomingAmountFields): boolean {
  const fields = upcomingAmountFields(fund);
  if (fields.every((value) => value == null)) return true;
  return fields.some((value) => value != null);
}

/**
 * Universe Upcoming gate for Search Sample Estimates, Highlights, and badges.
 * A fund appears with a true unpaid future announced distribution:
 * unpaid prelim/updated, ex_date still today-or-later (Chicago). Announced
 * **$0** still qualifies when dated. `$0` + stale as_of-only leftovers stay
 * out. `has_estimate: false` is never Upcoming. Never invent from paid/final
 * history, catalog identity, or illustration math.
 */
export function isUpcomingFund<
  T extends {
    bucket: DistributionBucket;
    hasEstimate?: boolean;
    asOfDate?: string | null;
    recordDate?: string | null;
    exDate?: string | null;
    payableDate?: string | null;
    publicationStage?: string | null;
  } & UpcomingAmountFields,
>(fund: T, today = chicagoTodayIso()): boolean {
  if (fund.hasEstimate === false) return false;
  if (fund.bucket !== "upcoming") return false;
  if (!hasDisclosedUpcomingAmount(fund)) return false;
  const dates = {
    asOfDate: fund.asOfDate,
    recordDate: fund.recordDate,
    exDate: fund.exDate,
    payableDate: fund.payableDate,
    publicationStage: fund.publicationStage,
  };
  if (
    isStaleAnnouncedOnly(dates, today) &&
    !hasPositiveUpcomingAmount(fund)
  ) {
    return false;
  }
  if (
    fund.asOfDate != null ||
    fund.recordDate != null ||
    fund.exDate != null ||
    fund.payableDate != null ||
    fund.publicationStage != null
  ) {
    return distributionBucket(dates, today) === "upcoming";
  }
  return true;
}

export function publicationStageLabel(stage: string | null | undefined): string {
  const key = normalizePublicationStage(stage);
  switch (key) {
    case "preliminary_estimate":
      return "Preliminary estimate";
    case "updated_estimate":
      return "Updated estimate";
    case "final":
      return "Final";
    case "paid":
      return "Paid";
    default:
      return key ? key.replace(/_/g, " ") : "";
  }
}

export function toPaidEvent(
  row: DistributionDateFields & {
    asOfDate: string;
    estimatedDistributionAmount: number;
    estimatedOrdinaryIncome: number;
    estimatedCapitalGains: number;
    estimatedDistributionPctNav: number;
    distributionYear: number;
    publishedPctOfNav?: number | null;
    navOnDistributionDay?: number | null;
    navOnDistributionDayAsOf?: string | null;
    navOnDistributionDaySource?: string | null;
  },
): PaidDistributionEvent {
  return {
    asOfDate: row.asOfDate,
    recordDate: row.recordDate ?? null,
    exDate: row.exDate ?? null,
    payableDate: row.payableDate ?? null,
    publicationStage: row.publicationStage ?? null,
    estimatedDistributionAmount: row.estimatedDistributionAmount,
    estimatedOrdinaryIncome: row.estimatedOrdinaryIncome,
    estimatedCapitalGains: row.estimatedCapitalGains,
    estimatedDistributionPctNav: row.estimatedDistributionPctNav,
    distributionYear: row.distributionYear,
    publishedPctOfNav: row.publishedPctOfNav ?? null,
    navOnDistributionDay: row.navOnDistributionDay ?? null,
    navOnDistributionDayAsOf: row.navOnDistributionDayAsOf ?? null,
    navOnDistributionDaySource: row.navOnDistributionDaySource ?? null,
  };
}

export function splitFundsByBucket<
  T extends { bucket: DistributionBucket; hasEstimate?: boolean },
>(funds: T[]): { upcoming: T[]; paid: T[] } {
  const upcoming: T[] = [];
  const paid: T[] = [];
  for (const fund of funds) {
    if (isUpcomingFund(fund)) upcoming.push(fund);
    else paid.push(fund);
  }
  return { upcoming, paid };
}
