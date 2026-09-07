/** Ledger Light series colors — not neon. Shared by growth lines and tax bars. */

export const FUND_SERIES_COLORS = [
  "#0f7a4b",
  "#6b5348",
  "#3f5c4f",
  "#8a6a4f",
] as const;

export const BENCHMARK_COLOR = "#8b958c";

export function fundSeriesColor(index: number): string {
  return FUND_SERIES_COLORS[index % FUND_SERIES_COLORS.length];
}
