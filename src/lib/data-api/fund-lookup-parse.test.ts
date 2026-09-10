import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { parseFundLookupResponse } from "./fund-lookup-parse.ts";

describe("GET /funds/lookup", () => {
  it("maps a live AGTHX awaiting_estimate hit", () => {
    const parsed = parseFundLookupResponse(
      200,
      {
        ticker: "AGTHX",
        fund_name: "The Growth Fund of America",
        fund_family: "American Funds",
        has_estimate: false,
        coverage_status: "awaiting_estimate",
        nav_per_share: "88.419998",
      },
      "AGTHX",
    );
    assert.equal(parsed.kind, "found");
    if (parsed.kind !== "found") return;
    assert.equal(parsed.coverageStatus, "awaiting_estimate");
    assert.equal(parsed.fund.ticker, "AGTHX");
    assert.ok(parsed.fund.nav > 0 && Math.abs(parsed.fund.nav - 88.419998) < 1e-6);
  });

  it("maps 404 not_in_universe to Add to universe, not an empty catalog", () => {
    const parsed = parseFundLookupResponse(
      404,
      {
        coverage_status: "not_in_universe",
        ticker: "ZZZZZ",
        add_to_universe: "POST /request/ticker",
      },
      "ZZZZZ",
    );
    assert.deepEqual(parsed, {
      kind: "not_in_universe",
      ticker: "ZZZZZ",
      addToUniverse: "POST /request/ticker",
    });
  });

  it("treats 5xx lookup as unavailable", () => {
    assert.equal(parseFundLookupResponse(502, {}, "AGTHX").kind, "unavailable");
  });
});
