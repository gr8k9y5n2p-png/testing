import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  ACCOUNT_COOKIE,
  ACCOUNT_ID_PREFIX,
  isAccountId,
  newAccountId,
  readAccountIdFromRequest,
  readCookie,
  resolveAccountSession,
  serializeAccountCookie,
} from "./session.ts";

describe("account session stub", () => {
  it("mints acct_stub_ UUIDs and accepts Stripe customer ids later", () => {
    const id = newAccountId();
    assert.equal(id.startsWith(ACCOUNT_ID_PREFIX), true);
    assert.equal(isAccountId(id), true);
    assert.equal(isAccountId("cus_abc123XYZ"), true);
    assert.equal(isAccountId("acct_1UD66TRqA7bY5N5q"), false);
    assert.equal(isAccountId("not-an-id"), false);
  });

  it("reads the account cookie from a request", () => {
    const id = newAccountId();
    const request = new Request("http://localhost/api/saved-assets", {
      headers: { cookie: `${ACCOUNT_COOKIE}=${id}; other=1` },
    });
    assert.equal(readAccountIdFromRequest(request), id);
    assert.equal(readCookie("a=1; b=two", "b"), "two");
  });

  it("issues a new account id when the cookie is missing", () => {
    const request = new Request("http://localhost/api/saved-assets");
    const first = resolveAccountSession(request);
    assert.equal(first.issued, true);
    assert.equal(isAccountId(first.accountId), true);

    const withCookie = new Request("http://localhost/api/saved-assets", {
      headers: { cookie: serializeAccountCookie(first.accountId, false) },
    });
    const again = resolveAccountSession(withCookie);
    assert.equal(again.issued, false);
    assert.equal(again.accountId, first.accountId);
  });
});
