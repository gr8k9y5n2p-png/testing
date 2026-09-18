import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { serializeAccountCookie } from "../account/session.ts";
import { hashPassword } from "../account/passwords.ts";
import { createCheckoutSession } from "./checkout.ts";
import { BILLING_NOT_CONFIGURED, BILLING_SIGN_IN } from "./billing-copy.ts";

const here = dirname(fileURLToPath(import.meta.url));

describe("Checkout Session", () => {
  it("soft-fails without STRIPE_SECRET_KEY and does not invent keys", async () => {
    const prior = process.env.STRIPE_SECRET_KEY;
    delete process.env.STRIPE_SECRET_KEY;
    try {
      const { result, status } = await createCheckoutSession();
      assert.equal(status, 501);
      assert.equal(result.stub, true);
      assert.equal(result.detail, BILLING_NOT_CONFIGURED);
      assert.equal(result.price_id, "price_1UD6C0RqA7bY5N5qVleZso0d");
      assert.match(result.success_url, /checkout=success/);
      assert.match(result.cancel_url, /checkout=cancel/);
    } finally {
      if (prior == null) delete process.env.STRIPE_SECRET_KEY;
      else process.env.STRIPE_SECRET_KEY = prior;
    }
  });

  it("asks unsigned visitors to sign in when keys are present", async () => {
    const prior = process.env.STRIPE_SECRET_KEY;
    process.env.STRIPE_SECRET_KEY = "sk_test_dummy_not_a_real_key";
    try {
      const { result, status } = await createCheckoutSession(
        new Request("http://localhost/api/checkout", { method: "POST" }),
      );
      assert.equal(status, 401);
      assert.equal(result.stub, true);
      assert.equal(result.needs_account, true);
      assert.equal(result.detail, BILLING_SIGN_IN);
    } finally {
      if (prior == null) delete process.env.STRIPE_SECRET_KEY;
      else process.env.STRIPE_SECRET_KEY = prior;
    }
  });

  it("soft-fails a signed-in account when the dummy key is rejected", async () => {
    const prior = process.env.STRIPE_SECRET_KEY;
    const priorPath = process.env.AFTERTAX_ACCOUNTS_PATH;
    process.env.STRIPE_SECRET_KEY = "sk_test_dummy_not_a_real_key";
    const { mkdtempSync } = await import("node:fs");
    const { tmpdir } = await import("node:os");
    const { join } = await import("node:path");
    process.env.AFTERTAX_ACCOUNTS_PATH = join(
      mkdtempSync(join(tmpdir(), "aftertax-accounts-")),
      "accounts.json",
    );
    const { getAccountStore, resetAccountStoreForTests } = await import(
      "../account/store.ts"
    );
    resetAccountStoreForTests();
    const store = getAccountStore();
    const row = await store.create({
      email: "ada@aftertax.com",
      passwordHash: hashPassword("wholesaler"),
    });
    try {
      const { result, status } = await createCheckoutSession(
        new Request("http://localhost/api/checkout", {
          method: "POST",
          headers: { cookie: serializeAccountCookie(row.id, false) },
        }),
      );
      assert.ok(status === 200 || status === 502);
      assert.ok(result.detail || result.url);
      assert.equal("stub" in result ? result.stub !== undefined : true, true);
    } finally {
      if (prior == null) delete process.env.STRIPE_SECRET_KEY;
      else process.env.STRIPE_SECRET_KEY = prior;
      if (priorPath == null) delete process.env.AFTERTAX_ACCOUNTS_PATH;
      else process.env.AFTERTAX_ACCOUNTS_PATH = priorPath;
      resetAccountStoreForTests();
    }
  });

  it("soft-fails when the account store throws instead of hanging", async () => {
    const prior = process.env.STRIPE_SECRET_KEY;
    process.env.STRIPE_SECRET_KEY = "sk_test_dummy_not_a_real_key";
    const { serializeAccountCookie } = await import("../account/session.ts");
    const { getAccountStore, resetAccountStoreForTests } = await import(
      "../account/store.ts"
    );
    resetAccountStoreForTests();
    const store = getAccountStore();
    const original = store.findById.bind(store);
    store.findById = async () => {
      throw new Error("Account storage timed out. Try again.");
    };
    try {
      const { result, status } = await createCheckoutSession(
        new Request("http://localhost/api/checkout", {
          method: "POST",
          headers: {
            cookie: serializeAccountCookie(
              "acct_11111111-1111-1111-1111-111111111111",
              false,
            ),
          },
        }),
      );
      assert.equal(status, 502);
      assert.equal(result.stub, true);
      assert.match(result.detail, /timed out/);
    } finally {
      store.findById = original;
      if (prior == null) delete process.env.STRIPE_SECRET_KEY;
      else process.env.STRIPE_SECRET_KEY = prior;
      resetAccountStoreForTests();
    }
  });

  it("never hard-codes a Stripe secret or publishable key", () => {
    const source = readFileSync(join(here, "checkout.ts"), "utf8");
    assert.doesNotMatch(source, /sk_live_|sk_test_[A-Za-z0-9]{10,}|pk_live_|pk_test_[A-Za-z0-9]{10,}/);
    assert.match(source, /mode: "subscription"/);
    assert.doesNotMatch(source, /payment_method_types/);
  });
});
