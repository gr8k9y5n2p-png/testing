import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  scaleNormalizedHoldingDollars,
  scaleUpcomingToHolding,
} from "./compare-map.ts";

describe("compare holding scale", () => {
  it("rescales $10k-normalized pair dollars to the shared holding", () => {
    assert.equal(scaleNormalizedHoldingDollars(-142, 20_000, 10_000), -284);
    assert.equal(scaleNormalizedHoldingDollars(-142, 10_000, 10_000), -142);
    const upcoming = scaleUpcomingToHolding(
      { left_dollars: 185, right_dollars: 100, delta_dollars: -85 },
      20_000,
      10_000,
    );
    assert.equal(upcoming?.left_dollars, 370);
    assert.equal(upcoming?.right_dollars, 200);
    assert.equal(upcoming?.delta_dollars, -170);
  });
});
