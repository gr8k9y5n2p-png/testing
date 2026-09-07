/** Ledger Light series colors — not neon. Shared by growth lines and tax bars. */

export const FUND_SERIES_COLORS = [
  "#0f7a4b",
  "#6b5348",
  "#3f5c4f",
  "#8a6a4f",
  "#4a5d6b",
  "#7a4a4a",
] as const;

export const BENCHMARK_COLOR = "#8b958c";

export const MAX_GROWTH_FUNDS = 6;

export function fundSeriesColor(index: number): string {
  return FUND_SERIES_COLORS[index % FUND_SERIES_COLORS.length];
}
