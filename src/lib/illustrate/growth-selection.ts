import { MAX_GROWTH_FUNDS } from "../charts/series-colors.ts";

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
