/**
 * Locked GET /performance and POST /performance/growth contract from PR #2
 * (`cursor/fund-distribution-ingest-api-85ed`). Field names must not drift.
 */

export const DEFAULT_START_DOLLARS = 10_000;

export const PERFORMANCE_FIXTURE_TICKERS = [
  "AGTHX",
  "AMCPX",
  "FBGRX",
  "VFIAX",
] as const;

export const PERFORMANCE_BENCHMARKS = ["SPY", "AGG", "VXUS"] as const;

export type PerformanceAssetClass = "equity" | "fixed_income" | "international";
export type PerformanceMode = "fixture" | "live" | "auto";

export type PerformancePoint = {
  date: string;
  adj_close: number;
  monthly_return: number | null;
  growth_of_x: number;
};

export type PerformanceSeriesOut = {
  ticker: string;
  name: string;
  currency: string;
  price_unit: string;
  return_unit: string;
  growth_unit: string;
  points: PerformancePoint[];
};

export type PerformanceResponse = {
  fund_ticker: string;
  fund_identifier: string;
  fund_name: string;
  asset_class: PerformanceAssetClass;
  start_dollars: number;
  start_date: string;
  end_date: string;
  as_of: string;
  frequency: "monthly";
  mode: string;
  source: string;
  source_urls: string[];
  benchmark_id: string;
  benchmark_label: string;
  benchmark_tracks: string;
  is_proxy: boolean;
  fund: PerformanceSeriesOut;
  benchmark: PerformanceSeriesOut;
  disclaimers: string[];
};

export type PerformanceGrowthRequest = {
  ticker?: string | null;
  fund_identifier?: string | null;
  benchmark?: string | null;
  asset_class?: PerformanceAssetClass | null;
  benchmark_hint?: PerformanceAssetClass | null;
  start_dollars?: number;
  start_date?: string | null;
  end_date?: string | null;
  mode?: PerformanceMode | string | null;
};

export type PerformanceQuery = PerformanceGrowthRequest;
