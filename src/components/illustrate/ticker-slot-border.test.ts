import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { tickerSlotBorderClass } from "./ticker-slot-border.ts";

const here = dirname(fileURLToPath(import.meta.url));

function read(relative: string): string {
  return readFileSync(join(here, relative), "utf8");
}

describe("tickerSlotBorderClass", () => {
  it("keeps empty and mid-edit slots on the neutral line token", () => {
    assert.equal(
      tickerSlotBorderClass({ committed: false, midEdit: false }),
      "border-line",
    );
    assert.equal(
      tickerSlotBorderClass({ committed: false, midEdit: true }),
      "border-line",
    );
    assert.equal(
      tickerSlotBorderClass({ committed: true, midEdit: true }),
      "border-line",
    );
  });

  it("uses LIVE / above green once a ticker is locked in", () => {
    const locked = tickerSlotBorderClass({ committed: true, midEdit: false });
    assert.match(locked, /border-above/);
    assert.match(locked, /border-2/);
    assert.match(locked, /ticker-lock-in-universe/);
  });

  it("uses tax-more red when the locked ticker is not in the universe", () => {
    const missing = tickerSlotBorderClass({
      committed: false,
      midEdit: false,
      notInUniverse: true,
    });
    assert.match(missing, /border-tax-more/);
    assert.match(missing, /border-2/);
    assert.match(missing, /ticker-lock-missing/);
    assert.equal(
      tickerSlotBorderClass({
        committed: true,
        midEdit: false,
        notInUniverse: true,
      }),
      missing,
    );
    assert.equal(
      tickerSlotBorderClass({
        committed: true,
        midEdit: true,
        notInUniverse: true,
      }),
      "border-line",
    );
  });
});

describe("ticker slot locked-border wiring", () => {
  it("FundPicker and TickerField share one border helper — no page-local colors", () => {
    const helper = read("ticker-slot-border.ts");
    const picker = read("FundPicker.tsx");
    const field = read("portfolio-compare/TickerField.tsx");
    const workspace = read("CompareWorkspace.tsx");
    const column = read("portfolio-compare/AllocationColumn.tsx");
    const lists = read("../lists/ListsWorkspace.tsx");

    assert.match(helper, /border-above/);
    assert.match(helper, /border-line/);
    assert.match(helper, /border-tax-more/);
    assert.match(helper, /ticker-lock-in-universe/);
    assert.match(helper, /ticker-lock-missing/);
    assert.doesNotMatch(helper, /#[0-9a-fA-F]{3,8}/);

    const css = read("../../app/globals.css");
    assert.match(css, /@layer base/);
    assert.match(css, /\.ticker-lock-in-universe/);
    assert.match(css, /\.ticker-lock-missing/);
    assert.match(css, /border-color: var\(--above\)/);
    assert.match(css, /border-color: var\(--tax-more\)/);

    assert.match(picker, /tickerSlotBorderClass/);
    assert.match(picker, /committed: Boolean\(selected\)/);
    assert.match(picker, /notInUniverse: Boolean\(pendingTicker\)/);
    assert.match(picker, /midEdit: open/);

    assert.match(field, /tickerSlotBorderClass/);
    assert.match(field, /committed: lockedInUniverse/);
    assert.match(field, /notInUniverse: lockedMiss/);
    assert.match(field, /midEdit: open/);
    assert.match(field, /data-ticker-lock/);
    assert.match(field, /in-universe/);

    assert.match(workspace, /TickerField/);
    assert.match(column, /TickerField/);
    assert.match(lists, /tickerSlotBorderClass/);
    assert.doesNotMatch(workspace, /border-above/);
    assert.doesNotMatch(column, /border-above/);
    assert.doesNotMatch(lists, /border-above/);
  });
});
