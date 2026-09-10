import type { FundEstimateView } from "@/data/types";

const dateFormatter = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
  year: "numeric",
  timeZone: "UTC",
});

const compactDateFormatter = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
  timeZone: "UTC",
});

export function formatDate(isoDate: string): string {
  return dateFormatter.format(new Date(`${isoDate}T00:00:00Z`));
}

export function formatCompactDate(isoDate: string): string {
  return compactDateFormatter.format(new Date(`${isoDate}T00:00:00Z`));
}

/** Advisor-facing date. Missing or invalid values stay "—" — never invent a day. */
export function formatOptionalDate(
  iso: string | null | undefined,
  compact = false,
): string {
  if (!iso) return "—";
  const parsed = new Date(`${iso}T00:00:00Z`);
  if (Number.isNaN(parsed.getTime())) return "—";
  return compact ? formatCompactDate(iso) : formatDate(iso);
}

export function formatUsd(value: number, digits = 2): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}

export function formatUsdRange(
  point: number | null | undefined,
  min?: number | null,
  max?: number | null,
  digits = 0,
): string {
  if (min != null && max != null && min !== max) {
    return `${formatUsd(min, digits)}–${formatUsd(max, digits)}`;
  }
  if (point == null) return "—";
  return formatUsd(point, digits);
}

export function formatRatePct(decimal: number): string {
  return `${(decimal * 100).toFixed(1)}%`;
}

export function formatPct(value: number, digits = 2): string {
  return `${value.toFixed(digits)}%`;
}

export function formatSignedPp(value: number, digits = 2): string {
  const abs = Math.abs(value).toFixed(digits);
  if (value > 0.004) return `+${abs} pp`;
  if (value < -0.004) return `−${abs} pp`;
  return `${(0).toFixed(digits)} pp`;
}

/** vs category: above = more tax (style red), below = less tax (style green). */
export function deltaTone(value: number): "above" | "below" | "neutral" {
  if (value >= 1) return "above";
  if (value <= -1) return "below";
  return "neutral";
}

export function sortFunds(
  funds: FundEstimateView[],
  key: SortKey,
  direction: SortDirection,
): FundEstimateView[] {
  const sorted = [...funds].sort((a, b) => compareFunds(a, b, key));
  return direction === "desc" ? sorted.reverse() : sorted;
}

export type SortKey =
  | "fundName"
  | "family"
  | "category"
  | "estimatedDistributionAmount"
  | "estimatedDistributionPctNav"
  | "publishedAt"
  | "asOfDate"
  | "recordDate"
  | "exDate"
  | "vsCategoryPctNav";

export type SortDirection = "asc" | "desc";

/** ISO calendar dates only. Invalid / missing values sort after real dates. */
export function compareOptionalIsoDates(
  a: string | null | undefined,
  b: string | null | undefined,
): number {
  const left = sortableIsoDate(a);
  const right = sortableIsoDate(b);
  if (!left && !right) return 0;
  if (!left) return 1;
  if (!right) return -1;
  return left.localeCompare(right);
}

function sortableIsoDate(value: string | null | undefined): string | null {
  if (!value) return null;
  const parsed = new Date(`${value}T00:00:00Z`);
  return Number.isNaN(parsed.getTime()) ? null : value;
}

/**
 * Aftertax % of NAV for Search sort: Dist $/share ÷ the correct NAV series.
 * Upcoming → weekly NAV. Paid/final → nav on distribution day.
 * Never manager-published percent_of_nav / estimatedDistributionPctNav.
 * Mirrors `pctOfNavForFund` without importing nav-math (cycle).
 */
function aftertaxPctOfNavForSort(fund: FundEstimateView): number | null {
  const perShare = Number(fund.estimatedDistributionAmount);
  if (!Number.isFinite(perShare)) return null;
  const stage = (fund.publicationStage ?? "").trim().toLowerCase();
  const day = fund.exDate ?? fund.payableDate ?? "";
  const paid =
    stage === "final" ||
    stage === "paid" ||
    (day.length >= 10 && day <= new Date().toISOString().slice(0, 10));
  const nav = paid ? fund.navOnDistributionDay : fund.nav;
  if (nav == null || !(Number(nav) > 0)) return null;
  return (perShare / Number(nav)) * 100;
}

function compareOptionalPct(
  left: number | null,
  right: number | null,
): number {
  if (left == null && right == null) return 0;
  if (left == null) return 1;
  if (right == null) return -1;
  return left - right;
}

/** Dist $/share. Non-finite / missing amounts sort after real dollars. */
function distPerShareForSort(fund: FundEstimateView): number | null {
  const amount = Number(fund.estimatedDistributionAmount);
  return Number.isFinite(amount) ? amount : null;
}

function compareFunds(
  a: FundEstimateView,
  b: FundEstimateView,
  key: SortKey,
): number {
  switch (key) {
    case "fundName":
    case "family":
    case "category":
    case "publishedAt":
      return a[key].localeCompare(b[key]);
    case "asOfDate":
      return compareOptionalIsoDates(a.asOfDate, b.asOfDate);
    case "recordDate":
      return compareOptionalIsoDates(a.recordDate, b.recordDate);
    case "exDate":
      return compareOptionalIsoDates(a.exDate, b.exDate);
    case "estimatedDistributionAmount":
      return compareOptionalPct(distPerShareForSort(a), distPerShareForSort(b));
    case "estimatedDistributionPctNav":
      return compareOptionalPct(
        aftertaxPctOfNavForSort(a),
        aftertaxPctOfNavForSort(b),
      );
    default:
      return a[key] - b[key];
  }
}
