import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import type { FundEstimateView } from "../../data/types.ts";
import {
  firstSearchParam,
  fundHistoryPath,
  growthFundFromTicker,
  HOMEPAGE_GROWTH_FUNDS,
  resolveFundView,
} from "./fund-history.ts";

const here = dirname(fileURLToPath(import.meta.url));

function view(ticker: string, fundName: string, family = "American Funds"): FundEstimateView {
  return {
    id: ticker.toLowerCase(),
    fundName,
    ticker,
    cusip: "000000000",
    family,
    category: "Large Growth",
    shareClass: "Class A",
    nav: 41.22,
    estimatedDistributionAmount: 2.6,
    estimatedOrdinaryIncome: 0.5,
    estimatedCapitalGains: 2.1,
    estimatedDistributionPctNav: 6.4,
    publishedAt: "2026-09-05",
    asOfDate: "2026-08-29",
    distributionYear: 2026,
    categoryAveragePctNav: 6.4,
    vsCategoryPctNav: 0,
  };
}

const funds = [
  view("AGTHX", "The Growth Fund of America"),
  view("AMCPX", "AMCAP Fund"),
];

describe("fund history deep-link", () => {
  it("builds /?ticker= + #illustrate", () => {
    assert.equal(fundHistoryPath("amcap"), "/?ticker=AMCAP#illustrate");
    assert.equal(fundHistoryPath(" AGTHX "), "/?ticker=AGTHX#illustrate");
  });

  it("reads the first ticker search param", () => {
    assert.equal(firstSearchParam("amcpx"), "AMCPX");
    assert.equal(firstSearchParam(["dodix", "agthx"]), "DODIX");
    assert.equal(firstSearchParam("  "), undefined);
    assert.equal(firstSearchParam(undefined), undefined);
  });

  it("resolves AMCAP to the AMCPX seed row", () => {
    const match = resolveFundView(funds, "AMCAP");
    assert.equal(match?.ticker, "AMCPX");
    assert.equal(match?.fundName, "AMCAP Fund");
  });

  it("keeps an exact ticker match", () => {
    assert.equal(resolveFundView(funds, "AGTHX")?.ticker, "AGTHX");
  });

  it("builds a GrowthAndTaxDrag seed without inventing a benchmark", () => {
    const input = growthFundFromTicker("AMCAP", funds);
    assert.deepEqual(input, {
      ticker: "AMCPX",
      label: "AMCPX",
      fundIdentifier: "AMCPX",
      fundFamily: "American Funds",
      fundName: "AMCAP Fund",
      navPerShare: 41.22,
    });
    assert.equal(Object.hasOwn(input ?? {}, "benchmark"), false);
  });

  it("does not preload homepage growth funds", () => {
    assert.deepEqual(HOMEPAGE_GROWTH_FUNDS, []);
    assert.equal(
      HOMEPAGE_GROWTH_FUNDS.some((fund) => fund.ticker === "FCNTX"),
      false,
    );
  });

  it("does not mount GrowthAndTaxDragModule on Search", () => {
    const app = readFileSync(
      join(here, "../../components/AftertaxApp.tsx"),
      "utf8",
    );
    const moduleFile = readFileSync(
      join(here, "../../components/illustrate/GrowthAndTaxDragModule.tsx"),
      "utf8",
    );
    assert.doesNotMatch(app, /GrowthAndTaxDragModule/);
    assert.doesNotMatch(app, /<GrowthAndTaxDragModule/);
    assert.match(app, /<IllustratePanel/);
    assert.match(moduleFile, /export function GrowthAndTaxDragModule/);
  });
});
