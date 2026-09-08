import assert from "node:assert/strict";
import { describe, it } from "node:test";
import type { CompareResponse } from "./compare-types.ts";
import {
  growthFundKey,
  isRemovableGrowthSeries,
  mergeSeedFunds,
  removeGrowthFund,
  upcomingPreferSide,
  upcomingRowForSelectedFunds,
} from "./growth-selection.ts";

function fund(ticker: string) {
  return { ticker, label: ticker, fundIdentifier: ticker };
}

function upcomingCompare(leftDollars: number | null, rightDollars: number | null): CompareResponse {
  return {
    mode: "fund_vs_fund",
    as_of: "2026-09-01",
    holding_dollars: 10_000,
    left: { label: "AMCPX", ticker: "AMCPX" },
    right: { label: "AGTHX", ticker: "AGTHX" },
    periods: [],
    summary: {
      upcoming_taxable_distribution: {
        left_dollars: leftDollars,
        right_dollars: rightDollars,
        left_publication_stage: leftDollars != null ? "announced" : "unannounced",
        right_publication_stage: rightDollars != null ? "announced" : "unannounced",
      },
    },
  } as CompareResponse;
}

describe("growth fund remove selection", () => {
  it("removes AMCPX and AGTHX and allows an empty chart", () => {
    const selected = [fund("AMCPX"), fund("AGTHX")];
    const withoutAmcpx = removeGrowthFund(selected, "amcpx");
    assert.deepEqual(
      withoutAmcpx.map((row) => row.ticker),
      ["AGTHX"],
    );
    assert.deepEqual(removeGrowthFund(withoutAmcpx, "AGTHX"), []);
  });

  it("does not treat the S&P 500 benchmark as removable", () => {
    assert.equal(isRemovableGrowthSeries("AMCPX"), true);
    assert.equal(isRemovableGrowthSeries("AGTHX"), true);
    assert.equal(isRemovableGrowthSeries("bench-SPY", true), false);
    assert.equal(isRemovableGrowthSeries("S&P 500", true), false);
  });

  it("clears that fund’s upcoming badge while keeping the other series", () => {
    const pair = upcomingCompare(522, null);
    const rows = [
      { ticker: "AMCPX", tax: pair, taxSide: "left" as const },
      { ticker: "AGTHX", tax: pair, taxSide: "right" as const },
    ];
    const both = upcomingRowForSelectedFunds(rows, [fund("AMCPX"), fund("AGTHX")]);
    assert.equal(both?.ticker, "AMCPX");
    assert.equal(upcomingPreferSide(both?.taxSide ?? "auto"), "left");
    assert.equal(both?.tax?.summary.upcoming_taxable_distribution?.left_dollars, 522);

    const afterAmcpx = upcomingRowForSelectedFunds(rows, [fund("AGTHX")]);
    assert.equal(afterAmcpx?.ticker, "AGTHX");
    assert.equal(upcomingPreferSide(afterAmcpx?.taxSide ?? "auto"), "right");
    assert.equal(
      afterAmcpx?.tax?.summary.upcoming_taxable_distribution?.right_dollars,
      null,
    );

    const afterAgthx = upcomingRowForSelectedFunds(rows, [fund("AMCPX")]);
    assert.equal(afterAgthx?.ticker, "AMCPX");
    assert.equal(
      afterAgthx?.tax?.summary.upcoming_taxable_distribution?.left_dollars,
      522,
    );
  });

  it("keeps Add Fund extras when search reseeds a ticker", () => {
    const merged = mergeSeedFunds([fund("AGTHX"), fund("FBGRX")], [fund("AMCPX")]);
    assert.deepEqual(
      merged.map((row) => growthFundKey(row).ticker),
      ["AMCPX", "AGTHX", "FBGRX"],
    );
  });
});
