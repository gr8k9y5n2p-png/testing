import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(here, "ResultsTable.tsx"), "utf8");

describe("ResultsTable Search ticker clicks", () => {
  it("selects ticker/name into Search a fund instead of routing to Compare", () => {
    assert.match(source, /SearchTickerButton/);
    assert.match(source, /onSelect=\{onIllustrate\}/);
    assert.doesNotMatch(source, /CompareTickerLink|compareTickersPath|\/compare\?tickers=/);
  });
});

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
  it("puts the hybrid pager inside each FundSection card, not as a strip between modules", () => {
    const start = source.indexOf("return (");
    const layout = source.slice(start, source.indexOf("function FundSection"));
    const upcoming = layout.indexOf('title="Upcoming / Announced"');
    const paid = layout.indexOf('title="Paid history"');
    assert.ok(upcoming >= 0, "Upcoming / Announced section");
    assert.ok(paid >= 0, "Paid history section");
    assert.doesNotMatch(layout, /<PaginationBar/, "no inter-module pager strip");
    assert.match(layout, /page=\{page\}/);
    assert.equal(
      (layout.match(/page=\{page\}/g) ?? []).length,
      2,
      "Upcoming and Paid history both receive the same hybrid page controls",
    );

    const fundSection = source.slice(
      source.indexOf("function FundSection"),
      source.indexOf("function EstimateRow"),
    );
    assert.match(fundSection, /<PaginationBar/);
    assert.match(fundSection, /VirtualizedTable/);
    const tableCard = fundSection.indexOf("md:block");
    const desktopPager = fundSection.indexOf("<PaginationBar", tableCard);
    const mobileCards = fundSection.indexOf("md:hidden");
    assert.ok(tableCard >= 0 && desktopPager >= 0 && mobileCards >= 0);
    assert.ok(
      tableCard < desktopPager && desktopPager < mobileCards,
      "desktop pager sits in the table card chrome, before the mobile list",
    );
  });

  it("keeps PaginationBar compact table chrome, not a chunky standalone strip", () => {
    const start = source.indexOf("function PaginationBar");
    const pager = source.slice(start, source.indexOf("function VirtualizedTable"));
    assert.match(pager, /border-t border-line/);
    assert.match(pager, /h-6 /);
    assert.match(pager, /text-\[11px\]/);
    assert.doesNotMatch(pager, /rounded-lg border border-line bg-surface/);
    assert.doesNotMatch(pager, /h-9 /);
    assert.doesNotMatch(pager, /py-2\.5/);
  });
});
