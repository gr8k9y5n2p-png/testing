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
  assert.equal(view.nav, 0);
  assert.equal(view.navAsOf, null);
  assert.equal(view.bucket, "paid");
  assert.equal(view.publicationStage, null);
});

test("mapFundsApiItem reads live weekly NAV and does not invent a miss", () => {
  const view = mapFundsApiItem({
    ticker: "ABALX",
    fund_name: "American Balanced Fund",
    fund_family: "American Funds",
    nav_per_share: "40.849998",
    nav_as_of: "2026-09-08",
    nav_source: "yahoo_last_close",
    has_estimate: false,
  });
  assert.equal(view.nav, 40.849998);
  assert.equal(view.navAsOf, "2026-09-08");
  assert.equal(view.navSource, "yahoo_last_close");

  const missing = mapFundsApiItem({
    ticker: "ZZNOPE",
    fund_name: "Unknown",
    fund_family: "Unknown",
    nav_per_share: null,
    has_estimate: false,
  });
  assert.equal(missing.nav, 0);
  assert.equal(missing.navAsOf, null);
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
  assert.equal(view.bucket, "paid");
  assert.equal(view.publicationStage, null);
  assert.equal(view.estimatedDistributionAmount, 0);
  assert.match(view.id, /ab-all-market-total-return-portfolio/);
});
