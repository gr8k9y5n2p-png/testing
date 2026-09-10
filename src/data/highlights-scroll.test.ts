import assert from "node:assert/strict";
import { test } from "node:test";
import { getHighlights, withPeerContext } from "./queries.ts";
import type { FundEstimate } from "./types.ts";

function stub(index: number, asOfDate: string, pct: number): FundEstimate {
  const n = String(index).padStart(3, "0");
  return {
    id: `recent-${n}`,
    fundName: `Weekly ${n}`,
    ticker: `WK${n}`,
    cusip: "000000000",
    family: "American Funds",
    category: "Large Growth",
    shareClass: "A",
    nav: 10,
    estimatedDistributionAmount: (pct / 100) * 10,
    estimatedOrdinaryIncome: (pct / 100) * 5,
    estimatedCapitalGains: (pct / 100) * 5,
    estimatedDistributionPctNav: pct,
    publishedAt: asOfDate,
    asOfDate,
    recordDate: "2026-12-12",
    exDate: "2026-12-15",
    payableDate: "2026-12-17",
    publicationStage: "updated_estimate",
    bucket: "upcoming",
    paidHistory: [],
    distributionYear: 2026,
  };
}

test("Most Recent keeps same-day weekly dump rows beyond the card footprint", () => {
  const funds = withPeerContext(
    Array.from({ length: 40 }, (_, index) => stub(index + 1, "2026-09-08", 1 + index / 100)),
  );
  const highlights = getHighlights(funds, 5);
  assert.ok(highlights.mostRecent.length > 5);
  assert.equal(highlights.mostRecent.length, 40);
  assert.ok(highlights.mostRecent.every((fund) => fund.asOfDate === "2026-09-08"));
});

test("Largest also fills the scroller instead of capping at 5", () => {
  const funds = withPeerContext(
    Array.from({ length: 20 }, (_, index) =>
      stub(index + 1, "2026-09-01", 8 - index * 0.1),
    ),
  );
  const highlights = getHighlights(funds, 5);
  assert.equal(highlights.largest.length, 20);
});
