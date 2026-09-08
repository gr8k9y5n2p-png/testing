import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

describe("paid_history contract wiring", () => {
  it("normalizes holdings[].paid_history on portfolio compare", () => {
    const client = readFileSync(join(here, "portfolio-compare-client.ts"), "utf8");
    assert.match(client, /paid_history:/);
    assert.match(client, /normalizeUpcoming\(row\.paid_history\)/);
    assert.match(
      client,
      /Object\.prototype\.hasOwnProperty\.call\(row, "paid_history"\)/,
    );
  });

  it("ships additive paid_history on the mock fixture", () => {
    const fixture = readFileSync(join(here, "portfolio-compare-fixture.ts"), "utf8");
    assert.match(fixture, /paid_history: paidHistory/);
    assert.match(fixture, /publication_stage: "paid"/);
  });

  it("keeps the dedicated field on the holding type", () => {
    const types = readFileSync(join(here, "portfolio-compare-types.ts"), "utf8");
    assert.match(types, /paid_history\?:/);
    assert.match(types, /PortfolioPaidHistory/);
    assert.doesNotMatch(types, /Temporary Paid History fallback/);
  });

  it("does not fall back to illustration.components for Paid History", () => {
    const stage = readFileSync(join(here, "publication-stage.ts"), "utf8");
    const fn = stage.split("function paidHistoryEventsFromHolding")[1]?.split(
      "const STAGE_LABELS",
    )[0];
    assert.ok(fn);
    assert.match(fn, /holding\.paid_history/);
    assert.doesNotMatch(fn, /holding\.illustration/);
    assert.doesNotMatch(fn, /holding\.distributions/);
  });
});

describe("portfolio compare periods wiring", () => {
  it("POSTs periods 2021–2025 on portfolio compare", () => {
    const client = readFileSync(join(here, "portfolio-compare-client.ts"), "utf8");
    assert.match(client, /periods:/);
    assert.match(client, /ensurePortfolioComparePeriods/);
    assert.match(client, /normalizePortfolioComparePeriods/);
    assert.match(client, /portfolioPeriodTaxIsUnmatched/);
  });

  it("keeps Upcoming as its own module and does not mount Paid History", () => {
    const compare = readFileSync(
      join(here, "../../components/illustrate/PortfolioCompare.tsx"),
      "utf8",
    );
    const table = readFileSync(
      join(here, "../../components/illustrate/portfolio-compare/UpcomingTable.tsx"),
      "utf8",
    );
    assert.match(compare, /upcomingHoldingsForSide/);
    assert.match(compare, /<UpcomingTable/);
    assert.doesNotMatch(compare, /PaidHistoryTable/);
    assert.doesNotMatch(compare, /paidHistoryRowsForSide/);
    assert.match(table, /UPCOMING_MODULE_DETAIL/);
    assert.match(table, /upcomingDistributionLine/);
    assert.match(table, /upcomingEstimatedTaxLine/);
    assert.doesNotMatch(table, /Est\. dist \$/);
    assert.doesNotMatch(table, /export function PaidHistoryTable/);
    assert.doesNotMatch(table, /Paid history/);
    assert.doesNotMatch(table, /ticker×year matrix is Website/);
    assert.doesNotMatch(table, /Website owns converting/);
  });

  it("does not mount the duplicate Total tax impact / upcoming-tax-to-holder cards", () => {
    const compare = readFileSync(
      join(here, "../../components/illustrate/PortfolioCompare.tsx"),
      "utf8",
    );
    assert.match(compare, /<UpcomingTable/);
    assert.match(compare, /<CalendarYearTaxTable/);
    assert.doesNotMatch(compare, /TaxImpactChart/);
    assert.doesNotMatch(compare, /taxImpactBarsForSide/);
    assert.doesNotMatch(compare, /Upcoming tax to holder/);
    assert.doesNotMatch(compare, /tax-impact-current/);
    assert.doesNotMatch(compare, /tax-impact-proposed/);
  });

  it("keeps CalendarYearTaxTable as the existing matrix, not a Paid History rebuild", () => {
    const compare = readFileSync(
      join(here, "../../components/illustrate/PortfolioCompare.tsx"),
      "utf8",
    );
    const yearTable = readFileSync(
      join(here, "../../components/illustrate/portfolio-compare/CalendarYearTaxTable.tsx"),
      "utf8",
    );
    assert.match(compare, /<CalendarYearTaxTable/);
    assert.doesNotMatch(compare, /PaidHistoryTable/);
    assert.match(yearTable, /YEAR_TAX_HEADING/);
    assert.match(yearTable, /Website keeps\/enhances/);
    const exportSrc = readFileSync(join(here, "portfolio-compare-export.ts"), "utf8");
    assert.doesNotMatch(exportSrc, /<h3>Paid history<\/h3>/);
    assert.doesNotMatch(exportSrc, /paidHistoryRowsForSide/);
  });

  it("mocks calendar-year tax per ticker", () => {
    const fixture = readFileSync(join(here, "portfolio-compare-fixture.ts"), "utf8");
    assert.match(fixture, /mockCalendarYearPeriods/);
    assert.match(fixture, /portfolioYearTaxRate/);
  });
});

describe("portfolio compare nav_per_share wiring", () => {
  it("enriches holdings from search/seed NAV and never sends 0", () => {
    const client = readFileSync(join(here, "portfolio-compare-client.ts"), "utf8");
    const seed = readFileSync(join(here, "seed-nav.ts"), "utf8");
    const compare = readFileSync(
      join(here, "../../components/illustrate/PortfolioCompare.tsx"),
      "utf8",
    );
    assert.match(client, /withPortfolioHoldingNav/);
    assert.match(client, /seedNavLookup/);
    assert.match(client, /positiveNav\(holding\.nav_per_share\)/);
    assert.match(compare, /navFromFundMetadata\(ticker, holding\.nav, seedNavLookup\)/);
    assert.match(seed, /DODIX:\s*12\.8/);
    assert.match(seed, /DODGX:\s*273\.16/);
    assert.match(seed, /CGHM:\s*25\.18/);
    assert.match(seed, /AMCAP:\s*"AMCPX"/);
    assert.doesNotMatch(seed, /DODIX:\s*0\b/);
  });
});
