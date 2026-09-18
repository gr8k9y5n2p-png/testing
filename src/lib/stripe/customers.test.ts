import assert from "node:assert/strict";
import { describe, it } from "node:test";
import type Stripe from "stripe";
import type { AccountRecord, AccountStore } from "../account/store.ts";
import { ensureStripeCustomer } from "./customers.ts";

function account(): AccountRecord {
  return {
    id: "acct_11111111-1111-1111-1111-111111111111",
    email: "ada@aftertax.com",
    passwordHash: "scrypt$n$r$p$salt$hash",
    stripeCustomerId: null,
    stripeSubscriptionId: null,
    subscriptionStatus: null,
    cancelAtPeriodEnd: false,
    currentPeriodEnd: null,
    usage: { searches: 0, compareKeys: [], portfolioKeys: [] },
    createdAt: "2026-01-01T00:00:00.000Z",
    updatedAt: "2026-01-01T00:00:00.000Z",
  };
}

describe("ensureStripeCustomer", () => {
  it("returns the Customer id when updateBilling throws", async () => {
    const stripe = {
      customers: {
        list: async () => ({ data: [] }),
        create: async () => ({ id: "cus_live_1" }),
      },
    };
    const store = {
      async updateBilling() {
        throw new Error("Account storage timed out. Try again.");
      },
    };
    const id = await ensureStripeCustomer(
      stripe as unknown as Stripe,
      store as unknown as AccountStore,
      account(),
    );
    assert.equal(id, "cus_live_1");
  });

  it("reuses an existing stripeCustomerId without calling Stripe", async () => {
    let listed = 0;
    const stripe = {
      customers: {
        list: async () => {
          listed += 1;
          return { data: [] };
        },
      },
    };
    const row = account();
    row.stripeCustomerId = "cus_existing";
    const id = await ensureStripeCustomer(
      stripe as unknown as Stripe,
      {} as AccountStore,
      row,
    );
    assert.equal(id, "cus_existing");
    assert.equal(listed, 0);
  });
});
