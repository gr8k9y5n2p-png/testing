import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  BILLING_CREATE_ACCOUNT,
  BILLING_NOT_CONFIGURED,
  BILLING_SIGN_IN,
} from "./billing-copy.ts";
import {
  ACCOUNT_LOGIN_HREF,
  HOMEPAGE_LOGIN_HREF,
  accountLoginHref,
  unlockCtaPreview,
  unlockCtaStatus,
} from "./unlock-cta.ts";

describe("SoftWall unlock status", () => {
  it("redirects when Checkout returns a live URL", () => {
    const status = unlockCtaStatus(
      { url: "https://checkout.stripe.com/c/pay/cs_test_1", detail: "" },
      true,
    );
    assert.equal(status.kind, "redirect");
    assert.equal(status.detail, "");
  });

  it("asks unsigned visitors to sign in when checkout returns needs_account", () => {
    const status = unlockCtaStatus(
      { detail: BILLING_SIGN_IN, needsAccount: true },
      false,
    );
    assert.equal(status.kind, "sign_in");
    assert.equal(status.detail, BILLING_CREATE_ACCOUNT);
    assert.equal(HOMEPAGE_LOGIN_HREF, "/#account");
    assert.equal(ACCOUNT_LOGIN_HREF, "/account");
  });

  it("asks a signed-out visitor to sign in even without the needs_account flag", () => {
    const status = unlockCtaStatus(
      { detail: BILLING_NOT_CONFIGURED },
      false,
    );
    assert.equal(status.kind, "sign_in");
    assert.equal(status.detail, BILLING_CREATE_ACCOUNT);
  });

  it("surfaces Stripe / not-configured errors for a signed-in account", () => {
    const stripe = unlockCtaStatus(
      { detail: "No such price: price_missing" },
      true,
    );
    assert.equal(stripe.kind, "error");
    assert.equal(stripe.detail, "No such price: price_missing");

    const missing = unlockCtaStatus({ detail: "" }, true);
    assert.equal(missing.kind, "error");
    assert.equal(missing.detail, BILLING_NOT_CONFIGURED);
  });

  it("previews sign-in chrome for signed-out visitors before they click", () => {
    assert.deepEqual(unlockCtaPreview(false), {
      kind: "sign_in",
      detail: BILLING_CREATE_ACCOUNT,
    });
    assert.equal(unlockCtaPreview(true), null);
    assert.equal(accountLoginHref("/"), HOMEPAGE_LOGIN_HREF);
    assert.equal(accountLoginHref("/compare"), ACCOUNT_LOGIN_HREF);
  });
});
