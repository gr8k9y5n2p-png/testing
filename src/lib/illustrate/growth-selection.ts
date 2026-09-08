import { MAX_GROWTH_FUNDS } from "../charts/series-colors.ts";
import type { CompareResponse } from "./compare-types.ts";

export type GrowthFundInput = {
  ticker: string;
  label?: string;
  fundIdentifier?: string;
  fundFamily?: string;
  /** Real product name. Never the ticker — Data ANDs fund_name. */
  fundName?: string;
  /** Search / fund metadata NAV. Sent on YoY compare when > 0. */
  navPerShare?: number | null;
};

export function normalizeGrowthTicker(ticker: string): string {
  return ticker.trim().toUpperCase();
}

export function growthFundKey(fund: GrowthFundInput): GrowthFundInput {
  return {
    ticker: normalizeGrowthTicker(fund.ticker),
    label: fund.label,
    fundIdentifier: fund.fundIdentifier,
    fundFamily: fund.fundFamily,
    fundName: fund.fundName,
    navPerShare: fund.navPerShare,
  };
}

/** Drop a user-added fund. Empty is valid (homepage starts with no series). */
export function removeGrowthFund(
  selected: GrowthFundInput[],
  ticker: string,
): GrowthFundInput[] {
  const key = normalizeGrowthTicker(ticker);
  return selected.filter((fund) => growthFundKey(fund).ticker !== key);
}

export function mergeSeedFunds(
  current: GrowthFundInput[],
  seeds: GrowthFundInput[],
): GrowthFundInput[] {
  const seeded = seeds.map(growthFundKey);
  const seen = new Set(seeded.map((fund) => fund.ticker));
  const rest = current.filter((fund) => !seen.has(growthFundKey(fund).ticker));
  return [...seeded, ...rest].slice(0, MAX_GROWTH_FUNDS);
}

export function isRemovableGrowthSeries(id: string, dashed?: boolean): boolean {
  return !dashed && !id.startsWith("bench-");
}

export type GrowthUpcomingRow = {
  ticker: string;
  tax: CompareResponse | null;
  taxSide: "left" | "right" | "auto";
};

/**
 * First remaining fund with an upcoming payload. Removed tickers are skipped
 * so the header/tax-drag badges drop that fund immediately.
 */
export function upcomingRowForSelectedFunds(
  rows: GrowthUpcomingRow[] | null | undefined,
  selected: GrowthFundInput[],
): GrowthUpcomingRow | null {
  if (!rows?.length || selected.length === 0) return null;
  const keep = new Set(selected.map((fund) => growthFundKey(fund).ticker));
  return (
    rows.find(
      (item) =>
        keep.has(normalizeGrowthTicker(item.ticker)) &&
        item.tax?.summary.upcoming_taxable_distribution,
    ) ?? null
  );
}

export function upcomingPreferSide(
  taxSide: GrowthUpcomingRow["taxSide"],
): "left" | "right" | "either" {
  return taxSide === "left" || taxSide === "right" ? taxSide : "either";
}
