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

export function formatUsd(value: number, digits = 2): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
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
  | "estimatedDistributionPctNav"
  | "publishedAt"
  | "vsCategoryPctNav";

export type SortDirection = "asc" | "desc";

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
    default:
      return a[key] - b[key];
  }
}
