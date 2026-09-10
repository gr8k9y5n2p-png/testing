import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  collectTaxYearsFromFund,
  collectTaxYearsFromFunds,
  mergeTaxYears,
  taxYearsFromPayload,
} from "./tax-years.ts";
import type { FundEstimate } from "./types.ts";

function fund(patch: Partial<FundEstimate> = {}): FundEstimate {
  return {
    id: "fund-1",
    fundName: "AMCAP",
    ticker: "AMCPX",
    cusip: "",
    family: "American Funds",
    category: "Large Growth",
    shareClass: "A",
    nav: 10,
    estimatedDistributionAmount: 0.2,
    estimatedOrdinaryIncome: 0.1,
    estimatedCapitalGains: 0.1,
    estimatedDistributionPctNav: 0.01,
    publishedAt: "2026-09-01",
    asOfDate: "2026-09-01",
    recordDate: "2026-12-12",
    exDate: "2026-12-15",
    payableDate: "2026-12-17",
    publicationStage: "preliminary_estimate",
    bucket: "upcoming",
    paidHistory: [],
    distributionYear: 2026,
    ...patch,
  };
}

describe("tax years from Data", () => {
  it("merges concrete years newest first and drops invented / invalid values", () => {
    assert.deepEqual(mergeTaxYears([2024, "2021", 2024], [2025]), [2025, 2024, 2021]);
    assert.deepEqual(mergeTaxYears([0, 1899, 3001, "n/a", null]), []);
    assert.deepEqual(taxYearsFromPayload({ tax_years: [2022, 2023] }), [2023, 2022]);
    assert.deepEqual(taxYearsFromPayload({ facets: { years: ["2024"] } }), [2024]);
    assert.deepEqual(taxYearsFromPayload({ years: [] }), []);
  });

  it("collects paid-history and event years without filling a missing range", () => {
    const row = fund({
      distributionYear: 2026,
      paidHistory: [
        {
          asOfDate: "2024-12-10",
          recordDate: "2024-12-12",
          exDate: "2024-12-13",
          payableDate: "2024-12-16",
          publicationStage: "paid",
          estimatedDistributionAmount: 1,
          estimatedOrdinaryIncome: 1,
          estimatedCapitalGains: 0,
          estimatedDistributionPctNav: 0.02,
          distributionYear: 2024,
        },
      ],
    });
    assert.deepEqual(collectTaxYearsFromFund(row), [2026, 2024]);
    assert.deepEqual(collectTaxYearsFromFunds([row, fund({ distributionYear: 2025 })]), [
      2026,
      2025,
      2024,
    ]);
    assert.ok(!collectTaxYearsFromFunds([row]).includes(2021));
    assert.ok(!collectTaxYearsFromFunds([row]).includes(2022));
    assert.ok(!collectTaxYearsFromFunds([row]).includes(2023));
  });
});
