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
});
