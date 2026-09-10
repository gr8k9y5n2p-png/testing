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
  it("passes showPayable into EstimateRow for the payable date column", () => {
    const start = source.indexOf("<EstimateRow");
    const estimateCall = source.slice(start, source.indexOf("/>", start) + 2);
    assert.match(estimateCall, /<EstimateRow/);
    assert.match(estimateCall, /showPayable=\{showPayable\}/);
    const props = source.slice(
      source.indexOf("function EstimateRow"),
      source.indexOf("function onRowClick"),
    );
    assert.match(props, /showPayable: boolean/);
  });
});

describe("ResultsTable Search Paid history", () => {
  it("keeps Upcoming / Announced and mounts Paid history from /distributions", () => {
    assert.match(source, /title=\{SEARCH_UPCOMING_HEADING\}/);
    assert.match(source, /title=\{SEARCH_PAID_HISTORY_HEADING\}/);
    assert.match(source, /UPCOMING_UNAVAILABLE_HEADLINE/);
    assert.match(source, /UPCOMING_UNAVAILABLE_DETAIL/);
    assert.match(source, /paidHistoryViews/);
    assert.match(source, /PAID_HISTORY_EMPTY/);
    assert.match(source, /Dist \$\/sh/);
    assert.match(source, /% NAV/);
    assert.match(source, /Aftertax % of NAV/);
    assert.match(source, /estimatePct\(fund\)/);
    assert.doesNotMatch(source, /Ordinary income/);
    assert.doesNotMatch(source, /Capital gains/);
    assert.doesNotMatch(source, /estimatedCapitalGains/);
    assert.doesNotMatch(source, /estimatedOrdinaryIncome/);
  });

  it("renders a visible Paid History module header, not only the kicker chip", () => {
    const paidCall = source.slice(
      source.indexOf("title={SEARCH_PAID_HISTORY_HEADING}"),
      source.indexOf("function FundSection"),
    );
    assert.match(paidCall, /showHeading/);
    const fundSection = source.slice(
      source.indexOf("function FundSection"),
      source.indexOf("function EstimateRow"),
    );
    assert.match(fundSection, /<h3 className="font-serif text-xl tracking-tight text-ink">\{title\}<\/h3>/);
    assert.match(fundSection, /\{description\}/);
    assert.match(fundSection, /showHeading \? \(/);
    assert.match(fundSection, /Paid History year/);
    assert.match(fundSection, /Paid History filters/);
    assert.match(fundSection, /All families/);
    assert.match(fundSection, /All categories/);
    assert.match(fundSection, /Paid History family/);
    assert.match(fundSection, /Paid History category/);
  });
});

describe("ResultsTable Search pager placement", () => {
  it("puts the hybrid pager inside each FundSection card, not as a strip between modules", () => {
    const start = source.indexOf("return (");
    const layout = source.slice(start, source.indexOf("function FundSection"));
    const upcoming = layout.indexOf("title={SEARCH_UPCOMING_HEADING}");
    const paid = layout.indexOf("title={SEARCH_PAID_HISTORY_HEADING}");
    assert.ok(upcoming >= 0, "Upcoming / Announced section");
    assert.ok(paid > upcoming, "Paid history mounts below Upcoming");
    assert.doesNotMatch(layout, /<PaginationBar/, "no inter-module pager strip");
    assert.match(layout, /page=\{page\}/);
    assert.match(layout, /page=\{paidPage\}/);
    assert.equal(
      (layout.match(/page=\{page\}/g) ?? []).length,
      1,
      "Upcoming receives the hybrid page controls",
    );
    assert.equal(
      (layout.match(/page=\{paidPage\}/g) ?? []).length,
      1,
      "Paid History receives its own year-book pager",
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
    assert.match(pager, /Funds per page/);
    assert.match(pager, /onLimit/);
  });
});
