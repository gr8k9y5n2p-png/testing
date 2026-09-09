import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

describe("toTaxDeltaCardModel source chrome", () => {
  it("labels Live from Data API source and never appends demo / SAMPLE suffixes", () => {
    const source = readFileSync(join(here, "compare-map.ts"), "utf8");
    const mapper = source.split("export function toTaxDeltaCardModel")[1];
    assert.ok(mapper);
    assert.match(mapper, /isLiveDataSource\(response\.source\)/);
    assert.match(mapper, /response\.source === "mock"/);
    assert.doesNotMatch(mapper, /notes\.some/);
    assert.doesNotMatch(mapper, / · demo/);
    assert.doesNotMatch(mapper, /demo \?/);
    assert.match(mapper, /live,/);
  });
});
