import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

function read(relative: string): string {
  return readFileSync(join(here, relative), "utf8");
}

const SEARCH_BANNER =
  "MOCK /illustrate — sample seed math, not the Data team service. Set NEXT_PUBLIC_ILLUSTRATE_URL to swap.";
const PORTFOLIO_BANNER =
  "MOCK /illustrate/portfolio. Set NEXT_PUBLIC_DATA_API_URL to use the Data team endpoint.";

describe("production MOCK lock", () => {
  it("keeps the GTM-failing banners only behind demoEngineNotes + strip", () => {
    const engine = read("mock-engine.ts");
    const portfolio = read("../../app/api/illustrate/portfolio/route.ts");
    const notes = read("user-facing-notes.ts");
    assert.match(engine, /demoEngineNotes/);
    assert.match(portfolio, /demoEngineNotes/);
    assert.match(notes, /stripMockChromeFromPayload/);
    assert.match(notes, /Set NEXT_PUBLIC_\(DATA_API_URL\|ILLUSTRATE_URL\)/);
    assert.equal(
      new RegExp(String.raw`MOCK\s*/illustrate|sample seed math`).test(SEARCH_BANNER),
      true,
    );
    assert.equal(
      new RegExp(String.raw`MOCK\s*/illustrate/portfolio|Set NEXT_PUBLIC_DATA_API_URL`).test(
        PORTFOLIO_BANNER,
      ),
      true,
    );
  });

  it("does not treat same-origin /api/illustrate as mock", () => {
    const config = read("../data-api/config.ts");
    assert.match(config, /return allowDemoEngine\(\)/);
    assert.doesNotMatch(
      config,
      /export function isMockIllustrateEndpoint[\s\S]*return endpoint\.startsWith\("\/"\)/,
    );
    assert.match(config, /sameOriginApiUrl\("\/illustrate"\)/);
  });

  it("API illustrate routes proxy or 503 — they do not run seed math on Production", () => {
    const helper = read("illustrate-route.ts");
    const illustrate = read("../../app/api/illustrate/route.ts");
    const portfolio = read("../../app/api/illustrate/portfolio/route.ts");
    const compare = read("../../app/api/illustrate/compare/route.ts");
    const portfolioCompare = read("../../app/api/illustrate/portfolio/compare/route.ts");
    assert.match(helper, /if \(!allowDemoEngine\(\)\)/);
    assert.match(helper, /stripMockChromeFromPayload/);
    for (const source of [illustrate, portfolio, compare, portfolioCompare]) {
      assert.match(source, /proxyLiveOrDemo/);
    }
  });

  it("clients never seed-fallback on Production", () => {
    const panel = read("../../components/illustrate/IllustratePanel.tsx");
    const compare = read("compare-client.ts");
    const portfolio = read("portfolio-compare-client.ts");
    const coverage = read("portfolio.ts");
    assert.match(panel, /isMockIllustrate\(\)/);
    assert.match(compare, /return allowDemoEngine\(\)/);
    assert.match(compare, /sameOriginApiUrl\("\/illustrate\/compare"\)/);
    assert.match(portfolio, /emptyPortfolioAllocation/);
    assert.match(portfolio, /allowDemoEngine\(\)/);
    assert.match(coverage, /sameOriginApiUrl\("\/illustrate\/portfolio"\)/);
    assert.match(coverage, /const remote = !allowDemoEngine\(\)/);
  });
});
