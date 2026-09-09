import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(here, "Dashboard.tsx"), "utf8");

describe("Dashboard Paid history year", () => {
  it("sends paid_year to /api/funds and wires the Search table toggle", () => {
    assert.match(source, /paid_year/);
    assert.match(source, /defaultPaidHistoryYear/);
    assert.match(source, /paidHistoryYearOptions/);
    assert.match(source, /paidYear=\{paidYear\}/);
    assert.match(source, /onPaidYear=\{applyPaidYear\}/);
  });
});
