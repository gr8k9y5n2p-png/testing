import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

describe("Search / Sample Estimates fund page", () => {
  it("hydrates unique /funds rows from /distributions and does not seed", () => {
    const source = readFileSync(join(here, "funds-page.ts"), "utf8");
    assert.match(source, /hydrateFundPage/);
    assert.match(source, /loadDistributionsForFundPage/);
    assert.match(source, /mergeFundWithDistributions/);
    assert.match(source, /has_estimate/);
    assert.doesNotMatch(source, /SAMPLE_FUNDS|from ["']@\/data\/seed["']/);
  });

  it("hydrates a browse page prefix instead of skipping all ticker GETs", () => {
    const source = readFileSync(join(here, "distributions.ts"), "utf8");
    assert.match(source, /missingTickers\.slice\(0, 8\)/);
    assert.doesNotMatch(
      source,
      /Boolean\(q\) \|\| missingTickers\.length <= 8/,
    );
  });

  it("passes as_of_from / as_of_to year bounds to GET /distributions", () => {
    const distributions = readFileSync(join(here, "distributions.ts"), "utf8");
    const page = readFileSync(join(here, "funds-page.ts"), "utf8");
    assert.match(distributions, /as_of_from/);
    assert.match(distributions, /as_of_to/);
    assert.match(page, /asOfYearBounds/);
    assert.match(page, /asOfFrom/);
    assert.match(page, /asOfTo/);
    assert.match(page, /paidYear/);
  });

  it("keeps paid/final history off the has_estimate Upcoming gate", () => {
    const table = readFileSync(
      join(here, "../../components/ResultsTable.tsx"),
      "utf8",
    );
    const badge = readFileSync(
      join(here, "../../components/DeltaBadge.tsx"),
      "utf8",
    );
    assert.match(table, /hideUpcomingAmounts/);
    assert.match(table, /paidEventsForFund/);
    assert.doesNotMatch(table, /hasEstimate === false \? "—"/);
    assert.match(badge, /hideUpcomingAmounts/);
  });

  it("Dollar Illustration Upcoming stays unpaid prelim only — never result.totals", () => {
    const results = readFileSync(
      join(here, "../../components/illustrate/IllustrationResults.tsx"),
      "utf8",
    );
    const bucket = readFileSync(
      join(here, "../../data/distribution-bucket.ts"),
      "utf8",
    );
    assert.match(results, /upcomingIllustrationTotals/);
    assert.match(results, /splitIllustrationComponents/);
    assert.doesNotMatch(results, /totals\.distribution_dollars/);
    assert.match(bucket, /every fund \(not ticker-specific\)/);
    assert.match(bucket, /`final` and `paid` are Paid history/);
    assert.doesNotMatch(bucket, /ABALX|AMCPX|ticker ===/);
  });
});
