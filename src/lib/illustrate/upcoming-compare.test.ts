import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import type { ComparePeriodOut, CompareUpcomingDistribution } from "./compare-types.ts";
import {
  gateCompareUpcoming,
  sideIsAnnounced,
  toUpcomingSummary,
} from "./upcoming-compare.ts";

const here = dirname(fileURLToPath(import.meta.url));

function period(year: number, leftTax: number | null, rightTax: number | null): ComparePeriodOut {
  return {
    year,
    left: {
      label: "AMCPX",
      matched: leftTax != null,
      totals: { estimated_tax: leftTax, estimated_tax_dollars: leftTax },
    },
    right: {
      label: "AGTHX",
      matched: rightTax != null,
      totals: { estimated_tax: rightTax, estimated_tax_dollars: rightTax },
    },
    deltas: {
      distribution_dollars: 0,
      estimated_tax: 0,
      effective_tax_on_holding: 0,
    },
  };
}

const unpaid: CompareUpcomingDistribution = {
  left_dollars: 185,
  right_dollars: 100,
  delta_dollars: -85,
  left_publication_stage: "updated_estimate",
  right_publication_stage: "preliminary_estimate",
};

describe("unpaid-only Upcoming gate", () => {
  it("does not treat dollars without an unpaid stage as announced", () => {
    assert.equal(sideIsAnnounced(522, null), false);
    assert.equal(sideIsAnnounced(522, "paid"), false);
    assert.equal(sideIsAnnounced(522, "final"), false);
    assert.equal(sideIsAnnounced(522, "preliminary_estimate"), true);
  });

  it("drops invented annual-tax upcoming even when staged as prelim", () => {
    const invented: CompareUpcomingDistribution = {
      left_dollars: 214,
      right_dollars: 214,
      delta_dollars: 0,
      left_publication_stage: "preliminary_estimate",
      right_publication_stage: "preliminary_estimate",
    };
    const periods = [period(2025, 214, 290)];
    assert.equal(gateCompareUpcoming(invented, periods), null);
    assert.equal(toUpcomingSummary(invented, "left", periods), null);
  });

  it("hides a $522 badge when Data sent dollars with no unpaid announce", () => {
    const invented: CompareUpcomingDistribution = {
      left_dollars: 522,
      right_dollars: 522,
      delta_dollars: 0,
      left_publication_stage: null,
      right_publication_stage: null,
    };
    assert.equal(gateCompareUpcoming(invented), null);
    assert.equal(toUpcomingSummary(invented, "left"), null);
  });

  it("keeps a real unpaid announced upcoming that is not a period copy", () => {
    const periods = [period(2025, 214, 290)];
    const gated = gateCompareUpcoming(unpaid, periods);
    assert.equal(gated?.left_dollars, 185);
    assert.equal(gated?.right_dollars, 100);
    const summary = toUpcomingSummary(unpaid, "left", periods);
    assert.equal(summary?.announced, true);
    assert.equal(summary?.dollars, 185);
    assert.match(summary?.label ?? "", /Upcoming/);
    assert.doesNotMatch(summary?.label ?? "", /522/);
  });

  it("treats explicit null upcoming as undisclosed", () => {
    assert.equal(gateCompareUpcoming(null), null);
    assert.equal(toUpcomingSummary(null), null);
  });

  it("does not invent YoY upcoming from the latest calendar-year tax", () => {
    const fixture = readFileSync(join(here, "compare-fixture.ts"), "utf8");
    const yoy = fixture.split("function mockYoyResponse")[1]?.split(
      "export function mockCompareResponse",
    )[0];
    assert.ok(yoy);
    assert.match(yoy, /upcoming_taxable_distribution:\s*null/);
    assert.doesNotMatch(yoy, /left_dollars:\s*latestTax/);
  });
});
