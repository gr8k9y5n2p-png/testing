import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  AWAITING_ESTIMATE_LABEL,
  fundPickerCoverageLabel,
  resolveCoverageStatus,
} from "./coverage-status.ts";

describe("coverage_status", () => {
  it("prefers a published Data coverage_status (Data #114; #112 Ready unblocked)", () => {
    assert.equal(
      resolveCoverageStatus({
        coverageStatus: "awaiting_estimate",
        foundInFunds: true,
        hasEstimate: true,
        hasUpcoming: true,
      }),
      "awaiting_estimate",
    );
    assert.equal(
      resolveCoverageStatus({
        coverageStatus: "estimate_announced",
        foundInFunds: true,
        hasEstimate: false,
      }),
      "estimate_announced",
    );
  });

  it("best-effort: /funds hit + no unpaid → awaiting_estimate; miss → not_in_universe", () => {
    assert.equal(
      resolveCoverageStatus({
        foundInFunds: true,
        hasEstimate: false,
        hasUpcoming: false,
      }),
      "awaiting_estimate",
    );
    assert.equal(
      resolveCoverageStatus({
        foundInFunds: true,
        hasEstimate: true,
      }),
      "estimate_announced",
    );
    assert.equal(
      resolveCoverageStatus({ foundInFunds: false }),
      "not_in_universe",
    );
  });

  it("labels AGTHX-class picker rows Awaiting Estimate and FBGRX announced as none", () => {
    assert.equal(
      fundPickerCoverageLabel({
        hasEstimate: false,
        bucket: "paid",
      }),
      AWAITING_ESTIMATE_LABEL,
    );
    assert.equal(
      fundPickerCoverageLabel({
        hasEstimate: true,
        bucket: "upcoming",
      }),
      null,
    );
  });
});
