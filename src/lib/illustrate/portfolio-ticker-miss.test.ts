import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  requestTickerOnPortfolioMiss,
} from "../request-ticker.ts";
import {
  requestTickerOnPortfolioMiss as impl,
} from "../data-api/request-ticker.ts";

const here = dirname(fileURLToPath(import.meta.url));

function read(relative: string): string {
  return readFileSync(join(here, relative), "utf8");
}

describe("Portfolio / Compare slot ticker miss wiring", () => {
  it("re-exports the shared requestTickerOnPortfolioMiss helper", () => {
    assert.equal(requestTickerOnPortfolioMiss, impl);
  });

  it("Portfolio add-holding commits unknown tickers through notifyPortfolioTickerMiss", () => {
    const field = read("../../components/illustrate/portfolio-compare/TickerField.tsx");
    const compare = read("../../components/illustrate/PortfolioCompare.tsx");
    const column = read("../../components/illustrate/portfolio-compare/AllocationColumn.tsx");
    assert.match(field, /notifyPortfolioTickerMiss/);
    assert.doesNotMatch(field, /fetch\(/);
    assert.doesNotMatch(field, /\/request\/ticker/);
    assert.match(compare, /NoticeToast/);
    assert.match(compare, /useNoticeToast/);
    assert.match(compare, /onNotice=\{onNotice\}/);
    assert.match(column, /onNotice=\{onNotice\}/);
  });

  it("Compare slots report source portfolio, not a second fetch or search_miss", () => {
    const picker = read("../../components/illustrate/FundPicker.tsx");
    const homepage = read("../../components/illustrate/HomepageFundCompare.tsx");
    const rail = read("../../components/illustrate/FundCompareRail.tsx");
    const hook = read("../data-api/use-portfolio-miss.ts");
    assert.match(picker, /usePortfolioMissRequest/);
    assert.match(picker, /reportPortfolioMiss/);
    assert.match(homepage, /reportPortfolioMiss/);
    assert.match(homepage, /compareSideFromFund\(\{ ticker: leftPending \}\)/);
    assert.match(rail, /reportPortfolioMiss/);
    assert.match(hook, /requestTickerOnPortfolioMiss/);
    assert.match(hook, /source=portfolio/);
    assert.doesNotMatch(hook, /source=search_miss/);
    assert.doesNotMatch(picker, /fetch\(/);
    assert.doesNotMatch(homepage, /fetch\(/);
    assert.doesNotMatch(rail, /\/request\/ticker/);
  });

  it("does not invent pillar dollars in pending slot or holding rows", () => {
    const field = read("../../components/illustrate/portfolio-compare/TickerField.tsx");
    const homepage = read("../../components/illustrate/HomepageFundCompare.tsx");
    assert.match(field, /fundName: ""/);
    assert.match(field, /nav: null/);
    assert.match(homepage, /compareSideFromFund\(\{ ticker: leftPending \}\)/);
    assert.match(homepage, /compareSideFromFund\(\{ ticker: rightPending \}\)/);
    assert.doesNotMatch(homepage, /estimatedDistributionAmount:\s*[1-9]/);
    assert.doesNotMatch(homepage, /nav:\s*[1-9]/);
  });
});
