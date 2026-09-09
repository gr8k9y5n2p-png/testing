import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  ANNOUNCED_COLUMN,
  DIST_AMOUNT_COLUMN,
  DOLLAR_IMPACT_COLUMN,
  EST_DISTRIBUTION_LINE_LABEL,
  ESTIMATED_TAX_LINE_LABEL,
  EX_COLUMN,
  PCT_OF_NAV_COLUMN,
  RECORD_COLUMN,
  UPCOMING_AMOUNT_UNAVAILABLE,
  upcomingDistributionAmount,
  upcomingDistributionLine,
  upcomingDollarImpactAmount,
  upcomingEstimatedTaxLine,
  upcomingPctOfNavAmount,
  PAID_HISTORY_DETAIL,
  PAID_HISTORY_EMPTY,
  PAID_HISTORY_HEADING,
  TAX_DRAG_CARD_DETAIL,
  TAX_IMPACT_DELTA_DETAIL,
  UPCOMING_MODULE_DETAIL,
  UPCOMING_MODULE_HEADING,
  UPCOMING_UNAVAILABLE_DETAIL,
  UPCOMING_UNAVAILABLE_HEADLINE,
  YEAR_TAX_DETAIL,
  YEAR_TAX_EMPTY,
  YEAR_TAX_HEADING,
} from "./portfolio-compare-copy.ts";

describe("PortfolioCompare empty upcoming copy", () => {
  it("does not look like a $0 estimate", () => {
    assert.match(UPCOMING_UNAVAILABLE_HEADLINE, /not available/i);
    assert.match(UPCOMING_UNAVAILABLE_HEADLINE, /undisclosed/i);
    assert.doesNotMatch(UPCOMING_UNAVAILABLE_HEADLINE, /\$0|0\.00/);
    assert.doesNotMatch(UPCOMING_UNAVAILABLE_DETAIL, /\$0|0\.00/);
    assert.match(UPCOMING_UNAVAILABLE_DETAIL, /unpaid announced/i);
  });

  it("keeps paid-history empty copy distinct from upcoming", () => {
    assert.match(PAID_HISTORY_EMPTY, /paid/i);
    assert.match(PAID_HISTORY_HEADING, /paid history/i);
    assert.match(PAID_HISTORY_DETAIL, /not upcoming/i);
    assert.notEqual(PAID_HISTORY_EMPTY, UPCOMING_UNAVAILABLE_HEADLINE);
    assert.notEqual(PAID_HISTORY_EMPTY, UPCOMING_UNAVAILABLE_DETAIL);
  });
});

describe("PortfolioCompare upcoming module copy", () => {
  it("labels sell-before-record Upcoming without looking like $0", () => {
    assert.match(UPCOMING_MODULE_HEADING, /upcoming/i);
    assert.match(UPCOMING_MODULE_DETAIL, /sell before record/i);
    assert.doesNotMatch(UPCOMING_MODULE_DETAIL, /\$0|0\.00/);
    assert.notEqual(UPCOMING_MODULE_HEADING, PAID_HISTORY_HEADING);
    assert.equal(UPCOMING_AMOUNT_UNAVAILABLE, "Undisclosed");
    assert.equal(DIST_AMOUNT_COLUMN, "Dist $");
    assert.equal(PCT_OF_NAV_COLUMN, "% of NAV");
    assert.equal(DOLLAR_IMPACT_COLUMN, "$ impact");
    assert.equal(ANNOUNCED_COLUMN, "Announced");
    assert.equal(RECORD_COLUMN, "Record");
    assert.equal(EX_COLUMN, "Ex");
    assert.equal(EST_DISTRIBUTION_LINE_LABEL, "Est. Distribution");
    assert.equal(ESTIMATED_TAX_LINE_LABEL, "Estimated Tax");
    assert.doesNotMatch(EST_DISTRIBUTION_LINE_LABEL, /\$0|0\.00/);
    assert.doesNotMatch(ESTIMATED_TAX_LINE_LABEL, /\$0|0\.00/);
    assert.equal(
      upcomingDistributionLine({ available: false, distributionDollars: null }),
      "Est. Distribution: Undisclosed",
    );
    assert.equal(
      upcomingEstimatedTaxLine({
        available: false,
        covered: true,
        estimatedTax: null,
      }),
      "Estimated Tax: N/A",
    );
    assert.equal(
      upcomingDistributionAmount({ available: false, distributionDollars: null }),
      "Undisclosed",
    );
    assert.equal(
      upcomingPctOfNavAmount({ available: false, pctOfNav: null }),
      "Undisclosed",
    );
    assert.equal(
      upcomingPctOfNavAmount({ available: true, pctOfNav: 1.28 }),
      "1.28%",
    );
    assert.equal(
      upcomingDollarImpactAmount({
        available: true,
        covered: true,
        estimatedTax: 1120,
      }),
      "$1,120",
    );
    assert.doesNotMatch(
      upcomingPctOfNavAmount({ available: false, pctOfNav: null }),
      /\$0|0\.00/,
    );
  });
});

describe("PortfolioCompare tax drag copy", () => {
  it("keeps tax drag cards independent of empty Upcoming", () => {
    assert.match(TAX_DRAG_CARD_DETAIL, /compare totals/i);
    assert.match(TAX_DRAG_CARD_DETAIL, /not Upcoming/i);
    assert.match(TAX_IMPACT_DELTA_DETAIL, /proposed/i);
    assert.match(TAX_IMPACT_DELTA_DETAIL, /current/i);
    assert.match(TAX_IMPACT_DELTA_DETAIL, /not Upcoming/i);
    assert.notEqual(TAX_DRAG_CARD_DETAIL, UPCOMING_UNAVAILABLE_HEADLINE);
    assert.notEqual(TAX_IMPACT_DELTA_DETAIL, PAID_HISTORY_EMPTY);
  });
});

describe("PortfolioCompare calendar-year tax copy", () => {
  it("stays visually and verbally distinct from Upcoming", () => {
    assert.match(YEAR_TAX_HEADING, /calendar-year tax/i);
    assert.match(YEAR_TAX_DETAIL, /2025–2021/);
    assert.match(YEAR_TAX_DETAIL, /not Upcoming/);
    assert.doesNotMatch(YEAR_TAX_DETAIL, /Paid history/i);
    assert.notEqual(YEAR_TAX_HEADING, UPCOMING_UNAVAILABLE_HEADLINE);
    assert.notEqual(YEAR_TAX_EMPTY, PAID_HISTORY_EMPTY);
    assert.notEqual(YEAR_TAX_DETAIL, TAX_DRAG_CARD_DETAIL);
  });
});
