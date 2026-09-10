import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { mapFundsApiItem } from "./funds-list.ts";
import { fundPickerMatches } from "./fund-picker-matches.ts";
import { hideUpcomingAmounts } from "./hydrate-funds.ts";
import {
  AWAITING_ESTIMATE_LABEL,
  fundPickerCoverageLabel,
  resolveCoverageStatus,
} from "../lib/data-api/coverage-status.ts";
import { listRowFromFund } from "../lib/lists/rows.ts";
import { fillNavPerShareInput } from "../lib/illustrate/nav-math.ts";

const here = dirname(fileURLToPath(import.meta.url));

/** Live Data `/funds?q=AGTHX` while green — do not invent. */
const AGTHX = mapFundsApiItem({
  ticker: "AGTHX",
  fund_name: "The Growth Fund of America",
  fund_family: "American Funds",
  has_estimate: false,
  coverage_status: "awaiting_estimate",
  nav_per_share: "88.42",
  nav_as_of: "2026-09-08",
});

describe("Eric product lock — paid-only funds stay searchable", () => {
  it("Search AGTHX matches from /funds identity against an Upcoming-only book", () => {
    const upcomingBook = mapFundsApiItem({
      ticker: "FBGRX",
      fund_name: "Blue Chip Growth",
      fund_family: "Fidelity",
      has_estimate: true,
    });
    const matches = fundPickerMatches([upcomingBook], [AGTHX], "AGTHX");
    assert.equal(matches.length, 1);
    assert.equal(matches[0]?.ticker, "AGTHX");
    assert.equal(matches[0]?.hasEstimate, false);
    assert.ok(matches[0]!.nav > 0 && Math.abs(matches[0]!.nav - 88.42) < 1e-6);
    assert.equal(hideUpcomingAmounts(AGTHX), true);
  });

  it("Lists AGTHX is found with NAV ~$88.42 and estimate columns empty — not NOT FOUND", () => {
    const row = listRowFromFund({
      ticker: "AGTHX",
      fund: AGTHX,
      found: true,
    });
    assert.equal(row.found, true);
    assert.equal(row.status, "awaiting_estimate");
    assert.notEqual(row.status, "not_found");
    assert.ok(row.nav != null && Math.abs(row.nav - 88.42) < 1e-6);
    assert.equal(row.distPerShare, null);
    assert.equal(row.estimateTypes.long_term_capital_gains, null);
  });

  it("$ / share soft-fills NAV PER SHARE from nav_per_share", () => {
    assert.equal(fillNavPerShareInput("", 88.42), "88.42");
    assert.equal(fillNavPerShareInput("90", 88.42), "90");
  });

  it("Search / Compare / Lists do not gate autocomplete on has_estimate or Upcoming", () => {
    const picker = readFileSync(
      join(here, "../components/illustrate/FundPicker.tsx"),
      "utf8",
    );
    const field = readFileSync(
      join(here, "../components/illustrate/portfolio-compare/TickerField.tsx"),
      "utf8",
    );
    const client = readFileSync(join(here, "../lib/data-api/funds-client.ts"), "utf8");
    const lists = readFileSync(join(here, "../components/lists/ListsWorkspace.tsx"), "utf8");
    const panel = readFileSync(
      join(here, "../components/illustrate/IllustratePanel.tsx"),
      "utf8",
    );
    assert.doesNotMatch(picker, /splitFundsByBucket/);
    assert.doesNotMatch(picker, /hasEstimate === true/);
    assert.match(client, /nav_only/);
    assert.match(field, /fetchFundsSearch/);
    assert.match(lists, /LISTS_AWAITING_ESTIMATE/);
    assert.match(lists, /ADD_TO_UNIVERSE/);
    assert.match(lists, /source: "web"/);
    assert.match(picker, /ADD_TO_UNIVERSE/);
    assert.match(picker, /source: "web"/);
    assert.match(panel, /fillNavPerShareInput/);
    assert.match(panel, /hideAmounts \? "—"/);
  });

  it("empty states: /funds hit + no unpaid → Awaiting Estimate; miss → Add to universe", () => {
    assert.equal(
      resolveCoverageStatus({
        foundInFunds: true,
        hasEstimate: false,
        hasUpcoming: false,
      }),
      "awaiting_estimate",
    );
    assert.equal(fundPickerCoverageLabel(AGTHX), AWAITING_ESTIMATE_LABEL);
    assert.equal(
      resolveCoverageStatus({ foundInFunds: false }),
      "not_in_universe",
    );
    assert.equal(
      resolveCoverageStatus({
        coverageStatus: "awaiting_estimate",
        foundInFunds: true,
        hasEstimate: true,
      }),
      "awaiting_estimate",
      "published coverage_status wins when present — #112 Ready is not blocked on Data #114",
    );
    const picker = readFileSync(
      join(here, "../components/illustrate/FundPicker.tsx"),
      "utf8",
    );
    assert.match(picker, /exactTicker \? \(/);
    assert.match(picker, /ADD_TO_UNIVERSE/);
    assert.doesNotMatch(
      picker,
      /remotePending \? "Searching…" : "No funds match\."/,
    );
  });
});
