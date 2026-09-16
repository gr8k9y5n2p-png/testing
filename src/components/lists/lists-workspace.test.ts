import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

describe("Lists Save / Open chrome", () => {
  it("puts Save and Open at the top of ListsWorkspace", () => {
    const source = readFileSync(join(here, "ListsWorkspace.tsx"), "utf8");
    assert.match(source, /SavedAssetActions/);
    assert.match(source, /type="list"/);
    assert.match(source, /getPayload=\{\(\) => \(\{ tickers \}\)\}/);
    assert.match(source, /parseListPayload/);
    assert.match(source, /lists-heading/);
    const actionsAt = source.indexOf("<SavedAssetActions");
    const detailAt = source.indexOf("{LISTS_DETAIL}");
    assert.ok(actionsAt > 0 && detailAt > actionsAt, "Open/Save sit above the paste helper copy");
    assert.doesNotMatch(source, /NEXT_PUBLIC_FREEMIUM/);
    assert.doesNotMatch(source, /PaywallDialog/);
  });
});
