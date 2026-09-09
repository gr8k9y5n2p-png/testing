import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { shouldOpenFundSuggestions } from "./fund-picker-suggestions.ts";

const here = dirname(fileURLToPath(import.meta.url));

function read(relative: string): string {
  return readFileSync(join(here, relative), "utf8");
}

describe("shouldOpenFundSuggestions", () => {
  it("stays closed for empty or whitespace-only input", () => {
    assert.equal(shouldOpenFundSuggestions(""), false);
    assert.equal(shouldOpenFundSuggestions("   "), false);
    assert.equal(shouldOpenFundSuggestions("\t"), false);
  });

  it("opens once the user types a query", () => {
    assert.equal(shouldOpenFundSuggestions("v"), true);
    assert.equal(shouldOpenFundSuggestions(" VXUS "), true);
    assert.equal(shouldOpenFundSuggestions("capital"), true);
  });
});

describe("fund typeahead empty-query wiring", () => {
  it("FundPicker does not open or fill matches until the user types", () => {
    const picker = read("FundPicker.tsx");
    assert.match(picker, /shouldOpenFundSuggestions/);
    assert.match(picker, /if \(!query\.trim\(\)\) return \[\]/);
    assert.match(picker, /showSuggestions\(query\)/);
    assert.match(picker, /showSuggestions\(next\)/);
    assert.doesNotMatch(picker, /setOpen\(true\)/);
  });

  it("TickerField does not recommend funds on empty focus", () => {
    const field = read("portfolio-compare/TickerField.tsx");
    assert.match(field, /shouldOpenFundSuggestions/);
    assert.match(field, /if \(!needle\) return \[\]/);
    assert.match(field, /showSuggestions\(next\)/);
    assert.match(field, /showSuggestions\(ticker\)/);
    assert.doesNotMatch(field, /if \(!needle\) return pool\.slice\(0,\s*8\)/);
    assert.doesNotMatch(field, /setOpen\(true\)/);
  });

  it("Growth add-fund datalist stays empty until the user types", () => {
    const growth = read("GrowthAndTaxDragModule.tsx");
    assert.match(growth, /shouldOpenFundSuggestions\(addTicker\)/);
    assert.match(growth, /list="growth-tax-funds"/);
  });
});
