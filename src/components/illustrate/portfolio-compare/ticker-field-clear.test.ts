import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { shouldClearFundPickerSelection } from "../fund-picker-clear.ts";
import {
  emptyTickerSelection,
  shouldClearTickerSelection,
  shouldRehydrateTickerFromSelection,
  tickerFieldDisplay,
  tickerFieldSubtitle,
} from "./ticker-field-clear.ts";

const here = dirname(fileURLToPath(import.meta.url));

function read(relative: string): string {
  return readFileSync(join(here, relative), "utf8");
}

describe("ticker field X-wipe", () => {
  it("reuses the Search-a-fund clear rule", () => {
    assert.equal(shouldClearTickerSelection, shouldClearFundPickerSelection);
    assert.equal(
      shouldClearTickerSelection({
        nextValue: "",
        hasSelection: true,
        suggestionsOpen: false,
      }),
      true,
    );
    assert.equal(
      shouldClearTickerSelection({
        key: "Backspace",
        hasSelection: true,
        suggestionsOpen: false,
      }),
      true,
    );
    assert.equal(
      shouldClearTickerSelection({
        key: "Backspace",
        hasSelection: true,
        suggestionsOpen: true,
      }),
      false,
    );
    assert.equal(
      shouldClearTickerSelection({
        key: "Escape",
        hasSelection: true,
        suggestionsOpen: false,
      }),
      false,
    );
  });

  it("empties ticker, fund name, and nav together", () => {
    assert.deepEqual(emptyTickerSelection(), {
      ticker: "",
      fundName: "",
      nav: null,
    });
  });

  it("does not rehydrate the input or subtitle from a selected fund after clear", () => {
    assert.equal(
      tickerFieldDisplay({
        open: false,
        query: "",
        ticker: "MSPPX",
        cleared: true,
      }),
      "",
    );
    assert.equal(
      tickerFieldDisplay({
        open: true,
        query: "",
        ticker: "MSPPX",
        cleared: true,
      }),
      "",
    );
    assert.equal(
      tickerFieldDisplay({
        open: false,
        query: "",
        ticker: "MSPPX",
        cleared: false,
      }),
      "MSPPX",
    );
    assert.equal(
      tickerFieldSubtitle({
        fundName: "Capital Group — KKR Multi-Sector+",
        cleared: true,
      }),
      "Search a ticker",
    );
    assert.equal(shouldRehydrateTickerFromSelection({ cleared: true }), false);
    assert.equal(shouldRehydrateTickerFromSelection({ cleared: false }), true);
  });
});

describe("Portfolio / Compare ticker clear wiring", () => {
  it("TickerField owns a Clear ticker control that wipes selection", () => {
    const field = read("TickerField.tsx");
    assert.match(field, /aria-label="Clear ticker"/);
    assert.match(field, /onClick=\{clearSelection\}/);
    assert.match(field, /shouldClearFundPickerSelection/);
    assert.match(field, /emptyTickerSelection\(\)/);
    assert.match(field, /setCleared\(true\)/);
    assert.match(field, /if \(hasSelection \|\| cleared\)/);
    assert.match(field, /event\.key === "Escape"/);
    assert.match(field, /setOpen\(false\);\s*return;/);
    assert.doesNotMatch(field, /key === "Escape"[\s\S]{0,80}setQuery\(ticker\)/);
    assert.match(field, /notifyPortfolioTickerMiss/);
  });

  it("Portfolio holdings and Compare slots pass allowEmpty so blur cannot restore a ticker", () => {
    const column = read("AllocationColumn.tsx");
    const workspace = read("../CompareWorkspace.tsx");
    const rail = read("../FundCompareRail.tsx");
    assert.match(column, /allowEmpty/);
    assert.match(column, /TickerField/);
    assert.match(workspace, /allowEmpty/);
    assert.match(workspace, /setCompareSlot\(current, index, fund\.ticker\)/);
    assert.match(rail, /onClear=\{\(\) => \{/);
    assert.match(rail, /setOverridePeer\(null\)/);
    assert.match(rail, /setPendingPeer\(null\)/);
  });
});
