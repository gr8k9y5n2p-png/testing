import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  isPerformanceUnavailable,
  performanceHasFundSeries,
  usablePerformance,
} from "./series.ts";
import type { PerformanceResponse } from "./types.ts";

function response(
  points: Array<{ date: string; growth_of_x?: number }> = [],
): PerformanceResponse {
  return {
    fund_ticker: "SPY",
    fund_identifier: "SPY",
    fund_name: "SPDR S&P 500 ETF Trust",
    asset_class: "equity",
    start_dollars: 10_000,
    start_date: "2021-01-01",
    end_date: "2026-01-01",
    as_of: "2026-01-01",
    frequency: "monthly",
    mode: "fixture",
    source: "fixture",
    source_urls: [],
    benchmark_id: "SPY",
    benchmark_label: "SPY",
    benchmark_tracks: "S&P 500",
    is_proxy: true,
    fund: {
      ticker: "SPY",
      name: "SPY",
      currency: "USD",
      price_unit: "usd_per_share_adjusted",
      return_unit: "decimal",
      growth_unit: "usd",
      points: points.map((point) => ({
        date: point.date,
        adj_close: 100,
        monthly_return: null,
        growth_of_x: point.growth_of_x ?? 10_000,
      })),
    },
    benchmark: {
      ticker: "SPY",
      name: "SPY",
      currency: "USD",
      price_unit: "usd_per_share_adjusted",
      return_unit: "decimal",
      growth_unit: "usd",
      points: [],
    },
    disclaimers: [],
  };
}

describe("performance series degrade", () => {
  it("treats 404 and empty points as unavailable, not a series", () => {
    assert.equal(performanceHasFundSeries(null), false);
    assert.equal(performanceHasFundSeries(response([])), false);
    assert.equal(usablePerformance(response([])), null);
    assert.equal(
      isPerformanceUnavailable({ status: 404, message: "No performance fixture for ABALX" }),
      true,
    );
    assert.equal(isPerformanceUnavailable(new Error("No performance fixture for ZZXYZ")), true);
    assert.equal(isPerformanceUnavailable({ status: 500 }), false);
  });

  it("keeps a fixture pack (SPY) as a usable series", () => {
    const pack = response([
      { date: "2024-12-31", growth_of_x: 10_000 },
      { date: "2025-12-31", growth_of_x: 11_200 },
    ]);
    assert.equal(performanceHasFundSeries(pack), true);
    assert.equal(usablePerformance(pack), pack);
  });
});
