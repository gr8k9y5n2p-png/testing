import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(here, "SearchToolbar.tsx"), "utf8");
const dashboard = readFileSync(join(here, "Dashboard.tsx"), "utf8");

describe("Search Upcoming / Announced toolbar", () => {
  it("keeps family / category / clear and omits year", () => {
    assert.doesNotMatch(source, /type="search"/);
    assert.doesNotMatch(source, /Fund name, ticker, CUSIP/);
    assert.doesNotMatch(source, /lg:grid-cols-12|lg:col-span-6/);
    assert.match(source, /justify-start/);
    assert.match(source, /All families/);
    assert.match(source, /All categories/);
    assert.match(source, /\bClear\b/);
    assert.doesNotMatch(source, /All years/);
    assert.doesNotMatch(source, /yearOptions/);
    assert.doesNotMatch(source, /Distribution year/);
    assert.doesNotMatch(source, /filters\.year/);
    assert.match(source, /Year lives on Paid History only/);
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
    assert.match(dashboard, /mergePaidHistorySearchFunds/);
    assert.doesNotMatch(
      dashboard,
      /\[\.\.\.focusedItems, \.\.\.paidPage\.items\]/,
      "Search pick must not prepend into Paid History unfiltered",
    );
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
    assert.match(
      dashboard,
      /query\.paidHistory && query\.filters\.year/,
      "year URL param is Paid History only",
    );
    assert.match(
      dashboard,
      /year: filters.year/,
      "Upcoming Clear / family / category must keep Paid History year",
    );
    const requestFilters = dashboard.match(
      /const requestFilters = useMemo<SearchFilters>\(\s*\(\) => \(\{[\s\S]*?\}\),/,
    )?.[0];
    assert.ok(requestFilters, "Upcoming requestFilters memo");
    assert.match(requestFilters, /family: deferredFilters.family/);
    assert.match(requestFilters, /category: deferredFilters.category/);
    assert.doesNotMatch(
      requestFilters,
      /year/,
      "Upcoming page request must not include year",
    );
    const toolbar = dashboard.slice(
      dashboard.indexOf("<SearchToolbar"),
      dashboard.indexOf("<ResultsTable"),
    );
    assert.match(toolbar, /family: filters.family/);
    assert.match(toolbar, /category: filters.category/);
    assert.match(toolbar, /year: filters.year/);
    assert.doesNotMatch(toolbar, /years=\{|year=\{paidYear\}/);
  });
});
