import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

describe("Open dialog trash delete", () => {
  it("wires a row trash control to DELETE /api/saved-assets/:id", () => {
    const source = readFileSync(join(here, "SavedAssetActions.tsx"), "utf8");
    assert.match(source, /deleteSavedAsset/);
    assert.match(source, /applyDeletedPickerItem/);
    assert.match(source, /savedAssetDeleteLabel/);
    assert.match(source, /savedAssetDeleteConfirm/);
    assert.match(source, /stopPropagation/);
    assert.match(source, /window\.confirm/);
    assert.match(source, /TrashCanIcon/);
    assert.match(source, /aria-label=\{savedAssetDeleteLabel\(type, item\.name\)\}/);
    assert.doesNotMatch(source, /NEXT_PUBLIC_FREEMIUM/);
    assert.doesNotMatch(source, /PaywallDialog/);
  });
});
