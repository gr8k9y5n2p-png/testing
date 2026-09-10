import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  ANNOUNCED_COLUMN,
  DIST_AMOUNT_COLUMN,
  DOLLAR_IMPACT_COLUMN,
  EMPTY_BOOK_INVITE,
  EST_DISTRIBUTION_LINE_LABEL,
  ESTIMATED_TAX_LINE_LABEL,
  EX_COLUMN,
  PCT_OF_NAV_COLUMN,
  RECORD_COLUMN,
  UPCOMING_ADD_TO_UNIVERSE,
  UPCOMING_AMOUNT_UNAVAILABLE,
  UPCOMING_AWAITING_ESTIMATE,
  upcomingDistributionAmount,
  upcomingEmptyHeadline,
  upcomingEmptyLabel,
  upcomingDistributionLine,
  upcomingDollarImpactAmount,
  upcomingEstimatedTaxLine,
  upcomingPctOfNavAmount,
  upcomingDistributionPerShareAmount,
  upcomingHolderTaxDollars,
  upcomingPctOfNavFromPerShare,
  upcomingPerShareAmount,
  UPCOMING_SOFT_DASH,
  PAID_HISTORY_DETAIL,
  PAID_HISTORY_EMPTY,
  PAID_HISTORY_HEADING,
  SINGLE_BOOK_DELTA_DETAIL,
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
    assert.equal(UPCOMING_UNAVAILABLE_HEADLINE, "Awaiting Estimate");
    assert.equal(UPCOMING_AWAITING_ESTIMATE, "Awaiting Estimate");
    assert.equal(UPCOMING_ADD_TO_UNIVERSE, "Add to universe");
    assert.doesNotMatch(UPCOMING_UNAVAILABLE_HEADLINE, /\$0|0\.00/);
    assert.doesNotMatch(UPCOMING_UNAVAILABLE_DETAIL, /\$0|0\.00/);
    assert.match(UPCOMING_UNAVAILABLE_DETAIL, /unpaid announced/i);
    assert.doesNotMatch(UPCOMING_UNAVAILABLE_HEADLINE, /undisclosed/i);
    assert.doesNotMatch(UPCOMING_UNAVAILABLE_HEADLINE, /no funds match/i);
  });

  it("uses Awaiting Estimate in-universe and Add to universe off-catalog", () => {
    assert.equal(upcomingEmptyLabel(true), "Awaiting Estimate");
    assert.equal(upcomingEmptyLabel(false), "Add to universe");
    assert.equal(upcomingEmptyHeadline([{ inUniverse: true }]), "Awaiting Estimate");
    assert.equal(
      upcomingEmptyHeadline([{ inUniverse: false }, { inUniverse: false }]),
      "Add to universe",
    );
    assert.equal(
      upcomingEmptyHeadline([{ inUniverse: true }, { inUniverse: false }]),
      "Awaiting Estimate",
    );
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
    assert.match(UPCOMING_MODULE_DETAIL, /all funds/i);
    assert.match(UPCOMING_MODULE_DETAIL, /never invent/i);
    assert.doesNotMatch(UPCOMING_MODULE_DETAIL, /\$0|0\.00/);
    assert.notEqual(UPCOMING_MODULE_HEADING, PAID_HISTORY_HEADING);
    assert.equal(UPCOMING_AMOUNT_UNAVAILABLE, "Undisclosed");
    assert.equal(UPCOMING_AWAITING_ESTIMATE, "Awaiting Estimate");
    assert.equal(UPCOMING_MODULE_HEADING, "Upcoming / Announced");
    assert.equal(DIST_AMOUNT_COLUMN, "$ Distribution / share");
    assert.equal(PCT_OF_NAV_COLUMN, "Distribution % of NAV");
    assert.equal(DOLLAR_IMPACT_COLUMN, "$ tax impact");
    assert.equal(ANNOUNCED_COLUMN, "Announced date");
    assert.equal(RECORD_COLUMN, "Record date");
    assert.equal(EX_COLUMN, "Ex-date");
    assert.equal(EST_DISTRIBUTION_LINE_LABEL, "Est. Distribution");
    assert.equal(ESTIMATED_TAX_LINE_LABEL, "Estimated Tax");
    assert.doesNotMatch(EST_DISTRIBUTION_LINE_LABEL, /\$0|0\.00/);
    assert.doesNotMatch(ESTIMATED_TAX_LINE_LABEL, /\$0|0\.00/);
    assert.equal(
      upcomingDistributionLine({ available: false, distributionDollars: null }),
      "Est. Distribution: Awaiting Estimate",
    );
    assert.equal(
      upcomingEstimatedTaxLine({
        available: false,
        covered: true,
        estimatedTax: null,
      }),
      "Estimated Tax: Awaiting Estimate",
    );
    assert.equal(
      upcomingDistributionAmount({ available: false, distributionDollars: null }),
      "Awaiting Estimate",
    );
    assert.equal(
      upcomingDistributionAmount({
        available: false,
        inUniverse: false,
        distributionDollars: null,
      }),
      "Add to universe",
    );
    assert.equal(
      upcomingPctOfNavAmount({ available: false, pctOfNav: null }),
      "Awaiting Estimate",
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
    assert.equal(
      upcomingPerShareAmount({
        available: true,
        distributionDollars: 3200,
        holdingDollars: 250_000,
        navPerShare: 41.22,
      }),
      "$0.5276 / sh",
    );
    assert.equal(
      upcomingPerShareAmount({
        available: true,
        distributionDollars: 3200,
        holdingDollars: 250_000,
        navPerShare: null,
      }),
      null,
    );
    assert.equal(
      upcomingDistributionPerShareAmount({
        available: true,
        distributionPerShare: 2.6,
        distributionDollars: null,
        holdingDollars: 10_000,
        navPerShare: 41.22,
      }),
      "$2.6000 / sh",
    );
    assert.equal(
      upcomingDistributionPerShareAmount({
        available: true,
        distributionDollars: null,
        holdingDollars: 10_000,
        navPerShare: null,
      }),
      UPCOMING_SOFT_DASH,
    );
    assert.equal(upcomingPctOfNavFromPerShare(2.6, 41.22)?.toFixed(2), "6.31");
    assert.equal(upcomingPctOfNavFromPerShare(2.6, null), null);
    assert.equal(
      upcomingHolderTaxDollars({
        distDollars: 631,
        taxRates: {
          ordinary_income: 0.37,
          long_term_capital_gains: 0.2,
          short_term_capital_gains: 0.37,
          qualified_dividend: 0.2,
          state: 0.05,
        },
        combine: true,
      }),
      631 * 0.42,
    );
    assert.equal(
      upcomingDollarImpactAmount(
        {
          available: true,
          covered: true,
          estimatedTax: null,
          distributionPerShare: 2.6,
          distributionDollars: null,
          holdingDollars: 10_000,
          navPerShare: 41.22,
        },
        {
          taxRates: {
            ordinary_income: 0.24,
            long_term_capital_gains: 0.15,
            short_term_capital_gains: 0.24,
            qualified_dividend: 0.15,
            state: 0.05,
          },
          combine: true,
        },
      ) !== upcomingDollarImpactAmount(
        {
          available: true,
          covered: true,
          estimatedTax: null,
          distributionPerShare: 2.6,
          distributionDollars: null,
          holdingDollars: 10_000,
          navPerShare: 41.22,
        },
        {
          taxRates: {
            ordinary_income: 0.37,
            long_term_capital_gains: 0.2,
            short_term_capital_gains: 0.37,
            qualified_dividend: 0.2,
            state: 0.05,
          },
          combine: true,
        },
      ),
      true,
    );
    assert.equal(
      upcomingDistributionAmount({
        available: true,
        distributionDollars: 3200,
        distributionDollarsMin: 3000,
        distributionDollarsMax: 3600,
      }),
      "$3,000–$3,600",
    );
    assert.equal(
      upcomingDistributionAmount({ available: true, distributionDollars: 0 }),
      "$0",
    );
    assert.equal(
      upcomingDistributionPerShareAmount({
        available: true,
        distributionPerShare: 0,
        distributionDollars: 0,
        holdingDollars: 10_000,
        navPerShare: 41.22,
      }),
      "$0.0000 / sh",
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

  it("does not invent a single-book delta", () => {
    assert.match(EMPTY_BOOK_INVITE, /Add holding/);
    assert.doesNotMatch(EMPTY_BOOK_INVITE, /\$0|0\.00/);
    assert.match(SINGLE_BOOK_DELTA_DETAIL, /both sides/i);
    assert.match(SINGLE_BOOK_DELTA_DETAIL, /not Upcoming/i);
    assert.doesNotMatch(SINGLE_BOOK_DELTA_DETAIL, /\$0|0\.00/);
    assert.notEqual(SINGLE_BOOK_DELTA_DETAIL, TAX_IMPACT_DELTA_DETAIL);
    assert.notEqual(EMPTY_BOOK_INVITE, UPCOMING_UNAVAILABLE_HEADLINE);
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
