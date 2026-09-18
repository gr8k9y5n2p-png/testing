import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { BILLING_NOT_CONFIGURED, BILLING_SIGN_IN } from "./billing-copy.ts";
import {
  BILLING_FETCH_TIMEOUT_MESSAGE,
  startCheckout,
} from "./client-actions.ts";

describe("startCheckout client", () => {
  it("maps a 401 needs_account stub to sign-in copy", async () => {
    const prior = globalThis.fetch;
    globalThis.fetch = (async () =>
      new Response(
        JSON.stringify({
          stub: true,
          needs_account: true,
          detail: BILLING_SIGN_IN,
        }),
        { status: 401, headers: { "content-type": "application/json" } },
      )) as typeof fetch;
    try {
      const result = await startCheckout();
      assert.equal(result.needsAccount, true);
      assert.equal(result.detail, BILLING_SIGN_IN);
      assert.equal(result.url, undefined);
    } finally {
      globalThis.fetch = prior;
    }
  });

  it("returns a live Checkout URL when the server sends one", async () => {
    const prior = globalThis.fetch;
    globalThis.fetch = (async () =>
      new Response(
        JSON.stringify({
          stub: false,
          url: "https://checkout.stripe.com/c/pay/cs_test_1",
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      )) as typeof fetch;
    try {
      const result = await startCheckout();
      assert.equal(result.url, "https://checkout.stripe.com/c/pay/cs_test_1");
      assert.equal(result.configured, true);
    } finally {
      globalThis.fetch = prior;
    }
  });

  it("surfaces a timeout instead of hanging when fetch never settles", async () => {
    const prior = globalThis.fetch;
    const priorTimeout = AbortSignal.timeout;
    AbortSignal.timeout = ((ms: number) => {
      const controller = new AbortController();
      setTimeout(() => controller.abort(), Math.min(ms, 25));
      return controller.signal;
    }) as typeof AbortSignal.timeout;
    globalThis.fetch = ((input: RequestInfo | URL, init?: RequestInit) => {
      return new Promise((_resolve, reject) => {
        init?.signal?.addEventListener("abort", () => {
          reject(Object.assign(new Error("The operation was aborted"), { name: "AbortError" }));
        });
      });
    }) as typeof fetch;
    try {
      const result = await startCheckout();
      assert.equal(result.url, undefined);
      assert.ok(
        result.detail === BILLING_FETCH_TIMEOUT_MESSAGE ||
          result.detail === BILLING_NOT_CONFIGURED,
      );
    } finally {
      globalThis.fetch = prior;
      AbortSignal.timeout = priorTimeout;
    }
  });
});
