import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { WEBSITE_PORTFOLIO_HOLDINGS } from "./portfolio-compare-mount.ts";

const here = dirname(fileURLToPath(import.meta.url));

describe("Website PortfolioCompare mounts", () => {
  it("starts Current and Proposed with no holdings", () => {
    assert.deepEqual(WEBSITE_PORTFOLIO_HOLDINGS, []);
  });

  it("titles the Portfolio pages Portfolio, not portfolio comparison", () => {
    const page = readFileSync(join(here, "../../app/portfolio/page.tsx"), "utf8");
    const demo = readFileSync(join(here, "../../app/portfolio-compare/page.tsx"), "utf8");
    for (const source of [page, demo]) {
      assert.match(source, /title: "Aftertax — Portfolio"/);
      assert.doesNotMatch(source, /portfolio comparison/i);
    }
  });

  it("does not inject smoke tickers from Website mounts", () => {
    const homepage = readFileSync(
      join(here, "../../components/illustrate/HomepagePortfolioCompare.tsx"),
      "utf8",
    );
    const demo = readFileSync(join(here, "../../app/portfolio-compare/page.tsx"), "utf8");
    for (const source of [homepage, demo]) {
      assert.match(source, /current=\{WEBSITE_PORTFOLIO_HOLDINGS\}/);
      assert.match(source, /proposed=\{WEBSITE_PORTFOLIO_HOLDINGS\}/);
      assert.doesNotMatch(source, /smokeCurrentHoldings/);
      assert.doesNotMatch(source, /smokeProposedHoldings/);
      assert.doesNotMatch(source, /SMOKE_CURRENT_TICKERS/);
      assert.doesNotMatch(source, /AGTHX/);
    }
  });
});
