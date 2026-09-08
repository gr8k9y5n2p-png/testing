import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  smokeCurrentHoldings,
  smokeProposedHoldings,
} from "./portfolio-compare-catalog.ts";
import { mockPortfolioCompareResponse } from "./portfolio-compare-fixture.ts";
import { PORTFOLIO_COMPARE_BOOK_DOLLARS } from "./portfolio-compare-types.ts";

function toApiHoldings(
  holdings: ReturnType<typeof smokeCurrentHoldings>,
) {
  return holdings.map((holding) => ({
    ticker: holding.ticker,
    fund_identifier: holding.ticker,
    fund_name: holding.fundName,
    fund_family: holding.family,
    weight_pct: holding.weightPct,
  }));
}

describe("PortfolioCompare smoke fixture", () => {
  it("covers every default holding on both sides", () => {
    const current = smokeCurrentHoldings();
    const proposed = smokeProposedHoldings();
    const result = mockPortfolioCompareResponse({
      current: {
        label: "Current Allocation",
        book_dollars: PORTFOLIO_COMPARE_BOOK_DOLLARS,
        holdings: toApiHoldings(current),
      },
      proposed: {
        label: "Proposed Allocation",
        book_dollars: PORTFOLIO_COMPARE_BOOK_DOLLARS,
        holdings: toApiHoldings(proposed),
      },
    });

    assert.equal(result.current.coverage.holdings_uncovered, 0);
    assert.equal(result.proposed.coverage.holdings_uncovered, 0);
    assert.equal(result.current.coverage.coverage_pct, 100);
    assert.equal(result.proposed.coverage.coverage_pct, 100);
    assert.deepEqual(
      result.current.holdings.map((holding) => holding.ticker),
      current.map((holding) => holding.ticker),
    );
    assert.deepEqual(
      result.proposed.holdings.map((holding) => holding.ticker),
      proposed.map((holding) => holding.ticker),
    );
  });
});
