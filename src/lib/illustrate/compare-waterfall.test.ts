import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { loadGrowthAndTaxDrag } from "./growth-tax-load.ts";
import type { CompareRequest, CompareResponse } from "./compare-types.ts";
import type { PerformanceQuery, PerformanceResponse } from "../performance/types.ts";

/**
 * Request budget after the Compare populate fix.
 *
 * Before (measured from source, AGTHX confirm):
 *   CompareWorkspace YoY + Growth YoY + Growth performance, then prefetch
 *   remounted Growth (`key={filledKey}` + prefetchKey in requestKey) and
 *   fetched performance again → 2 compare + 2 performance.
 *   3 tickers: 6 compare + 6 performance.
 *
 * After:
 *   /compare first paint skips the unpaid catalog dump.
 *   1 ticker → 1 YoY compare + 1 performance (in parallel) + 1 identity hydrate.
 *   3 tickers → 3 YoY + 3 performance (in parallel, progressive onRow).
 *   Adding a 4th ticker does not require a second compare storm for the
 *   first three when prefetch/cache covers them.
 */

function pack(ticker: string): PerformanceResponse {
  return {
    fund_ticker: ticker,
    fund_identifier: ticker,
    fund_name: ticker,
    asset_class: "equity",
    start_dollars: 10_000,
    start_date: "2024-12-31",
    end_date: "2025-12-31",
    as_of: "2025-12-31",
    frequency: "monthly",
    mode: "live",
    source: "live",
    source_urls: [],
    benchmark_id: "SPY",
    benchmark_label: "S&P 500",
    benchmark_tracks: "S&P 500",
    is_proxy: true,
    fund: {
      ticker,
      name: ticker,
      currency: "USD",
      price_unit: "usd_per_share_adjusted",
      return_unit: "decimal",
      growth_unit: "usd",
      points: [
        { date: "2024-12-31", adj_close: 80, monthly_return: null, growth_of_x: 10_000 },
        { date: "2025-12-31", adj_close: 88, monthly_return: 0.08, growth_of_x: 10_800 },
      ],
    },
    benchmark: {
      ticker: "SPY",
      name: "SPY",
      currency: "USD",
      price_unit: "usd_per_share_adjusted",
      return_unit: "decimal",
      growth_unit: "usd",
      points: [
        { date: "2024-12-31", adj_close: 400, monthly_return: null, growth_of_x: 10_000 },
        { date: "2025-12-31", adj_close: 428, monthly_return: 0.07, growth_of_x: 10_700 },
      ],
    },
    disclaimers: [],
  };
}

function yoy(ticker: string): CompareResponse {
  return {
    mode: "yoy",
    periods: [
      {
        year: 2025,
        left: {
          label: ticker,
          matched: true,
          totals: { estimated_tax: 120, estimated_tax_dollars: 120 },
        },
        right: {
          label: ticker,
          matched: true,
          totals: { estimated_tax: 120, estimated_tax_dollars: 120 },
        },
        deltas: { distribution_dollars: 0, estimated_tax: 0 },
      },
    ],
    summary: {
      normalized_holding_dollars: 10_000,
      total_tax_difference: 0,
      annualized_tax_drag_delta: 0,
      distribution_dollars_difference: 0,
      periods_compared: 1,
      common_inception: { from_year: 2025, to_year: 2025 },
    },
    notes: [],
  };
}

function tickerOf(request: CompareRequest | PerformanceQuery): string {
  if ("selectors" in request || "left" in request) {
    const compare = request as CompareRequest;
    return (
      compare.selectors?.ticker ??
      compare.left?.selectors?.ticker ??
      ""
    ).toUpperCase();
  }
  return String((request as PerformanceQuery).ticker ?? "").toUpperCase();
}

describe("Compare populate request budget", () => {
  it("one ticker: one performance + one YoY, overlapping start", async () => {
    const started: string[] = [];
    let resolveSlow!: () => void;
    const slow = new Promise<void>((resolve) => {
      resolveSlow = resolve;
    });

    const pending = loadGrowthAndTaxDrag(
      [{ ticker: "AGTHX" }],
      10_000,
      null,
      undefined,
      new AbortController().signal,
      {
        loaders: {
          async loadPerformance(request) {
            started.push(`perf:${tickerOf(request)}`);
            await slow;
            return pack("AGTHX");
          },
          async loadCompare(request) {
            started.push(`compare:${tickerOf(request)}`);
            return yoy("AGTHX");
          },
        },
      },
    );

    await new Promise((resolve) => setTimeout(resolve, 10));
    assert.deepEqual(started.sort(), ["compare:AGTHX", "perf:AGTHX"]);
    resolveSlow();
    const result = await pending;
    assert.equal(result.rows.length, 1);
    assert.equal(started.filter((item) => item.startsWith("compare:")).length, 1);
    assert.equal(started.filter((item) => item.startsWith("perf:")).length, 1);
  });

  it("three tickers: three performance + three YoY, no pair compare", async () => {
    const compares: string[] = [];
    const perfs: string[] = [];
    const result = await loadGrowthAndTaxDrag(
      [{ ticker: "AGTHX" }, { ticker: "AMCPX" }, { ticker: "VFIAX" }],
      10_000,
      null,
      undefined,
      new AbortController().signal,
      {
        loaders: {
          async loadPerformance(request) {
            perfs.push(tickerOf(request));
            return pack(tickerOf(request));
          },
          async loadCompare(request) {
            compares.push(`${request.mode}:${tickerOf(request)}`);
            return yoy(tickerOf(request) || "AGTHX");
          },
        },
      },
    );
    assert.equal(result.rows.length, 3);
    assert.deepEqual(perfs.sort(), ["AGTHX", "AMCPX", "VFIAX"]);
    assert.deepEqual(compares.sort(), [
      "yoy:AGTHX",
      "yoy:AMCPX",
      "yoy:VFIAX",
    ]);
  });

  it("adding a ticker with prefetch does not refetch the first book's compares", async () => {
    const compares: string[] = [];
    const first = await loadGrowthAndTaxDrag(
      [{ ticker: "AGTHX" }],
      10_000,
      null,
      undefined,
      new AbortController().signal,
      {
        loaders: {
          async loadPerformance(request) {
            return pack(tickerOf(request));
          },
          async loadCompare(request) {
            compares.push(tickerOf(request));
            return yoy(tickerOf(request));
          },
        },
      },
    );
    await loadGrowthAndTaxDrag(
      [{ ticker: "AGTHX" }, { ticker: "AMCPX" }],
      10_000,
      null,
      undefined,
      new AbortController().signal,
      {
        preferYoy: true,
        prefetchTax: first.rows.map((row) => ({
          ticker: row.input.ticker,
          tax: row.tax,
          taxSide: row.taxSide,
        })),
        loaders: {
          async loadPerformance(request) {
            return pack(tickerOf(request));
          },
          async loadCompare(request) {
            compares.push(tickerOf(request));
            return yoy(tickerOf(request));
          },
        },
      },
    );
    assert.deepEqual(compares, ["AGTHX", "AMCPX"]);
  });
});
