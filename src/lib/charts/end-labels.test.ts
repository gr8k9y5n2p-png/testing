import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  END_LABEL_MIN_GAP,
  hasOverlap,
  staggerEndLabels,
} from "./end-labels.ts";

describe("staggerEndLabels", () => {
  it("leaves well-separated labels on their series y", () => {
    const placed = staggerEndLabels(
      [
        { id: "high", y: 40 },
        { id: "low", y: 120 },
      ],
      { minY: 18, maxY: 208 },
    );
    assert.ok(placed);
    assert.equal(placed[0].id, "high");
    assert.equal(placed[0].labelY, 40);
    assert.equal(placed[1].id, "low");
    assert.equal(placed[1].labelY, 120);
    assert.equal(hasOverlap(placed), false);
  });

  it("separates Eric's close AMCPX / AGTHX endings", () => {
    // Pixel y's for $12,869 vs $13,828 on the $10k growth scale (~18px apart).
    // The old index offset (−12 / +12) pulled these toward each other.
    const amcpxY = 153.5;
    const agthxY = 135.3;
    const placed = staggerEndLabels(
      [
        { id: "AMCPX", y: amcpxY },
        { id: "AGTHX", y: agthxY },
      ],
      { minY: 26, maxY: 200, minGap: END_LABEL_MIN_GAP },
    );
    assert.ok(placed);
    const byId = Object.fromEntries(placed.map((row) => [row.id, row]));
    assert.ok(byId.AGTHX.labelY < byId.AMCPX.labelY);
    assert.ok(byId.AMCPX.labelY - byId.AGTHX.labelY >= END_LABEL_MIN_GAP);
    assert.equal(hasOverlap(placed), false);
  });

  it("keeps 6 stacked funds readable inside the plot", () => {
    const placed = staggerEndLabels(
      Array.from({ length: 6 }, (_, index) => ({
        id: `f${index}`,
        y: 140 + index * 2,
      })),
      { minY: 26, maxY: 200 },
    );
    assert.ok(placed);
    assert.equal(placed.length, 6);
    assert.equal(hasOverlap(placed), false);
    assert.ok(placed[0].labelY >= 26);
    assert.ok(placed[5].labelY <= 200);
  });

  it("drops labels when they cannot fit without overlapping", () => {
    const placed = staggerEndLabels(
      [
        { id: "a", y: 10 },
        { id: "b", y: 11 },
        { id: "c", y: 12 },
      ],
      { minY: 10, maxY: 20, minGap: 14 },
    );
    assert.equal(placed, null);
  });

  it("does not invert series order when staggering", () => {
    const placed = staggerEndLabels(
      [
        { id: "top", y: 80 },
        { id: "mid", y: 88 },
        { id: "bot", y: 94 },
      ],
      { minY: 18, maxY: 208 },
    );
    assert.ok(placed);
    assert.deepEqual(
      placed.map((row) => row.id),
      ["top", "mid", "bot"],
    );
    for (let i = 1; i < placed.length; i += 1) {
      assert.ok(placed[i].labelY >= placed[i - 1].labelY + END_LABEL_MIN_GAP);
    }
  });
});
