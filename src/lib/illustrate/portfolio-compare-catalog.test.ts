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

const GAP_HEROES = ["VFIAX", "VBIAX", "TRBCX", "FBGRX", "VIGAX"] as const;
const LEGACY_SMOKE_TICKERS = [
  "AGTHX",
  "DODIX",
  "AMCAP",
  "DODGX",
  "AMCPX",
  "CGHM",
] as const;

const here = dirname(fileURLToPath(import.meta.url));

function holdingDollars(weightPct: number, bookDollars: number): number {
  return (weightPct / 100) * bookDollars;
}

describe("PortfolioCompare smoke books", () => {
  it("starts Current and Proposed with no seeded holdings", () => {
    assert.deepEqual([...SMOKE_CURRENT_TICKERS], []);
    assert.deepEqual([...SMOKE_PROPOSED_TICKERS], []);
    const catalog = readFileSync(join(here, "portfolio-compare-catalog.ts"), "utf8");
    assert.match(catalog, /return SMOKE_CURRENT_TICKERS\.map/);
    assert.match(catalog, /return SMOKE_PROPOSED_TICKERS\.map/);
  });

  it("does not preload the former history-covered smoke tickers", () => {
    const smoke = new Set([...SMOKE_CURRENT_TICKERS, ...SMOKE_PROPOSED_TICKERS]);
    for (const ticker of LEGACY_SMOKE_TICKERS) {
      assert.equal(smoke.has(ticker), false, `${ticker} should not be a default holding`);
    }
  });

  it("keeps dollars derived from weight × book value when the book changes", () => {
    const book = 2_000_000;
    assert.equal(SMOKE_WEIGHT_PCT, 25);
    assert.equal(holdingDollars(SMOKE_WEIGHT_PCT, book), 500_000);
  });

  it("does not seed the Render coverage-gap heroes as smoke defaults", () => {
    const smoke = new Set([...SMOKE_CURRENT_TICKERS, ...SMOKE_PROPOSED_TICKERS]);
    for (const ticker of GAP_HEROES) {
      assert.equal(smoke.has(ticker), false, `${ticker} should not be a smoke default`);
    }
  });

  it("keeps catalog rates for autocomplete after a user adds a ticker", () => {
    const catalog = readFileSync(join(here, "portfolio-compare-catalog.ts"), "utf8");
    assert.match(catalog, /DODGX:\s*\{/);
    assert.match(catalog, /fundName:\s*"Dodge & Cox Stock Fund"/);
    assert.match(catalog, /from "@\/lib\/illustrate\/portfolio-compare-smoke"/);
    assert.match(catalog, /draftHolding\(ticker, SMOKE_WEIGHT_PCT,/);
  });

  it("defaults PortfolioCompare to the empty smoke books", () => {
    const compare = readFileSync(
      join(here, "../../components/illustrate/PortfolioCompare.tsx"),
      "utf8",
    );
    assert.match(compare, /currentProp \?\? smokeCurrentHoldings\(/);
    assert.match(compare, /proposedProp \?\? smokeProposedHoldings\(/);
    assert.doesNotMatch(
      compare,
      /Defaults to GTM history-covered Current: AGTHX \/ DODIX \/ AMCAP \/ DODGX/,
    );
    assert.doesNotMatch(
      compare,
      /Defaults to GTM history-covered Proposed: AMCPX \/ CGHM \/ AGTHX \/ AMCAP/,
    );
  });

  it("invites + Add holding when a book has zero holdings", () => {
    const column = readFileSync(
      join(here, "../../components/illustrate/portfolio-compare/AllocationColumn.tsx"),
      "utf8",
    );
    assert.match(column, /holdings\.length === 0/);
    assert.match(column, /No holdings yet — use \+ Add holding to start/);
    assert.match(column, /Add holding/);
  });

  it("keeps AGTHX fundName aligned with SAMPLE_FUNDS so Data can AND fund_name", () => {
    const catalog = readFileSync(join(here, "portfolio-compare-catalog.ts"), "utf8");
    const seed = readFileSync(join(here, "../../data/seed.ts"), "utf8");
    assert.match(catalog, /AGTHX:\s*\{[\s\S]*?fundName:\s*"The Growth Fund of America"/);
    assert.match(seed, /fundName:\s*"The Growth Fund of America"[\s\S]*?ticker:\s*"AGTHX"/);
    assert.doesNotMatch(catalog, /American Funds Growth Fund of America/);
  });
});
