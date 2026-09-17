import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  applyDeletedPickerItem,
  savedAssetDeleteConfirm,
  savedAssetDeleteLabel,
} from "./picker.ts";

describe("Open dialog delete picker", () => {
  it("removes the row and clears selection when that list was selected", () => {
    const items = [
      { id: "sav_a", name: "Test 2" },
      { id: "sav_b", name: "Test" },
    ];
    assert.deepEqual(applyDeletedPickerItem(items, "sav_a", "sav_a"), {
      items: [{ id: "sav_b", name: "Test" }],
      selectedId: null,
    });
  });

  it("keeps another selected row after deleting a neighbor", () => {
    const items = [
      { id: "sav_a", name: "Test 2" },
      { id: "sav_b", name: "Test" },
    ];
    assert.deepEqual(applyDeletedPickerItem(items, "sav_b", "sav_a"), {
      items: [{ id: "sav_b", name: "Test" }],
      selectedId: "sav_b",
    });
  });

  it("labels list and portfolio trash buttons", () => {
    assert.equal(savedAssetDeleteLabel("list", "Test 2"), "Delete list Test 2");
    assert.equal(
      savedAssetDeleteLabel("portfolio", "Proposal A"),
      "Delete portfolio Proposal A",
    );
    assert.equal(savedAssetDeleteConfirm("list", "Test 2"), "Delete list Test 2?");
    assert.equal(
      savedAssetDeleteConfirm("portfolio", "Proposal A"),
      "Delete portfolio Proposal A?",
    );
  });
});
