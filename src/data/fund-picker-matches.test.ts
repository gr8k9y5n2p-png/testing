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

  it("FundPicker always hits /api/funds for a typed query, not only search_miss", () => {
    const picker = readFileSync(
      join(here, "../components/illustrate/FundPicker.tsx"),
      "utf8",
    );
    assert.match(picker, /fundPickerMatches/);
    assert.match(picker, /fetchRemoteFunds/);
    assert.match(picker, /\/api\/funds/);
    assert.match(picker, /if \(!q\)/);
    assert.doesNotMatch(picker, /reportSearchMiss \|\| !q/);
    assert.doesNotMatch(
      picker,
      /const \{ upcoming, paid \} = splitFundsByBucket/,
    );
  });
});
