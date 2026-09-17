import assert from "node:assert/strict";
import { describe, it } from "node:test";
import Stripe from "stripe";
import { MemoryAccountStore } from "../account/store.ts";
import { hashPassword } from "../account/passwords.ts";
import { applyCheckoutCompleted, handleStripeWebhook } from "./webhook.ts";

describe("Stripe webhook", () => {
  it("soft-fails without webhook secret or secret key", async () => {
    const priorKey = process.env.STRIPE_SECRET_KEY;
    const priorSecret = process.env.STRIPE_WEBHOOK_SECRET;
    delete process.env.STRIPE_SECRET_KEY;
    delete process.env.STRIPE_WEBHOOK_SECRET;
    try {
      const { status, result } = await handleStripeWebhook(
        new Request("http://localhost/api/stripe/webhook", {
          method: "POST",
          body: "{}",
        }),
      );
      assert.equal(status, 501);
      assert.equal(result.stub, true);
      assert.equal(result.received, false);
    } finally {
      if (priorKey == null) delete process.env.STRIPE_SECRET_KEY;
      else process.env.STRIPE_SECRET_KEY = priorKey;
      if (priorSecret == null) delete process.env.STRIPE_WEBHOOK_SECRET;
      else process.env.STRIPE_WEBHOOK_SECRET = priorSecret;
    }
  });

  it("rejects a missing or invalid signature when configured", async () => {
    const priorKey = process.env.STRIPE_SECRET_KEY;
    const priorSecret = process.env.STRIPE_WEBHOOK_SECRET;
    process.env.STRIPE_SECRET_KEY = "sk_test_dummy_not_a_real_key";
    process.env.STRIPE_WEBHOOK_SECRET = "whsec_test_dummy";
    try {
      const missing = await handleStripeWebhook(
        new Request("http://localhost/api/stripe/webhook", {
          method: "POST",
          body: "{}",
        }),
      );
      assert.equal(missing.status, 400);
      const invalid = await handleStripeWebhook(
        new Request("http://localhost/api/stripe/webhook", {
          method: "POST",
          headers: { "stripe-signature": "t=1,v1=nope" },
          body: "{}",
        }),
      );
      assert.equal(invalid.status, 400);
    } finally {
      if (priorKey == null) delete process.env.STRIPE_SECRET_KEY;
      else process.env.STRIPE_SECRET_KEY = priorKey;
      if (priorSecret == null) delete process.env.STRIPE_WEBHOOK_SECRET;
      else process.env.STRIPE_WEBHOOK_SECRET = priorSecret;
    }
  });

  it("links a Customer and marks the account subscribed on checkout.session.completed", async () => {
    const store = new MemoryAccountStore();
    const account = await store.create({
      email: "ada@aftertax.com",
      passwordHash: hashPassword("wholesaler"),
    });
    await applyCheckoutCompleted(store, {
      id: "cs_test",
      object: "checkout.session",
      client_reference_id: account.id,
      metadata: { accountId: account.id },
      customer: "cus_linked",
      subscription: {
        id: "sub_live",
        object: "subscription",
        status: "active",
        cancel_at_period_end: false,
        cancel_at: null,
        customer: "cus_linked",
        metadata: { accountId: account.id },
        items: {
          object: "list",
          data: [
            {
              id: "si_1",
              object: "subscription_item",
              current_period_end: Math.floor(Date.now() / 1000) + 86400,
            },
          ],
        },
      },
    } as unknown as Stripe.Checkout.Session);

    const row = await store.findById(account.id);
    assert.equal(row?.stripeCustomerId, "cus_linked");
    assert.equal(row?.subscriptionStatus, "active");
    assert.equal(row?.stripeSubscriptionId, "sub_live");
  });

  it("can construct a signed test event header", () => {
    const payload = JSON.stringify({
      id: "evt_test",
      object: "event",
      type: "customer.subscription.deleted",
      data: { object: { id: "sub_x", customer: "cus_x", metadata: {} } },
    });
    const secret = "whsec_test_dummy";
    const header = Stripe.webhooks.generateTestHeaderString({ payload, secret });
    assert.match(header, /t=/);
    assert.match(header, /v1=/);
  });
});
