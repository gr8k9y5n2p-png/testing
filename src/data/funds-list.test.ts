import assert from "node:assert/strict";
import { test } from "node:test";
import { mapFundsApiItem } from "./funds-list.ts";

test("mapFundsApiItem keeps missing estimates honest", () => {
  const view = mapFundsApiItem({
    ticker: "VFIAX",
    fund_name: "500 Index Fund Admiral Shares",
    fund_family: "Vanguard",
    fund_identifier: "VFIAX",
    latest_as_of: "2025-12-24",
    has_estimate: false,
  });
  assert.equal(view.ticker, "VFIAX");
  assert.equal(view.fundName, "500 Index Fund Admiral Shares");
  assert.equal(view.hasEstimate, false);
  assert.equal(view.estimatedDistributionPctNav, 0);
});

test("mapFundsApiItem accepts a null ticker without inventing one", () => {
  const view = mapFundsApiItem({
    ticker: null,
    fund_name: "AB All Market Total Return Portfolio",
    fund_family: "AllianceBernstein",
    fund_identifier: "ab-all-market-total-return-portfolio",
    latest_as_of: "2025-10-31",
    has_estimate: true,
  });
  assert.equal(view.ticker, "—");
  assert.equal(view.hasEstimate, true);
  assert.match(view.id, /ab-all-market-total-return-portfolio/);
});
