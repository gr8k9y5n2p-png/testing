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
    assert.doesNotMatch(
      compare,
      /if \(remote && response\.status >= 500\) \{\s*response = await post\("\/api\/illustrate\/compare"\)/,
    );
    assert.doesNotMatch(portfolio, /normalizePortfolioCompareResponse\(raw, "mock"\)/);
    assert.match(portfolio, /Portfolio compare is unavailable from the Data API/);
  });
});
