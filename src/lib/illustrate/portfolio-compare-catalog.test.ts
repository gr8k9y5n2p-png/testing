import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  SMOKE_CURRENT_TICKERS,
  SMOKE_PROPOSED_TICKERS,
  SMOKE_WEIGHT_PCT,
} from "./portfolio-compare-smoke.ts";

const HISTORY_COVERED_CURRENT = ["AGTHX", "DODIX", "AMCAP", "DODGX"] as const;
const HISTORY_COVERED_PROPOSED = ["AMCPX", "CGHM", "AGTHX", "AMCAP"] as const;
const GAP_HEROES = ["VFIAX", "VBIAX", "TRBCX", "FBGRX", "VIGAX"] as const;
const DEFAULT_BOOK = 1_000_000;

const here = dirname(fileURLToPath(import.meta.url));

function holdingDollars(weightPct: number, bookDollars: number): number {
  return (weightPct / 100) * bookDollars;
}

describe("PortfolioCompare smoke books", () => {
  it("defaults Current to GTM history-covered tickers at 25% each", () => {
    assert.deepEqual([...SMOKE_CURRENT_TICKERS], [...HISTORY_COVERED_CURRENT]);
    assert.equal(SMOKE_WEIGHT_PCT, 25);
    assert.equal(SMOKE_CURRENT_TICKERS.length * SMOKE_WEIGHT_PCT, 100);
    assert.equal(holdingDollars(SMOKE_WEIGHT_PCT, DEFAULT_BOOK), 250_000);
  });

  it("defaults Proposed to GTM history-covered tickers at 25% each", () => {
    assert.deepEqual([...SMOKE_PROPOSED_TICKERS], [...HISTORY_COVERED_PROPOSED]);
    assert.equal(SMOKE_PROPOSED_TICKERS.length * SMOKE_WEIGHT_PCT, 100);
  });

  it("keeps dollars derived from weight × book value when the book changes", () => {
    const book = 2_000_000;
    assert.equal(holdingDollars(SMOKE_WEIGHT_PCT, book), 500_000);
  });

  it("does not seed the Render coverage-gap heroes as smoke defaults", () => {
    const smoke = new Set([...SMOKE_CURRENT_TICKERS, ...SMOKE_PROPOSED_TICKERS]);
    for (const ticker of GAP_HEROES) {
      assert.equal(smoke.has(ticker), false, `${ticker} should not be a smoke default`);
    }
  });

  it("includes DODGX fixture rates and re-exports smoke books from the catalog", () => {
    const catalog = readFileSync(join(here, "portfolio-compare-catalog.ts"), "utf8");
    assert.match(catalog, /DODGX:\s*\{/);
    assert.match(catalog, /fundName:\s*"Dodge & Cox Stock Fund"/);
    assert.match(catalog, /from "@\/lib\/illustrate\/portfolio-compare-smoke"/);
    assert.match(catalog, /draftHolding\(ticker, SMOKE_WEIGHT_PCT,/);
  });
});
