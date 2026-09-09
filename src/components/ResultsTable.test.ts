import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(here, "ResultsTable.tsx"), "utf8");

describe("ResultsTable EstimateRow props", () => {
  it("does not pass showPayable into EstimateRow (Vercel typecheck)", () => {
    const start = source.indexOf("<EstimateRow");
    const estimateCall = source.slice(start, source.indexOf("/>", start) + 2);
    assert.match(estimateCall, /<EstimateRow/);
    assert.doesNotMatch(estimateCall, /showPayable=/);
    const props = source.slice(
      source.indexOf("function EstimateRow"),
      source.indexOf("function onRowClick"),
    );
    assert.doesNotMatch(props, /showPayable/);
  });
});
