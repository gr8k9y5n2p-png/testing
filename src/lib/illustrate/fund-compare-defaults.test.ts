import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  defaultComparePeer,
  findFundByTicker,
} from "./fund-compare-defaults.ts";

const funds = [
  { id: "amcpx", ticker: "AMCPX", category: "Large Growth", family: "American Funds" },
  { id: "agthx", ticker: "AGTHX", category: "Large Growth", family: "American Funds" },
  { id: "vigax", ticker: "VIGAX", category: "Large Growth", family: "Vanguard" },
  { id: "awshx", ticker: "AWSHX", category: "Large Value", family: "American Funds" },
];

describe("fund-compare defaults", () => {
  it("finds a ticker case-insensitively", () => {
    assert.equal(findFundByTicker(funds, "amcpx")?.id, "amcpx");
    assert.equal(findFundByTicker(funds, " VIGAX ")?.ticker, "VIGAX");
    assert.equal(findFundByTicker(funds, ""), null);
    assert.equal(findFundByTicker(funds, "ZZNOPE"), null);
  });

  it("prefers a same-category peer from another family", () => {
    const peer = defaultComparePeer(funds[0], funds);
    assert.equal(peer?.ticker, "VIGAX");
  });
});
