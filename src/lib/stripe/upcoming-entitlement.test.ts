import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { describe, it } from "node:test";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { entitlementFrom, isUpcomingEntitled } from "./entitlement.ts";
import { SEARCH_UPCOMING_PAYWALL_LEAD } from "../copy.ts";

const here = dirname(fileURLToPath(import.meta.url));

describe("Upcoming / Announced entitlement gate", () => {
  it("treats homepage Upcoming as locked unless subscribed or freemium-bypass", () => {
    const locked = entitlementFrom(null, {
      searches: 0,
      compareKeys: [],
      portfolioKeys: [],
    });
    assert.equal(locked.walls.upcoming, true);
    assert.equal(locked.walls.search, false);
    assert.equal(isUpcomingEntitled(locked), false);

    const spent = entitlementFrom(null, {
      searches: 5,
      compareKeys: [],
      portfolioKeys: [],
    });
    assert.equal(spent.walls.upcoming, true);
    assert.equal(spent.walls.search, true);

    const subscribed = entitlementFrom(
      {
        id: "acct_test",
        email: "ada@aftertax.com",
        passwordHash: "x",
        createdAt: "2026-01-01T00:00:00.000Z",
        updatedAt: "2026-01-01T00:00:00.000Z",
        subscriptionStatus: "active",
        cancelAtPeriodEnd: false,
        currentPeriodEnd: null,
        stripeCustomerId: null,
        stripeSubscriptionId: null,
        usage: { searches: 0, compareKeys: [], portfolioKeys: [] },
      },
      { searches: 0, compareKeys: [], portfolioKeys: [] },
    );
    assert.equal(subscribed.walls.upcoming, false);
    assert.equal(isUpcomingEntitled(subscribed), true);

    const bypassed = entitlementFrom(
      null,
      { searches: 1, compareKeys: [], portfolioKeys: [] },
      { NEXT_PUBLIC_FREEMIUM_DISABLED: "1" },
    );
    assert.equal(bypassed.walls.upcoming, false);
    assert.equal(isUpcomingEntitled(bypassed), true);
  });

  it("wires the homepage Upcoming module to SoftWall + Unlock Checkout, not Paid History", () => {
    const dashboard = readFileSync(
      join(here, "../../components/Dashboard.tsx"),
      "utf8",
    );
    const app = readFileSync(
      join(here, "../../components/AftertaxApp.tsx"),
      "utf8",
    );
    const wall = readFileSync(
      join(here, "../../components/paywall/SoftWall.tsx"),
      "utf8",
    );
    const copy = readFileSync(join(here, "../copy.ts"), "utf8");

    assert.match(dashboard, /active=\{billing\.walls\.upcoming\}/);
    assert.match(dashboard, /surface="upcoming"/);
    assert.match(dashboard, /showPaidHistory=\{false\}/);
    assert.match(dashboard, /showUpcoming=\{false\}/);
    assert.match(dashboard, /active=\{billing\.walls\.search\}/);
    assert.match(dashboard, /SEARCH_UPCOMING_HEADING/);

    const upcomingBlock = dashboard.slice(
      dashboard.indexOf("billing.walls.upcoming"),
      dashboard.indexOf("billing.walls.search"),
    );
    assert.match(upcomingBlock, /SEARCH_UPCOMING_HEADING/);
    assert.match(upcomingBlock, /SearchToolbar/);
    assert.match(upcomingBlock, /showPaidHistory=\{false\}/);
    assert.doesNotMatch(upcomingBlock, /showUpcoming=\{false\}/);

    assert.match(app, /<IllustratePanel/);
    assert.match(app, /<Dashboard/);
    assert.doesNotMatch(
      app,
      /SoftWall active=\{billing\.walls\.search\}[\s\S]*<Dashboard/,
    );

    assert.match(wall, /surface === "upcoming"/);
    assert.match(wall, /SEARCH_UPCOMING_PAYWALL_LEAD/);
    assert.match(wall, /HOMEPAGE_UNLOCK_ACCESS/);
    assert.match(wall, /UnlockAccountModal/);
    assert.match(wall, /startOrCheckout/);
    assert.doesNotMatch(wall, /accountLoginHref/);
    assert.match(
      copy,
      new RegExp(
        `SEARCH_UPCOMING_PAYWALL_LEAD =\\s*"${SEARCH_UPCOMING_PAYWALL_LEAD.replace(
          /[.*+?^${}()|[\]\\]/g,
          "\\$&",
        )}"`,
      ),
    );
  });
});
