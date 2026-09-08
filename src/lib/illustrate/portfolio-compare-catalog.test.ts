import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  PORTFOLIO_TICKER_RATES,
  SMOKE_CURRENT_TICKERS,
  SMOKE_PROPOSED_TICKERS,
  SMOKE_WEIGHT_PCT,
  smokeCurrentHoldings,
  smokeProposedHoldings,
} from "./portfolio-compare-catalog.ts";
import { PORTFOLIO_COMPARE_BOOK_DOLLARS } from "./portfolio-compare-types.ts";

const HISTORY_COVERED_CURRENT = ["AGTHX", "DODIX", "AMCAP", "DODGX"] as const;
const HISTORY_COVERED_PROPOSED = ["AMCPX", "CGHM", "AGTHX", "AMCAP"] as const;
const GAP_HEROES = ["VFIAX", "VBIAX", "TRBCX", "FBGRX", "VIGAX"] as const;

describe("PortfolioCompare smoke books", () => {
  it("defaults Current to GTM history-covered tickers at 25% each", () => {
    assert.deepEqual([...SMOKE_CURRENT_TICKERS], [...HISTORY_COVERED_CURRENT]);
    assert.equal(SMOKE_WEIGHT_PCT, 25);

    const holdings = smokeCurrentHoldings();
    assert.deepEqual(
      holdings.map((holding) => holding.ticker),
      [...HISTORY_COVERED_CURRENT],
    );
    assert.ok(holdings.every((holding) => holding.weightPct === 25));
    assert.equal(
      holdings.reduce((sum, holding) => sum + holding.weightPct, 0),
      100,
    );
    assert.ok(
      holdings.every(
        (holding) =>
          holding.holdingDollars === 0.25 * PORTFOLIO_COMPARE_BOOK_DOLLARS,
      ),
    );
  });

  it("defaults Proposed to GTM history-covered tickers at 25% each", () => {
    assert.deepEqual([...SMOKE_PROPOSED_TICKERS], [...HISTORY_COVERED_PROPOSED]);

    const holdings = smokeProposedHoldings();
    assert.deepEqual(
      holdings.map((holding) => holding.ticker),
      [...HISTORY_COVERED_PROPOSED],
    );
    assert.ok(holdings.every((holding) => holding.weightPct === 25));
    assert.equal(
      holdings.reduce((sum, holding) => sum + holding.weightPct, 0),
      100,
    );
  });

  it("keeps dollars derived from weight × book value when the book changes", () => {
    const book = 2_000_000;
    const current = smokeCurrentHoldings(book);
    const proposed = smokeProposedHoldings(book);
    for (const holding of [...current, ...proposed]) {
      assert.equal(holding.holdingDollars, (holding.weightPct / 100) * book);
      assert.equal(holding.holdingDollars, 500_000);
    }
  });

  it("does not seed the Render coverage-gap heroes as smoke defaults", () => {
    const smoke = new Set([...SMOKE_CURRENT_TICKERS, ...SMOKE_PROPOSED_TICKERS]);
    for (const ticker of GAP_HEROES) {
      assert.equal(smoke.has(ticker), false, `${ticker} should not be a smoke default`);
    }
  });

  it("includes DODGX in the localhost fixture catalog", () => {
    assert.equal(PORTFOLIO_TICKER_RATES.DODGX?.fundName, "Dodge & Cox Stock Fund");
    assert.equal(PORTFOLIO_TICKER_RATES.DODGX?.family, "Dodge & Cox");
  });
});
