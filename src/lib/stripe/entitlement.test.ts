import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { FREEMIUM_COOKIE } from "../billing/limits.ts";
import { MemoryAccountStore } from "../account/store.ts";
import { hashPassword } from "../account/passwords.ts";
import {
  entitlementFrom,
  parseDeviceUsageCookie,
  serializeUsageCookie,
} from "./entitlement.ts";

describe("billing entitlement", () => {
  it("reads and writes the device usage cookie", () => {
    const cookie = serializeUsageCookie(
      { searches: 4, compareKeys: ["AGTHX"], portfolioKeys: [] },
      false,
    );
    assert.match(cookie, new RegExp(FREEMIUM_COOKIE));
    const usage = parseDeviceUsageCookie(cookie);
    assert.equal(usage.searches, 4);
    assert.deepEqual(usage.compareKeys, ["AGTHX"]);
  });

  it("does not raise walls for a subscribed account", async () => {
    const store = new MemoryAccountStore();
    const account = await store.create({
      email: "ada@aftertax.com",
      passwordHash: hashPassword("wholesaler"),
    });
    await store.updateBilling(account.id, {
      subscriptionStatus: "active",
      usage: {
        searches: 40,
        compareKeys: ["a", "b", "c"],
        portfolioKeys: ["1", "2", "3"],
      },
    });
    const row = await store.findById(account.id);
    const entitlement = entitlementFrom(row, {
      searches: 10,
      compareKeys: [],
      portfolioKeys: [],
    });
    assert.equal(entitlement.subscribed, true);
    assert.deepEqual(entitlement.walls, {
      search: false,
      compare: false,
      portfolio: false,
      lists: false,
      highlights: false,
      upcoming: false,
    });
  });

  it("raises the search wall after 5 anonymous loads", () => {
    const entitlement = entitlementFrom(null, {
      searches: 5,
      compareKeys: [],
      portfolioKeys: [],
    });
    assert.equal(entitlement.walls.search, true);
    assert.equal(entitlement.remaining.searches, 0);
    assert.equal(entitlement.signedIn, false);
  });

  it("walls Lists for freemium / signed-out / not entitled, never for subscribers", () => {
    const signedOut = entitlementFrom(null, {
      searches: 0,
      compareKeys: [],
      portfolioKeys: [],
    });
    assert.equal(signedOut.walls.lists, true);
    assert.equal(signedOut.walls.highlights, true);
    assert.equal(signedOut.walls.upcoming, true);
    assert.equal(signedOut.walls.search, false);
    assert.equal(signedOut.subscribed, false);

    const bypass = entitlementFrom(
      null,
      { searches: 0, compareKeys: [], portfolioKeys: [] },
      { NEXT_PUBLIC_FREEMIUM_DISABLED: "true" },
    );
    assert.equal(bypass.walls.lists, false);
    assert.equal(bypass.walls.highlights, false);
    assert.equal(bypass.walls.upcoming, false);
    assert.equal(bypass.bypass, true);
  });
});
