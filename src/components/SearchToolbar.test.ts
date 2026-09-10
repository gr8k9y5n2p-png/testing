import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(here, "SearchToolbar.tsx"), "utf8");
const dashboard = readFileSync(join(here, "Dashboard.tsx"), "utf8");

describe("Search Upcoming / Announced toolbar", () => {
  it("removes the text search box and left-aligns family / category / year", () => {
    assert.doesNotMatch(source, /type="search"/);
    assert.doesNotMatch(source, /Fund name, ticker, CUSIP/);
    assert.doesNotMatch(source, /lg:grid-cols-12|lg:col-span-6/);
    assert.match(source, /justify-start/);
    assert.match(source, /All families/);
    assert.match(source, /All categories/);
    assert.match(source, /All years/);
    assert.match(source, /yearOptions\.map/);
  });
});

describe("Search Upcoming / Announced module chrome", () => {
  it("uses locked Upcoming / Announced title and unpaid-only subtitle", () => {
    assert.match(dashboard, /SEARCH_UPCOMING_HEADING/);
    assert.match(dashboard, /SEARCH_UPCOMING_DETAIL/);
    assert.doesNotMatch(dashboard, /Sample estimates/);
    assert.doesNotMatch(dashboard, /Filter by name, ticker, CUSIP/);
    assert.doesNotMatch(dashboard, /type="search"/);
    assert.match(dashboard, /params.set\("q"/);
    assert.match(dashboard, /scopedTicker/);
    assert.match(dashboard, /buildSearchTableFunds/);
    assert.match(dashboard, /currentPaidHistoryYear/);
    assert.match(dashboard, /mergeTaxYears/);
    assert.match(dashboard, /FUND_PAGE_SIZE/);
    assert.match(dashboard, /paid_history/);
    assert.match(dashboard, /PAID_HISTORY_PAGE_SIZE/);
    assert.match(dashboard, /PAID_HISTORY_PAGE_SIZES/);
    assert.match(dashboard, /paidFunds/);
    assert.match(dashboard, /paidFacets/);
    assert.match(dashboard, /onPaidFamily/);
    assert.match(dashboard, /onPaidCategory/);
    assert.match(dashboard, /setPaidOffset\(0\)/);
    assert.match(
      dashboard,
      /onPaidFamily=\{\(family\) => applyFilters\(\{ \.\.\.filters, family \}\)\}/,
    );
    assert.match(
      dashboard,
      /onPaidCategory=\{\(category\) => applyFilters\(\{ \.\.\.filters, category \}\)\}/,
    );
    const apply = dashboard.slice(
      dashboard.indexOf("function applyFilters"),
      dashboard.indexOf("function applyPaidLimit"),
    );
    assert.match(apply, /setPaidOffset\(0\)/);
    assert.match(apply, /setOffset\(0\)/);
    assert.match(dashboard, /<ResultsTable/);
    assert.doesNotMatch(
      dashboard,
      /EmptyState/,
      "Paid History must stay mounted when Upcoming is empty",
    );
    assert.doesNotMatch(
      dashboard,
      /query: scopedTicker,/,
      "selected ticker must not replace the Upcoming universe query",
    );
  });
});
