import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { signInAccount, signUpAccount, AccountAuthError } from "./auth.ts";
import {
  handleAccountMe,
  handleAccountSignIn,
  handleAccountSignOut,
  handleAccountSignUp,
} from "./http.ts";
import { MemoryAccountStore } from "./store.ts";
import { readAccountIdFromRequest } from "./session.ts";

describe("email/password account auth", () => {
  it("signs up, signs in, and reserves stripeCustomerId", async () => {
    const store = new MemoryAccountStore();
    const created = await signUpAccount(store, {
      email: "Ada@Example.com",
      password: "wholesaler",
    });
    assert.equal(created.email, "ada@example.com");
    assert.equal(created.stripeCustomerId, null);
    assert.match(created.id, /^acct_/);

    const signedIn = await signInAccount(store, {
      email: "ada@example.com",
      password: "wholesaler",
    });
    assert.equal(signedIn.id, created.id);

    await assert.rejects(
      () => signInAccount(store, { email: "ada@example.com", password: "wrong-password" }),
      (error: unknown) => error instanceof AccountAuthError && error.status === 401,
    );
    await assert.rejects(
      () => signUpAccount(store, { email: "ada@example.com", password: "wholesaler" }),
      (error: unknown) => error instanceof AccountAuthError && error.status === 409,
    );
  });

  it("HTTP signup sets a session cookie; another user cannot see that account", async () => {
    const store = new MemoryAccountStore();
    const signup = await handleAccountSignUp(
      new Request("http://localhost/api/account/signup", {
        method: "POST",
        body: JSON.stringify({ email: "a@aftertax.com", password: "password1" }),
      }),
      store,
    );
    assert.equal(signup.status, 201);
    const cookie = signup.headers.get("set-cookie");
    assert.match(cookie ?? "", /aftertax_account=/);
    const me = await handleAccountMe(
      new Request("http://localhost/api/account/me", {
        headers: { cookie: cookie?.split(";", 1)[0] ?? "" },
      }),
      store,
    );
    const mine = (await me.json()) as { account: { email: string } | null };
    assert.equal(mine.account?.email, "a@aftertax.com");

    const other = await handleAccountSignUp(
      new Request("http://localhost/api/account/signup", {
        method: "POST",
        body: JSON.stringify({ email: "b@aftertax.com", password: "password1" }),
      }),
      store,
    );
    const otherCookie = other.headers.get("set-cookie")?.split(";", 1)[0] ?? "";
    const otherId = readAccountIdFromRequest(
      new Request("http://localhost/api/account/me", {
        headers: { cookie: otherCookie },
      }),
    );
    const aId = readAccountIdFromRequest(
      new Request("http://localhost/api/account/me", {
        headers: { cookie: cookie?.split(";", 1)[0] ?? "" },
      }),
    );
    assert.notEqual(aId, otherId);

    const signedOut = await handleAccountSignOut(
      new Request("http://localhost/api/account/signout", { method: "POST" }),
    );
    assert.equal(signedOut.status, 200);
    assert.match(signedOut.headers.get("set-cookie") ?? "", /Max-Age=0/);

    const signin = await handleAccountSignIn(
      new Request("http://localhost/api/account/signin", {
        method: "POST",
        body: JSON.stringify({ email: "a@aftertax.com", password: "password1" }),
      }),
      store,
    );
    assert.equal(signin.status, 200);
  });
});
