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

export function isoDate(value: unknown): string | null {
  if (value == null || value === "") return null;
  const raw = String(value).trim();
  if (/^\d{4}-\d{2}-\d{2}/.test(raw)) return raw.slice(0, 10);
  return null;
}

/** Payment/ex-date in the past. `as_of` is announcement and does not make a row paid. */
export function isPastDistribution(
  dates: DistributionDateFields,
  today = utcTodayIso(),
): boolean {
  const cutoff = dates.payableDate ?? dates.exDate ?? null;
  return cutoff != null && cutoff < today;
}

export function normalizePublicationStage(stage: string | null | undefined): string | null {
  if (stage == null || stage === "") return null;
  const key = stage.trim().toLowerCase().replace(/[\s-]+/g, "_");
  if (key === "preliminary" || key === "announced") return "preliminary_estimate";
  if (key === "updated") return "updated_estimate";
  return key;
}

/**
 * Upcoming / announced: preliminary_estimate, updated_estimate, or final that
 * has not paid yet. Paid history: paid, or final/any stage whose ex/payable
 * date is already past. Past rows must not sit in upcoming.
 */
export function distributionBucket(
  dates: DistributionDateFields,
  today = utcTodayIso(),
): DistributionBucket {
  const stage = normalizePublicationStage(dates.publicationStage);
  const past = isPastDistribution(dates, today);

  if (stage === "paid" || past) return "paid";
  if (stage === "final") return "upcoming";
  if (stage && UPCOMING_STAGES.has(stage)) return "upcoming";
  return "upcoming";
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
  };
}

export function splitFundsByBucket<T extends { bucket: DistributionBucket }>(
  funds: T[],
): { upcoming: T[]; paid: T[] } {
  const upcoming: T[] = [];
  const paid: T[] = [];
  for (const fund of funds) {
    if (fund.bucket === "paid") paid.push(fund);
    else upcoming.push(fund);
  }
  return { upcoming, paid };
}
