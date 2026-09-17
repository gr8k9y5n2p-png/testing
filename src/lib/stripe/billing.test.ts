import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { createCustomerPortalSession } from "./billing.ts";
import { BILLING_NOT_CONFIGURED, BILLING_SIGN_IN } from "./billing-copy.ts";

const here = dirname(fileURLToPath(import.meta.url));

describe("Customer Portal", () => {
  it("soft-fails without STRIPE_SECRET_KEY", async () => {
    const prior = process.env.STRIPE_SECRET_KEY;
    delete process.env.STRIPE_SECRET_KEY;
    try {
      const { status, result } = await createCustomerPortalSession();
      assert.equal(status, 501);
      assert.equal(result.stub, true);
      assert.equal(result.detail, BILLING_NOT_CONFIGURED);
      assert.match(result.return_url, /\/account$/);
    } finally {
      if (prior == null) delete process.env.STRIPE_SECRET_KEY;
      else process.env.STRIPE_SECRET_KEY = prior;
    }
  });

  it("requires an Account session when keys are present", async () => {
    const prior = process.env.STRIPE_SECRET_KEY;
    process.env.STRIPE_SECRET_KEY = "sk_test_dummy_not_a_real_key";
    try {
      const { status, result } = await createCustomerPortalSession(
        new Request("http://localhost/api/billing/portal", { method: "POST" }),
      );
      assert.equal(status, 401);
      assert.equal(result.needs_account, true);
      assert.equal(result.detail, BILLING_SIGN_IN);
    } finally {
      if (prior == null) delete process.env.STRIPE_SECRET_KEY;
      else process.env.STRIPE_SECRET_KEY = prior;
    }
  });

  it("documents cancel-at-period-end and does not invent keys", () => {
    const copy = readFileSync(join(here, "billing-copy.ts"), "utf8");
    const billing = readFileSync(join(here, "billing.ts"), "utf8");
    assert.match(copy, /Cancel anytime in the Customer Portal/);
    assert.match(copy, /period end/);
    assert.doesNotMatch(billing, /sk_live_|pk_live_/);
    assert.match(billing, /billingPortal\.sessions\.create/);
  });
});
