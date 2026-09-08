import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  compareSideFromFund,
  navFromFundMetadata,
  positiveNav,
  toDataApiCompareBody,
  withPortfolioHoldingNav,
} from "./compare-request.ts";

const here = dirname(fileURLToPath(import.meta.url));

/** Seed NAVs for the Engineering | Data AGTHX vs VIGAX pair. */
const SEED_NAV: Record<string, number> = {
  AGTHX: 72.14,
  VIGAX: 186.4,
};

function seedLookup(ticker: string): number | undefined {
  return SEED_NAV[ticker.toUpperCase()];
}

describe("compare-request NAV / Data body", () => {
  it("treats only values > 0 as NAV", () => {
    assert.equal(positiveNav(72.14), 72.14);
    assert.equal(positiveNav(0), undefined);
    assert.equal(positiveNav(-1), undefined);
    assert.equal(positiveNav(null), undefined);
    assert.equal(positiveNav(""), undefined);
  });

  it("uses search metadata first, then the ticker lookup", () => {
    assert.equal(navFromFundMetadata("AGTHX", 80, seedLookup), 80);
    assert.equal(navFromFundMetadata("AGTHX", 0, seedLookup), 72.14);
    assert.equal(navFromFundMetadata("vigax", undefined, seedLookup), 186.4);
    assert.equal(navFromFundMetadata("ZZNOPE", undefined, seedLookup), undefined);
  });

  it("builds a compare side with nav_per_share from fund metadata", () => {
    const side = compareSideFromFund(
      {
        ticker: "AGTHX",
        fundName: "The Growth Fund of America",
        family: "American Funds",
        nav: 0,
      },
      seedLookup,
    );
    assert.equal(side.selectors?.ticker, "AGTHX");
    assert.equal(side.nav_per_share, 72.14);
  });

  it("attaches seed NAV for AGTHX vs VIGAX when callers omit nav_per_share", () => {
    const body = toDataApiCompareBody(
      {
        mode: "fund_vs_fund",
        holding_dollars: 10_000,
        left: {
          label: "AGTHX",
          selectors: { ticker: "AGTHX", fund_identifier: "AGTHX" },
        },
        right: {
          label: "VIGAX",
          selectors: { ticker: "VIGAX", fund_identifier: "VIGAX" },
        },
      },
      seedLookup,
    );
    assert.equal(body.left?.nav_per_share, 72.14);
    assert.equal(body.right?.nav_per_share, 186.4);
    assert.equal(body.nav_per_share, undefined);
  });

  it("keeps an explicit per-side NAV and does not copy it to the peer", () => {
    const body = toDataApiCompareBody(
      {
        mode: "fund_vs_fund",
        holding_dollars: 10_000,
        left: {
          selectors: { ticker: "AGTHX" },
          nav_per_share: 100,
        },
        right: {
          selectors: { ticker: "VIGAX" },
          nav_per_share: 200,
        },
      },
      seedLookup,
    );
    assert.equal(body.left?.nav_per_share, 100);
    assert.equal(body.right?.nav_per_share, 200);
  });

  it("omits nav for unknown tickers so the request is holding_dollars-only", () => {
    const body = toDataApiCompareBody({
      mode: "fund_vs_fund",
      holding_dollars: 10_000,
      nav_per_share: 0,
      left: { selectors: { ticker: "ZZNOPE" }, nav_per_share: 0 },
      right: { selectors: { ticker: "YYNOPE" } },
    });
    assert.equal(body.left?.nav_per_share, undefined);
    assert.equal(body.right?.nav_per_share, undefined);
    assert.equal(body.nav_per_share, undefined);
  });

  it("stays aligned with SAMPLE_FUNDS NAVs for AGTHX and VIGAX", () => {
    const seed = readFileSync(join(here, "../../data/seed.ts"), "utf8");
    assert.match(seed, /ticker:\s*"AGTHX"[\s\S]*?nav:\s*72\.14/);
    assert.match(seed, /ticker:\s*"VIGAX"[\s\S]*?nav:\s*186\.4/);
  });

  it("fills YoY top-level and left NAV from metadata", () => {
    const body = toDataApiCompareBody(
      {
        mode: "yoy",
        holding_dollars: 10_000,
        selectors: { ticker: "AGTHX", fund_identifier: "AGTHX" },
        left: {
          label: "AGTHX",
          selectors: { ticker: "AGTHX", fund_identifier: "AGTHX" },
        },
        periods: [{ year: 2024 }, { year: 2025 }],
      },
      seedLookup,
    );
    assert.equal(body.nav_per_share, 72.14);
    assert.equal(body.left?.nav_per_share, 72.14);
  });

  it("attaches portfolio holding NAV from search/seed and omits 0", () => {
    const lookup = (ticker: string) =>
      ({ AGTHX: 72.14, DODIX: 12.8, AMCAP: 41.22, DODGX: 273.16, CGHM: 25.18 }[
        ticker.toUpperCase()
      ]);
    assert.equal(
      withPortfolioHoldingNav({ ticker: "AGTHX", nav_per_share: 0 }, lookup).nav_per_share,
      72.14,
    );
    assert.equal(
      withPortfolioHoldingNav({ ticker: "DODIX" }, lookup).nav_per_share,
      12.8,
    );
    assert.equal(
      withPortfolioHoldingNav({ ticker: "AMCAP" }, lookup).nav_per_share,
      41.22,
    );
    assert.equal(
      withPortfolioHoldingNav({ ticker: "CGHM", nav_per_share: 0 }, lookup).nav_per_share,
      25.18,
    );
    assert.equal(
      withPortfolioHoldingNav({ ticker: "ZZNOPE", nav_per_share: 0 }, lookup).nav_per_share,
      undefined,
    );
  });
});
