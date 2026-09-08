import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  PAID_HISTORY_EMPTY,
  TAX_DRAG_CARD_DETAIL,
  TAX_IMPACT_DELTA_DETAIL,
  UPCOMING_UNAVAILABLE_DETAIL,
  UPCOMING_UNAVAILABLE_HEADLINE,
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
    assert.notEqual(PAID_HISTORY_EMPTY, UPCOMING_UNAVAILABLE_HEADLINE);
    assert.notEqual(PAID_HISTORY_EMPTY, UPCOMING_UNAVAILABLE_DETAIL);
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
