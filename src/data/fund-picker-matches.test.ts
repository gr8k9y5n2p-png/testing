import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { mapFundsApiItem } from "./funds-list.ts";
import { fundPickerMatches } from "./fund-picker-matches.ts";

const here = dirname(fileURLToPath(import.meta.url));

describe("Search a fund FBGRX match", () => {
  it("finds FBGRX from GET /api/funds when the SSR catalog is empty", () => {
    const remote = mapFundsApiItem({
      ticker: "FBGRX",
      fund_name: "Blue Chip Growth",
      fund_family: "Fidelity",
      has_estimate: false,
      nav_per_share: "312.260010",
      nav_as_of: "2026-09-08",
    });
    assert.equal(remote.bucket, "paid");
    assert.equal(remote.hasEstimate, false);
    const matches = fundPickerMatches([], [remote], "FBGRX");
    assert.equal(matches.length, 1);
    assert.equal(matches[0]?.ticker, "FBGRX");
    assert.equal(matches[0]?.fundName, "Blue Chip Growth");
  });

  it("finds FBGRX from a typed query against the local catalog", () => {
    const local = mapFundsApiItem({
      ticker: "FBGRX",
      fund_name: "Blue Chip Growth",
      fund_family: "Fidelity",
      has_estimate: true,
    });
    const matches = fundPickerMatches([local], [], "fbgrx");
    assert.equal(matches.length, 1);
    assert.equal(matches[0]?.ticker, "FBGRX");
  });

  it("does not require Upcoming / has_estimate to keep the identity row selectable", () => {
    const remote = mapFundsApiItem({
      ticker: "FBGRX",
      fund_name: "Blue Chip Growth",
      fund_family: "Fidelity",
      has_estimate: false,
    });
    const matches = fundPickerMatches([], [remote], "Blue Chip");
    assert.equal(matches.some((fund) => fund.ticker === "FBGRX"), true);
  });

  it("finds AGTHX from GET /api/funds when has_estimate is false", () => {
    const remote = mapFundsApiItem({
      ticker: "AGTHX",
      fund_name: "The Growth Fund of America",
      fund_family: "American Funds",
      has_estimate: false,
      nav_per_share: "88.42",
      coverage_status: "awaiting_estimate",
    });
    assert.equal(remote.hasEstimate, false);
    assert.equal(remote.coverageStatus, "awaiting_estimate");
    const matches = fundPickerMatches([], [remote], "AGTHX");
    assert.equal(matches.length, 1);
    assert.equal(matches[0]?.ticker, "AGTHX");
    assert.ok(matches[0]!.nav > 0 && Math.abs(matches[0]!.nav - 88.42) < 1e-6);
  });

  it("FundPicker always hits /api/funds for a typed query, not only search_miss", () => {
    const picker = readFileSync(
      join(here, "../components/illustrate/FundPicker.tsx"),
      "utf8",
    );
    const client = readFileSync(join(here, "../lib/data-api/funds-client.ts"), "utf8");
    assert.match(picker, /fundPickerMatches/);
    assert.match(picker, /fetchFundsSearch/);
    assert.match(client, /\/api\/funds/);
    assert.match(picker, /if \(!q\)/);
    assert.doesNotMatch(picker, /reportSearchMiss \|\| !q/);
    assert.doesNotMatch(
      picker,
      /const \{ upcoming, paid \} = splitFundsByBucket/,
    );
    assert.match(picker, /fetchFundsSearch/);
    assert.match(picker, /DATA_API_UNAVAILABLE/);
    assert.match(picker, /ADD_TO_UNIVERSE/);
    assert.match(picker, /LISTS_AWAITING_ESTIMATE/);
    assert.match(picker, /remoteUnavailable/);
  });
});
