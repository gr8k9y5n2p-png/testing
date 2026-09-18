import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

function read(relative: string): string {
  return readFileSync(join(here, relative), "utf8");
}

describe("Unlock Access create-account modal", () => {
  it("defaults the Unlock popup to Create account with a Sign in path", () => {
    const modal = read("UnlockAccountModal.tsx");
    const form = read("AccountAuthForm.tsx");
    assert.match(modal, /role="dialog"/);
    assert.match(modal, /aria-modal="true"/);
    assert.match(modal, /font-serif/);
    assert.match(modal, /bg-surface/);
    assert.match(modal, /ACCOUNT_SIGN_UP/);
    assert.match(modal, /ACCOUNT_UNLOCK_DETAIL/);
    assert.match(modal, /COPY\.paywallPrice/);
    assert.match(form, /variant === "unlock"/);
    assert.match(form, /initialAction/);
    assert.match(form, /ACCOUNT_HAVE_ACCOUNT/);
    assert.match(form, /ACCOUNT_NEED_ACCOUNT/);
    assert.match(form, /new-password/);
  });

  it("continues into POST /api/checkout after create or sign-in", () => {
    const modal = read("UnlockAccountModal.tsx");
    const wall = read("paywall/SoftWall.tsx");
    const menu = read("ManageBillingButton.tsx");
    const checkout = read("../lib/stripe/client-actions.ts");
    const billingCopy = read("../lib/stripe/billing-copy.ts");
    assert.match(modal, /if \(!signedIn\) \{/);
    assert.match(modal, /setModalOpen\(true\)/);
    assert.match(modal, /billing\.unlock\(\)/);
    assert.match(modal, /finally \{\s*setBusy\(false\)/);
    assert.match(wall, /onAuthenticated=\{continueAfterAuth\}/);
    assert.match(menu, /onAuthenticated=\{continueAfterAuth\}/);
    assert.match(checkout, /CHECKOUT_API_PATH/);
    assert.match(billingCopy, /CHECKOUT_API_PATH = "\/api\/checkout"/);
  });
});
