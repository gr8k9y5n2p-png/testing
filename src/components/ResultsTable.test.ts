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

describe("ResultsTable Announced sort and Paid history year", () => {
  it("sorts Announced by asOfDate and always client-sorts Paid history", () => {
    assert.match(source, /column="asOfDate"/);
    assert.match(source, /announcedSortKey/);
    assert.match(source, /sortFunds\(paid,/);
    assert.match(source, /sortFunds\(upcoming,/);
    assert.doesNotMatch(source, /serverSorted \? paid/);
    const announcedHeader = source.slice(
      source.indexOf('label="Announced"'),
      source.indexOf('label="Announced"') + 180,
    );
    assert.match(announcedHeader, /column="asOfDate"/);
    assert.doesNotMatch(announcedHeader, /column="publishedAt"/);
  });

  it("owns a Paid history calendar-year toggle", () => {
    assert.match(source, /Paid history calendar year/);
    assert.match(source, /paidHistoryViews\(funds, paidYear\)/);
    assert.match(source, /paidHistoryEmptyForYear/);
    assert.match(source, /PaidHistoryYearToggle/);
  });
});

describe("ResultsTable Search pager placement", () => {
  it("puts the hybrid pager directly below Upcoming / announced, not above it", () => {
    const start = source.indexOf("return (");
    const layout = source.slice(start, source.indexOf("function FundSection"));
    const upcoming = layout.indexOf('title="Upcoming / announced"');
    const pager = layout.indexOf("<PaginationBar");
    const paid = layout.indexOf('title="Paid history"');
    assert.ok(upcoming >= 0, "Upcoming / announced section");
    assert.ok(pager >= 0, "hybrid PaginationBar");
    assert.ok(paid >= 0, "Paid history section");
    assert.ok(
      upcoming < pager && pager < paid,
      "pager must sit between Upcoming / announced and Paid history",
    );
    assert.equal(
      layout.indexOf("<PaginationBar"),
      pager,
      "first pager is the one under Upcoming",
    );
  });
});
