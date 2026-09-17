import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  ACCOUNT_COOKIE,
  ACCOUNT_ID_PREFIX,
  isAccountId,
  newAccountId,
  readAccountIdFromRequest,
  resolveAccountSession,
  isHttpsRequest,
  serializeAccountCookie,
  signAccountId,
  verifyAccountCookie,
} from "./session.ts";

describe("account session", () => {
  it("mints acct_ UUIDs and accepts Stripe customer ids later", () => {
    const id = newAccountId();
    assert.equal(id.startsWith(ACCOUNT_ID_PREFIX), true);
    assert.equal(isAccountId(id), true);
    assert.equal(isAccountId("cus_abc123XYZ"), true);
    assert.equal(isAccountId("acct_1UD66TRqA7bY5N5q"), false);
    assert.equal(isAccountId("not-an-id"), false);
  });

  it("signs and verifies the account cookie", () => {
    const id = newAccountId();
    const signed = signAccountId(id);
    assert.equal(verifyAccountCookie(signed), id);
    assert.equal(verifyAccountCookie(id), null);
    assert.equal(verifyAccountCookie(`${id}.deadbeef`), null);
  });

  it("reads the signed account cookie from a request", () => {
    const id = newAccountId();
    const request = new Request("http://localhost/api/saved-assets", {
      headers: { cookie: serializeAccountCookie(id, false) },
    });
    assert.equal(readAccountIdFromRequest(request), id);
    const session = resolveAccountSession(request);
    assert.equal(session?.accountId, id);
    assert.equal(session?.issued, false);
  });

  it("does not mint an anonymous session", () => {
    const request = new Request("http://localhost/api/saved-assets");
    assert.equal(resolveAccountSession(request), null);
    assert.match(serializeAccountCookie(newAccountId(), false), new RegExp(ACCOUNT_COOKIE));
  });

  it("sets Secure from x-forwarded-proto, not the internal http URL", () => {
    const request = new Request("http://127.0.0.1/api/account/me", {
      headers: { "x-forwarded-proto": "https, http" },
    });
    assert.equal(isHttpsRequest(request), true);
    assert.match(serializeAccountCookie(newAccountId(), true), /Secure/);
  });
});
