import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

const PORTFOLIO_COMPARE_SURFACES = [
  "../../components/illustrate/PortfolioCompare.tsx",
  "../../components/illustrate/TaxDeltaCompareCard.tsx",
  "../../components/illustrate/GrowthAndTaxDragModule.tsx",
  "../../components/illustrate/TaxDragByYearChart.tsx",
  "../../components/illustrate/portfolio-compare/SummaryStrip.tsx",
  "compare-map.ts",
  "portfolio-compare-export.ts",
] as const;

const SAMPLE_DEMO_CHROME = /Demo data|Aftertax · Sample| · Sample"| · demo\b|demo data/i;

describe("Portfolio + Compare friends-beta chrome", () => {
  it("does not advertise SAMPLE / demo data on Modules-owned surfaces", () => {
    for (const relative of PORTFOLIO_COMPARE_SURFACES) {
      const source = readFileSync(join(here, relative), "utf8");
      assert.doesNotMatch(
        source,
        SAMPLE_DEMO_CHROME,
        `${relative} still advertises Sample / demo chrome`,
      );
    }
  });

  it("keeps real empty-state copy (N/A, Undisclosed, No Performance)", () => {
    const portfolio = readFileSync(
      join(here, "../../components/illustrate/PortfolioCompare.tsx"),
      "utf8",
    );
    const growth = readFileSync(
      join(here, "../../components/illustrate/GrowthAndTaxDragModule.tsx"),
      "utf8",
    );
    const card = readFileSync(
      join(here, "../../components/illustrate/TaxDeltaCompareCard.tsx"),
      "utf8",
    );
    assert.match(portfolio, /Add at least one weighted holding/);
    assert.match(growth, /PERFORMANCE_UNAVAILABLE_LABEL/);
    assert.match(card, /TAX_DRAG_NA_LABEL/);
  });

  it("labels Live from Data API source and stays blank for mock", () => {
    const portfolio = readFileSync(
      join(here, "../../components/illustrate/PortfolioCompare.tsx"),
      "utf8",
    );
    const card = readFileSync(
      join(here, "../../components/illustrate/TaxDeltaCompareCard.tsx"),
      "utf8",
    );
    const growth = readFileSync(
      join(here, "../../components/illustrate/GrowthAndTaxDragModule.tsx"),
      "utf8",
    );
    const chart = readFileSync(
      join(here, "../../components/illustrate/TaxDragByYearChart.tsx"),
      "utf8",
    );
    assert.match(portfolio, /sourceEyebrowSuffix\(result\?\.source\)/);
    assert.match(card, /model\.live \? " · Live" : ""/);
    assert.match(growth, /sourceEyebrowSuffix\(liveSource\)/);
    assert.match(chart, /live \? " · Live" : ""/);
    assert.doesNotMatch(portfolio, /"Sample"/);
    assert.doesNotMatch(card, /"Sample"/);
    assert.doesNotMatch(growth, /"Sample"/);
  });

  it("omits demo data from Portfolio export HTML", () => {
    const source = readFileSync(join(here, "portfolio-compare-export.ts"), "utf8");
    const html = source.split("export function renderPortfolioComparePrintHtml")[1];
    assert.ok(html);
    assert.doesNotMatch(html, /demo data/i);
    assert.doesNotMatch(html, /model\.source === "mock"/);
  });
});
