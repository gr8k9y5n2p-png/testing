import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  FREE_COMPARE_LIMIT,
  FREE_PORTFOLIO_LIMIT,
  FREE_SEARCH_LIMIT,
  compareSessionKey,
  incrementUsage,
  isFreemiumDisabled,
  isSubscriptionEntitled,
  mergeUsage,
  normalizeUsage,
  portfolioReviewKey,
  remainingFromUsage,
  usageWalls,
} from "./limits.ts";

describe("freemium limits", () => {
  it("locks 10 / 3 / 3", () => {
    assert.equal(FREE_SEARCH_LIMIT, 10);
    assert.equal(FREE_COMPARE_LIMIT, 3);
    assert.equal(FREE_PORTFOLIO_LIMIT, 3);
  });

  it("enables the soft wall unless NEXT_PUBLIC_FREEMIUM_DISABLED is on", () => {
    assert.equal(isFreemiumDisabled({}), false);
    assert.equal(isFreemiumDisabled({ NEXT_PUBLIC_FREEMIUM_DISABLED: "" }), false);
    assert.equal(isFreemiumDisabled({ NEXT_PUBLIC_FREEMIUM_DISABLED: "false" }), false);
    assert.equal(isFreemiumDisabled({ NEXT_PUBLIC_FREEMIUM_DISABLED: "true" }), true);
    assert.equal(isFreemiumDisabled({ NEXT_PUBLIC_FREEMIUM_DISABLED: "1" }), true);
  });

  it("counts each search load and distinct compare / portfolio keys", () => {
    let usage = normalizeUsage(null);
    usage = incrementUsage(usage, "search");
    usage = incrementUsage(usage, "search");
    usage = incrementUsage(usage, "compare", compareSessionKey(["agthx", "FCNTX"]));
    usage = incrementUsage(usage, "compare", compareSessionKey(["FCNTX", "AGTHX"]));
    usage = incrementUsage(usage, "portfolio", portfolioReviewKey(["AGTHX"], ["FCNTX"]));
    assert.equal(usage.searches, 2);
    assert.deepEqual(usage.compareKeys, ["AGTHX,FCNTX"]);
    assert.deepEqual(usage.portfolioKeys, ["AGTHX|FCNTX"]);
  });

  it("merges device into account with max / union", () => {
    const merged = mergeUsage(
      { searches: 2, compareKeys: ["A"], portfolioKeys: [] },
      { searches: 8, compareKeys: ["B"], portfolioKeys: ["X"] },
    );
    assert.equal(merged.searches, 8);
    assert.deepEqual(merged.compareKeys, ["A", "B"]);
    assert.deepEqual(merged.portfolioKeys, ["X"]);
  });

  it("raises walls at the locked limits", () => {
    const walls = usageWalls({
      searches: 10,
      compareKeys: ["a", "b", "c"],
      portfolioKeys: ["1", "2", "3"],
    });
    assert.deepEqual(walls, { search: true, compare: true, portfolio: true });
    assert.deepEqual(
      remainingFromUsage({ searches: 7, compareKeys: ["a"], portfolioKeys: [] }),
      { searches: 3, compares: 2, portfolios: 3 },
    );
  });

  it("treats active and cancel-at-period-end as entitled until the period ends", () => {
    assert.equal(isSubscriptionEntitled({ subscriptionStatus: "active" }), true);
    assert.equal(isSubscriptionEntitled({ subscriptionStatus: "trialing" }), true);
    assert.equal(isSubscriptionEntitled({ subscriptionStatus: "canceled" }), false);
    const later = new Date(Date.now() + 60_000).toISOString();
    assert.equal(
      isSubscriptionEntitled({
        subscriptionStatus: "canceled",
        cancelAtPeriodEnd: true,
        currentPeriodEnd: later,
      }),
      true,
    );
  });
});
