import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  PERFORMANCE_UNAVAILABLE_HINT,
  PERFORMANCE_UNAVAILABLE_LABEL,
  isMissingPerformanceError,
  performanceCoveredFromRaw,
  performanceFromFetchError,
  performancePackIsUsable,
} from "./coverage.ts";
import type { PerformanceResponse } from "./types.ts";

class RequestError extends Error {
  status: number;
  code?: string;
  constructor(message: string, status: number, code?: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

function pack(overrides: Partial<PerformanceResponse> = {}): PerformanceResponse {
  return {
    fund_ticker: "AMCPX",
    fund_identifier: "AMCPX",
    fund_name: "AMCAP Fund",
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
      ticker: "AMCPX",
      name: "AMCAP Fund",
      currency: "USD",
      price_unit: "usd_per_share_adjusted",
      return_unit: "decimal",
      growth_unit: "usd",
      points: [
        {
          date: "2024-12-31",
          adj_close: 40,
          monthly_return: null,
          growth_of_x: 10_000,
        },
        {
          date: "2025-12-31",
          adj_close: 44,
          monthly_return: 0.1,
          growth_of_x: 11_000,
        },
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
        {
          date: "2024-12-31",
          adj_close: 400,
          monthly_return: null,
          growth_of_x: 10_000,
        },
      ],
    },
    disclaimers: [],
    ...overrides,
  };
}

describe("missing performance coverage", () => {
  it("treats 404 as a skippable missing pack", () => {
    assert.equal(
      isMissingPerformanceError(new RequestError("No performance fixture for VIGAX", 404)),
      true,
    );
    assert.equal(
      isMissingPerformanceError(new RequestError("Performance failed (404)", 404, "not_found")),
      true,
    );
  });

  it("treats uncovered codes as missing, not a hard module error", () => {
    assert.equal(
      isMissingPerformanceError(new RequestError("Ticker uncovered", 400, "uncovered")),
      true,
    );
    assert.equal(isMissingPerformanceError(new RequestError("uncovered pack", 422)), true);
  });

  it("does not treat other illustrate errors as missing performance", () => {
    assert.equal(
      isMissingPerformanceError(new RequestError("Need fund price", 422, "nav_required")),
      false,
    );
    assert.equal(isMissingPerformanceError(new Error("network down")), false);
  });

  it("returns null from a per-ticker fetch error instead of throwing", () => {
    assert.equal(
      performanceFromFetchError(new RequestError("No performance fixture for VIGAX", 404)),
      null,
    );
  });

  it("rejects uncovered or empty packs so callers never invent a series", () => {
    assert.equal(performancePackIsUsable(pack()), true);
    assert.equal(performancePackIsUsable(pack({ covered: false })), false);
    assert.equal(
      performancePackIsUsable(
        pack({
          fund: {
            ticker: "VIGAX",
            name: "VIGAX",
            currency: "USD",
            price_unit: "usd",
            return_unit: "decimal",
            growth_unit: "usd",
            points: [],
          },
        }),
      ),
      false,
    );
    assert.equal(performancePackIsUsable(null), false);
  });

  it("normalizes covered flags from the Data payload", () => {
    assert.equal(performanceCoveredFromRaw(false), false);
    assert.equal(performanceCoveredFromRaw("false"), false);
    assert.equal(performanceCoveredFromRaw(true), true);
    assert.equal(performanceCoveredFromRaw(undefined), undefined);
  });

  it("keeps the N/A empty-state copy", () => {
    assert.match(PERFORMANCE_UNAVAILABLE_LABEL, /Performance not available/i);
    assert.match(PERFORMANCE_UNAVAILABLE_HINT, /N\/A/);
    assert.doesNotMatch(PERFORMANCE_UNAVAILABLE_HINT, /\$0|Upcoming/);
  });
});
