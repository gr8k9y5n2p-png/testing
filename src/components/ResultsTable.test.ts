import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(here, "ResultsTable.tsx"), "utf8");

describe("ResultsTable EstimateRow props", () => {
  it("does not pass showPayable into EstimateRow (Vercel typecheck)", () => {
    const start = source.indexOf("<EstimateRow");
    const estimateCall = source.slice(start, source.indexOf("/>", start) + 2);
    assert.match(estimateCall, /<EstimateRow/);
    assert.doesNotMatch(estimateCall, /showPayable=/);
    const props = source.slice(
      source.indexOf("function EstimateRow"),
      source.indexOf("function onRowClick"),
    );
    assert.doesNotMatch(props, /showPayable/);
  });
});

describe("ResultsTable Search pager placement", () => {
  it("puts the hybrid pager directly below Upcoming / Announced, not above it", () => {
    const start = source.indexOf("return (");
    const layout = source.slice(start, source.indexOf("function FundSection"));
    const upcoming = layout.indexOf('title="Upcoming / Announced"');
    const pager = layout.indexOf("<PaginationBar");
    const paid = layout.indexOf('title="Paid history"');
    assert.ok(upcoming >= 0, "Upcoming / Announced section");
    assert.ok(pager >= 0, "hybrid PaginationBar");
    assert.ok(paid >= 0, "Paid history section");
    assert.ok(
      upcoming < pager && pager < paid,
      "pager must sit between Upcoming / Announced and Paid history",
    );
    assert.equal(
      layout.indexOf("<PaginationBar"),
      pager,
      "first pager is the one under Upcoming",
    );
  });
});
