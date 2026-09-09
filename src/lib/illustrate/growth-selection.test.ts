import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  growthFundKey,
  isRemovableGrowthSeries,
  mergeSeedFunds,
  removeGrowthFund,
} from "./growth-selection.ts";

function fund(ticker: string) {
  return { ticker, label: ticker, fundIdentifier: ticker };
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

  it("keeps Add Fund extras when search reseeds a ticker", () => {
    const merged = mergeSeedFunds([fund("AGTHX"), fund("FBGRX")], [fund("AMCPX")]);
    assert.deepEqual(
      merged.map((row) => growthFundKey(row).ticker),
      ["AMCPX", "AGTHX", "FBGRX"],
    );
  });
});
