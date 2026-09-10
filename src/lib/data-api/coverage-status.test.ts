import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  AWAITING_ESTIMATE_LABEL,
  fundPickerCoverageLabel,
  resolveCoverageStatus,
} from "./coverage-status.ts";

describe("coverage_status", () => {
  it("prefers the published Data field when present", () => {
    assert.equal(
      resolveCoverageStatus({
        coverageStatus: "awaiting_estimate",
        foundInFunds: true,
        hasEstimate: true,
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
    assert.equal(
      resolveCoverageStatus({
        coverageStatus: "not_in_universe",
        foundInFunds: true,
      }),
      "not_in_universe",
    );
  });

  it("infers AGTHX in-universe awaiting when has_estimate is false", () => {
    assert.equal(
      resolveCoverageStatus({
        foundInFunds: true,
        hasEstimate: false,
        hasUpcoming: false,
      }),
      "awaiting_estimate",
    );
  });

  it("treats an exact ticker miss as not_in_universe", () => {
    assert.equal(
      resolveCoverageStatus({ foundInFunds: false }),
      "not_in_universe",
    );
  });

  it("labels Search chips Awaiting Estimate only for awaiting funds", () => {
    assert.equal(
      fundPickerCoverageLabel({ hasEstimate: false, bucket: "paid" }),
      AWAITING_ESTIMATE_LABEL,
    );
    assert.equal(
      fundPickerCoverageLabel({ hasEstimate: true, bucket: "upcoming" }),
      null,
    );
  });
});
