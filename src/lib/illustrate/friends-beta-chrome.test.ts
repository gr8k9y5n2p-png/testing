import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

function read(relative: string): string {
  return readFileSync(join(here, relative), "utf8");
}

describe("friends-beta Portfolio / Compare chrome", () => {
  it("does not label product tabs SAMPLE or Demo data", () => {
    const portfolio = read("../../components/illustrate/PortfolioCompare.tsx");
    const card = read("../../components/illustrate/TaxDeltaCompareCard.tsx");
    const growth = read("../../components/illustrate/GrowthAndTaxDragModule.tsx");
    const chart = read("../../components/illustrate/TaxDragByYearChart.tsx");
    const strip = read("../../components/illustrate/portfolio-compare/SummaryStrip.tsx");
    const map = read("compare-map.ts");

    for (const source of [portfolio, card, growth, chart, strip]) {
      assert.doesNotMatch(source, /Aftertax · Sample/);
      assert.doesNotMatch(source, /AFTERTAX · SAMPLE/i);
      assert.doesNotMatch(source, /Demo data/);
      assert.doesNotMatch(source, /tax from Data API TBD/);
    }
    assert.doesNotMatch(portfolio, /sample \|\| !result/);
    assert.match(portfolio, /Aftertax · Portfolio/);
    assert.doesNotMatch(card, /model\.sample \? "Sample"/);
    assert.doesNotMatch(growth, /Aftertax · Sample/);
    assert.doesNotMatch(strip, / · demo/);
    assert.doesNotMatch(map, / · demo/);
  });

  it("does not fall back to mock fixtures when the live Data API is set", () => {
    const compare = read("compare-client.ts");
    const portfolio = read("portfolio-compare-client.ts");
    const illustrate = read("client.ts");
    const coverage = read("portfolio.ts");
    const performance = read("../performance/client.ts");
    const growth = read("growth-tax-load.ts");
    assert.doesNotMatch(
      compare,
      /if \(remote && response\.status >= 500\) \{\s*response = await post\("\/api\/illustrate\/compare"\)/,
    );
    assert.doesNotMatch(portfolio, /normalizePortfolioCompareResponse\(raw, "mock"\)/);
    assert.match(portfolio, /Portfolio compare is unavailable from the Data API/);
    assert.doesNotMatch(illustrate, /post\("\/api\/illustrate", request\)/);
    assert.doesNotMatch(coverage, /post\("\/api\/illustrate\/portfolio"\)/);
    assert.doesNotMatch(growth, /mode:\s*"fixture"/);
    assert.match(growth, /defaultPerformanceMode\(\)/);
    assert.doesNotMatch(
      performance,
      /params\.set\("mode", request\.mode\?\.trim\(\) \|\| "fixture"\)/,
    );
    assert.doesNotMatch(
      performance,
      /mode: request\.mode \?\? "fixture"/,
    );
    assert.doesNotMatch(
      performance,
      /if \(remote && response\.status >= 500\) \{\s*response = await fetch\(fallback/,
    );
  });

  it("never renders MOCK / seed-math banners in Search illustrate chrome", () => {
    const results = read("../../components/illustrate/IllustrationResults.tsx");
    const card = read("../../components/illustrate/PortfolioCoverageCard.tsx");
    const notes = read("user-facing-notes.ts");
    const footer =
      "MOCK /illustrate — sample seed math, not the Data team service. Set NEXT_PUBLIC_ILLUSTRATE_URL to swap.";
    assert.match(results, /userFacingNotes/);
    assert.match(card, /userFacingNotes/);
    assert.match(notes, /sample seed math/);
    assert.match(notes, /allowDemoEngine/);
    assert.match(notes, /MOCK\\s\*\\\/illustrate/);
    const runtime = read("../data-api/runtime-env.ts");
    assert.match(runtime, /NODE_ENV === "production"/);
    assert.doesNotMatch(results, /Set NEXT_PUBLIC_ILLUSTRATE_URL to swap/);
    assert.ok(
      new RegExp(String.raw`MOCK\s*/illustrate|sample seed math`).test(footer),
    );
  });

  it("proxies /api/illustrate to the live Data API when Vercel env is set", () => {
    const illustrate = read("../../app/api/illustrate/route.ts");
    const portfolio = read("../../app/api/illustrate/portfolio/route.ts");
    const compare = read("../../app/api/illustrate/compare/route.ts");
    const portfolioCompare = read("../../app/api/illustrate/portfolio/compare/route.ts");
    const helper = read("illustrate-route.ts");
    const panel = read("../../components/illustrate/IllustratePanel.tsx");
    assert.match(illustrate, /proxyLiveOrDemo/);
    assert.match(illustrate, /Illustrate is unavailable from the Data API/);
    assert.match(helper, /allowDemoEngine/);
    assert.match(helper, /getLiveIllustrateUrl/);
    assert.match(helper, /stripMockChromeFromPayload/);
    assert.ok(
      helper.indexOf("getLiveIllustrateUrl") < helper.indexOf("options.mock"),
      "live proxy must run before the localhost mock engine",
    );
    assert.match(portfolio, /proxyLiveOrDemo/);
    assert.match(compare, /proxyLiveOrDemo/);
    assert.match(portfolioCompare, /proxyLiveOrDemo/);
    assert.match(panel, /emptyIllustrateResponse/);
  });
});
