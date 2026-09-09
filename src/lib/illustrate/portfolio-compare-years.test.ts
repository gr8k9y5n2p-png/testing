import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { portfolioPeriodTaxIsUnmatched } from "./portfolio-compare-years.ts";

describe("portfolioPeriodTaxIsUnmatched", () => {
  it("keeps matched published $0 as a real zero", () => {
    assert.equal(
      portfolioPeriodTaxIsUnmatched({ matched: true, estimatedTax: 0 }),
      false,
    );
  });

  it("treats covered:false / gap_reason / omitted matched + null totals as N/A", () => {
    assert.equal(
      portfolioPeriodTaxIsUnmatched({
        covered: false,
        estimatedTax: 0,
      }),
      true,
    );
    assert.equal(
      portfolioPeriodTaxIsUnmatched({
        estimatedTax: null,
      }),
      true,
    );
    assert.equal(
      portfolioPeriodTaxIsUnmatched({
        matched: false,
        estimatedTax: 0,
      }),
      true,
    );
  });

  it("densifies published tax even when Upcoming left the holding uncovered", () => {
    assert.equal(
      portfolioPeriodTaxIsUnmatched({
        covered: false,
        gapReason: "no unpaid announce",
        estimatedTax: 2140,
      }),
      false,
    );
    assert.equal(
      portfolioPeriodTaxIsUnmatched({
        gapReason: "uncovered",
        estimatedTax: 12,
      }),
      false,
    );
  });

  it("keeps omitted matched + numeric tax (including 0) when covered", () => {
    assert.equal(
      portfolioPeriodTaxIsUnmatched({ estimatedTax: 40 }),
      false,
    );
    assert.equal(
      portfolioPeriodTaxIsUnmatched({ covered: true, estimatedTax: 0 }),
      false,
    );
  });
});
