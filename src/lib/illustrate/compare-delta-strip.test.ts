import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  COMPARE_DELTA_STRIP_LABELS,
  deltaStripFromPairMetrics,
  deltaStripFromSingleUpcoming,
  reservedDeltaStrip,
  scaleNormalizedHoldingDollars,
  scaleUpcomingToHolding,
} from "./compare-delta-strip.ts";

describe("compare delta strip", () => {
  it("reserves all four metric cells without inventing $0", () => {
    const items = reservedDeltaStrip();
    assert.deepEqual(
      items.map((item) => item.key),
      ["tax_difference", "tax_drag", "distributions", "upcoming_tax"],
    );
    assert.equal(items[0]?.label, COMPARE_DELTA_STRIP_LABELS.tax_difference);
    assert.equal(items[0]?.headline, null);
    assert.equal(items[1]?.headline, null);
    assert.equal(items[2]?.headline, null);
    assert.match(items[3]?.headline ?? "", /undisclosed/i);
    assert.equal(
      items.some((item) => item.headline === "$0" || item.headline === "$0.00"),
      false,
    );
    assert.equal(items[0]?.detail, "on $10,000");
    assert.equal(reservedDeltaStrip(25_000)[0]?.detail, "on $25,000");
  });

  it("keeps pair Δ reserved for one fund and uses unpaid upcoming or Undisclosed", () => {
    const empty = deltaStripFromSingleUpcoming({ announced: false, dollars: null });
    assert.equal(empty[0]?.reserved, true);
    assert.equal(empty[0]?.headline, null);
    assert.match(empty[3]?.headline ?? "", /undisclosed/i);

    const announced = deltaStripFromSingleUpcoming({ announced: true, dollars: 185 });
    assert.equal(announced[0]?.headline, null);
    assert.equal(announced[3]?.headline, "$185");
    assert.equal(announced[3]?.reserved, false);
  });

  it("fills reserved cells from a live pair model without dropping the four-slot layout", () => {
    const items = deltaStripFromPairMetrics([
      {
        key: "tax_difference",
        headline: "$120 more tax",
        detail: "on $10,000",
        polarity: "more",
      },
    ]);
    assert.equal(items.length, 4);
    assert.equal(items[0]?.headline, "$120 more tax");
    assert.equal(items[0]?.reserved, false);
    assert.equal(items[1]?.reserved, true);
    assert.match(items[3]?.headline ?? "", /undisclosed/i);
  });

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
