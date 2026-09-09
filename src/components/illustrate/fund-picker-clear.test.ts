import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { shouldClearFundPickerSelection } from "./fund-picker-clear.ts";

const here = dirname(fileURLToPath(import.meta.url));

function read(relative: string): string {
  return readFileSync(join(here, relative), "utf8");
}

describe("shouldClearFundPickerSelection", () => {
  it("clears when the search value is emptied and a fund is selected", () => {
    assert.equal(
      shouldClearFundPickerSelection({
        nextValue: "",
        hasSelection: true,
        suggestionsOpen: false,
      }),
      true,
    );
  });

  it("clears Backspace/Delete on the selected chip, not while typing suggestions", () => {
    assert.equal(
      shouldClearFundPickerSelection({
        key: "Backspace",
        hasSelection: true,
        suggestionsOpen: false,
      }),
      true,
    );
    assert.equal(
      shouldClearFundPickerSelection({
        key: "Delete",
        hasSelection: true,
        suggestionsOpen: false,
      }),
      true,
    );
    assert.equal(
      shouldClearFundPickerSelection({
        key: "Backspace",
        hasSelection: true,
        suggestionsOpen: true,
      }),
      false,
    );
  });

  it("does not clear when nothing is selected", () => {
    assert.equal(
      shouldClearFundPickerSelection({
        nextValue: "",
        hasSelection: false,
        suggestionsOpen: false,
      }),
      false,
    );
    assert.equal(
      shouldClearFundPickerSelection({
        key: "Backspace",
        hasSelection: false,
        suggestionsOpen: false,
      }),
      false,
    );
  });

  it("does not treat Escape as a clear", () => {
    assert.equal(
      shouldClearFundPickerSelection({
        key: "Escape",
        hasSelection: true,
        suggestionsOpen: false,
      }),
      false,
    );
  });
});

describe("Search-a-fund clear wiring", () => {
  it("FundPicker owns a Clear search control that calls onClear", () => {
    const picker = read("FundPicker.tsx");
    assert.match(picker, /onClear\?: \(\) => void/);
    assert.match(picker, /aria-label="Clear search"/);
    assert.match(picker, /onClick=\{clearSelection\}/);
    assert.match(picker, /shouldClearFundPickerSelection/);
    assert.match(picker, /event\.key === "Escape"/);
    assert.match(picker, /setOpen\(false\);\s*return;/);
  });

  it("homepage Hero and AftertaxApp reset selected so IllustratePanel unmounts", () => {
    const hero = read("../landing/Hero.tsx");
    const app = read("../AftertaxApp.tsx");
    assert.match(hero, /onClear=\{onClear\}/);
    assert.match(app, /function clearFund\(\)/);
    assert.match(app, /setPicked\(null\)/);
    assert.match(app, /onClear=\{clearFund\}/);
    assert.match(app, /picked !== undefined \? picked : focusedFund/);
    assert.match(app, /\{selected \?/);
    assert.match(app, /<IllustratePanel selected=\{selected\} \/>/);
  });
});
