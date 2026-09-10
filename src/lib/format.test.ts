import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  compareOptionalIsoDates,
  formatDate,
  formatOptionalDate,
  sortFunds,
} from "./format.ts";
import type { FundEstimateView } from "../data/types.ts";

describe("formatDate", () => {
  it("includes the year in advisor-facing dates", () => {
    assert.equal(formatDate("2025-12-15"), "Dec 15, 2025");
    assert.equal(formatDate("2026-08-12"), "Aug 12, 2026");
    assert.equal(formatDate("2026-09-19"), "Sep 19, 2026");
  });
});

describe("formatOptionalDate", () => {
  it("uses the year-inclusive format by default", () => {
    assert.equal(formatOptionalDate("2025-12-15"), "Dec 15, 2025");
    assert.equal(formatOptionalDate("2026-08-14"), "Aug 14, 2026");
  });

  it("does not invent missing or invalid dates", () => {
    assert.equal(formatOptionalDate(null), "—");
    assert.equal(formatOptionalDate(undefined), "—");
    assert.equal(formatOptionalDate(""), "—");
    assert.equal(formatOptionalDate("not-a-date"), "—");
  });

  it("keeps compact month-day only when asked", () => {
    assert.equal(formatOptionalDate("2025-12-15", true), "Dec 15");
  });
});

describe("compareOptionalIsoDates", () => {
  it("sorts by calendar day, not display-string blobs", () => {
    assert.equal(compareOptionalIsoDates("2026-08-29", "2026-12-12"), -1);
    assert.equal(compareOptionalIsoDates("2025-12-15", "2026-08-29"), -1);
    assert.equal(compareOptionalIsoDates("2026-08-29", "2026-08-29"), 0);
  });

  it("keeps missing or invalid dates after real ones and does not invent a day", () => {
    assert.equal(compareOptionalIsoDates(null, "2026-08-29"), 1);
    assert.equal(compareOptionalIsoDates("2026-08-29", undefined), -1);
    assert.equal(compareOptionalIsoDates("", "not-a-date"), 0);
  });
});

describe("sortFunds date columns", () => {
  function row(
    ticker: string,
    asOfDate: string,
    recordDate: string | null,
    exDate: string | null,
  ): FundEstimateView {
    return {
      id: ticker,
      fundName: ticker,
      ticker,
      cusip: "000000000",
      family: "American Funds",
      category: "Large Growth",
      shareClass: "Class A",
      nav: 40,
      estimatedDistributionAmount: 1,
      estimatedOrdinaryIncome: 0.2,
      estimatedCapitalGains: 0.8,
      estimatedDistributionPctNav: 2,
      publishedAt: asOfDate,
      asOfDate,
      recordDate,
      exDate,
      payableDate: null,
      publicationStage: "preliminary_estimate",
      bucket: "upcoming",
      paidHistory: [],
      distributionYear: 2026,
      categoryAveragePctNav: 2,
      vsCategoryPctNav: 0,
    };
  }

  it("sorts Announced / Record / Ex-div by ISO date values", () => {
    const funds = [
      row("LATE", "2026-12-15", "2026-12-12", "2026-12-15"),
      row("EARLY", "2026-08-29", null, "2026-09-01"),
      row("MID", "2026-09-05", "2026-09-10", null),
    ];

    assert.deepEqual(
      sortFunds(funds, "asOfDate", "asc").map((fund) => fund.ticker),
      ["EARLY", "MID", "LATE"],
    );
    assert.deepEqual(
      sortFunds(funds, "recordDate", "asc").map((fund) => fund.ticker),
      ["MID", "LATE", "EARLY"],
    );
    assert.deepEqual(
      sortFunds(funds, "exDate", "asc").map((fund) => fund.ticker),
      ["EARLY", "LATE", "MID"],
    );
  });

  it("sorts Dist $/Share by per-share amount, highest first then lowest", () => {
    const low = row("LOW", "2026-07-31", "2026-12-12", "2026-12-15");
    low.estimatedDistributionAmount = 0.25;
    low.estimatedDistributionPctNav = 20;
    const mid = row("MID$", "2026-07-31", "2026-12-12", "2026-12-15");
    mid.estimatedDistributionAmount = 2.5;
    mid.estimatedDistributionPctNav = 1;
    const high = row("HIGH", "2026-07-31", "2026-12-12", "2026-12-15");
    high.estimatedDistributionAmount = 21.021;
    high.estimatedDistributionPctNav = 2;

    assert.deepEqual(
      sortFunds([low, high, mid], "estimatedDistributionAmount", "desc").map(
        (fund) => fund.ticker,
      ),
      ["HIGH", "MID$", "LOW"],
    );
    assert.deepEqual(
      sortFunds([high, low, mid], "estimatedDistributionAmount", "asc").map(
        (fund) => fund.ticker,
      ),
      ["LOW", "MID$", "HIGH"],
    );
  });

  it("sorts % of NAV by Dist $/share ÷ weekly NAV, not published %", () => {
    const publishedWins = row("PUB", "2026-07-31", "2026-12-12", "2026-12-15");
    publishedWins.estimatedDistributionAmount = 1;
    publishedWins.nav = 100;
    publishedWins.estimatedDistributionPctNav = 20;
    publishedWins.publishedPctOfNav = 20;

    const distWins = row("DIST", "2026-07-31", "2026-12-12", "2026-12-15");
    distWins.estimatedDistributionAmount = 5;
    distWins.nav = 100;
    distWins.estimatedDistributionPctNav = 2;
    distWins.publishedPctOfNav = 2;

    assert.deepEqual(
      sortFunds([publishedWins, distWins], "estimatedDistributionPctNav", "desc").map(
        (fund) => fund.ticker,
      ),
      ["DIST", "PUB"],
    );
  });
});
