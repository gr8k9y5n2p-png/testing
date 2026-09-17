import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
  AccountAuthError,
  PASSWORD_RESET_MAIL_UNAVAILABLE,
  PASSWORD_RESET_REQUESTED,
  requestPasswordReset,
  resetAccountPassword,
  signInAccount,
  signUpAccount,
} from "./auth.ts";
import {
  handleAccountForgot,
  handleAccountMe,
  handleAccountReset,
  handleAccountSignIn,
  handleAccountSignOut,
  handleAccountSignUp,
} from "./http.ts";
import { JsonFileAccountStore, MemoryAccountStore } from "./store.ts";
import { hashPassword, hashPasswordResetToken, verifyPassword } from "./passwords.ts";
import { isHttpsRequest, readAccountIdFromRequest } from "./session.ts";

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

  it("does not treat the friends-beta shared password as an Account password", async () => {
    const store = new MemoryAccountStore();
    await signUpAccount(store, {
      email: "ada@example.com",
      password: "wholesaler",
    });
    await assert.rejects(
      () =>
        signInAccount(store, {
          email: "ada@example.com",
          password: "friends-beta-shared",
        }),
      (error: unknown) => error instanceof AccountAuthError && error.status === 401,
    );
    const signedIn = await signInAccount(store, {
      email: "ada@example.com",
      password: "wholesaler",
    });
    assert.equal(signedIn.email, "ada@example.com");
  });

  it("reloads the JSON account file so a later sign-in process can verify", async () => {
    const dir = mkdtempSync(join(tmpdir(), "aftertax-accounts-"));
    const filePath = join(dir, "accounts.json");
    const writer = new JsonFileAccountStore(filePath);
    await signUpAccount(writer, {
      email: "ada@example.com",
      password: "wholesaler",
    });
    const reader = new JsonFileAccountStore(filePath);
    const signedIn = await signInAccount(reader, {
      email: "ada@example.com",
      password: "wholesaler",
    });
    assert.equal(signedIn.email, "ada@example.com");
    assert.equal(verifyPassword("wholesaler", JSON.parse(readFileSync(filePath, "utf8"))[0].passwordHash), true);
  });

  it("skips account rows that lost their password hash instead of throwing", async () => {
    const dir = mkdtempSync(join(tmpdir(), "aftertax-accounts-"));
    const filePath = join(dir, "accounts.json");
    writeFileSync(
      filePath,
      `${JSON.stringify([
        {
          id: "acct_11111111-1111-1111-1111-111111111111",
          email: "ada@example.com",
          createdAt: "2026-01-01T00:00:00.000Z",
          updatedAt: "2026-01-01T00:00:00.000Z",
          stripeCustomerId: null,
        },
      ])}\n`,
    );
    const store = new JsonFileAccountStore(filePath);
    await assert.rejects(
      () => signInAccount(store, { email: "ada@example.com", password: "wholesaler" }),
      (error: unknown) => error instanceof AccountAuthError && error.status === 401,
    );
  });

  it("issues a reset token, then accepts the new password and rejects the old one", async () => {
    const store = new MemoryAccountStore();
    await signUpAccount(store, {
      email: "ada@example.com",
      password: "wholesaler",
    });
    let resetUrl = "";
    const result = await requestPasswordReset(
      store,
      { email: "Ada@Example.com" },
      {
        origin: "https://getaftertax.com",
        env: { RESEND_API_KEY: "re_test" },
        sendMail: async ({ resetUrl: url }) => {
          resetUrl = url;
          return { configured: true, sent: true };
        },
      },
    );
    assert.equal(result.detail, PASSWORD_RESET_REQUESTED);
    assert.equal(result.mailConfigured, true);
    assert.match(resetUrl, /^https:\/\/getaftertax\.com\/account\/reset\?token=/);
    const token = new URL(resetUrl).searchParams.get("token") ?? "";
    assert.match(token, /^[0-9a-f]{64}$/i);

    const unknown = await requestPasswordReset(
      store,
      { email: "missing@example.com" },
      {
        env: { RESEND_API_KEY: "re_test" },
        sendMail: async () => {
          throw new Error("must not send mail for an unknown email");
        },
      },
    );
    assert.equal(unknown.detail, PASSWORD_RESET_REQUESTED);
    assert.equal(unknown.mailConfigured, true);

    const reset = await resetAccountPassword(store, {
      token,
      password: "new-pass-9",
    });
    assert.equal(reset.email, "ada@example.com");
    await assert.rejects(
      () => signInAccount(store, { email: "ada@example.com", password: "wholesaler" }),
      (error: unknown) => error instanceof AccountAuthError && error.status === 401,
    );
    const signedIn = await signInAccount(store, {
      email: "ada@example.com",
      password: "new-pass-9",
    });
    assert.equal(signedIn.id, reset.id);
    await assert.rejects(
      () => resetAccountPassword(store, { token, password: "another-1" }),
      (error: unknown) => error instanceof AccountAuthError && error.status === 400,
    );
  });

  it("HTTP forgot is always 200 for a valid email; reset sets the session cookie", async () => {
    const store = new MemoryAccountStore();
    await handleAccountSignUp(
      new Request("http://localhost/api/account/signup", {
        method: "POST",
        body: JSON.stringify({ email: "ada@aftertax.com", password: "password1" }),
      }),
      store,
    );
    const row = await store.findByEmail("ada@aftertax.com");
    assert.ok(row);
    const token = "a".repeat(64);
    await store.setPasswordReset(
      row.id,
      hashPasswordResetToken(token),
      new Date(Date.now() + 60_000).toISOString(),
    );

    const forgot = await handleAccountForgot(
      new Request("http://localhost/api/account/forgot", {
        method: "POST",
        body: JSON.stringify({ email: "unknown@aftertax.com" }),
      }),
      store,
    );
    assert.equal(forgot.status, 200);
    const forgotBody = (await forgot.json()) as {
      detail: string;
      mailConfigured: boolean;
    };
    assert.equal(forgotBody.mailConfigured, Boolean(process.env.RESEND_API_KEY?.trim()));
    assert.equal(
      forgotBody.detail,
      forgotBody.mailConfigured
        ? PASSWORD_RESET_REQUESTED
        : PASSWORD_RESET_MAIL_UNAVAILABLE,
    );

    const reset = await handleAccountReset(
      new Request("https://staging.getaftertax.com/api/account/reset", {
        method: "POST",
        headers: { "x-forwarded-proto": "https" },
        body: JSON.stringify({ token, password: "password2" }),
      }),
      store,
    );
    assert.equal(reset.status, 200);
    assert.match(reset.headers.get("set-cookie") ?? "", /aftertax_account=/);
    assert.match(reset.headers.get("set-cookie") ?? "", /Secure/);
  });

  it("returns the same forgot copy for known and unknown emails when mail is off", async () => {
    const store = new MemoryAccountStore();
    await signUpAccount(store, {
      email: "ada@example.com",
      password: "wholesaler",
    });
    const known = await requestPasswordReset(
      store,
      { email: "ada@example.com" },
      { env: {} },
    );
    const unknown = await requestPasswordReset(
      store,
      { email: "missing@example.com" },
      { env: {} },
    );
    assert.equal(known.detail, unknown.detail);
    assert.equal(known.mailConfigured, false);
    assert.equal(known.detail, PASSWORD_RESET_MAIL_UNAVAILABLE);
    assert.doesNotMatch(known.detail, /we sent a reset link/);
  });

  it("hashes and verifies passwords without accepting a swapped hash", () => {
    const stored = hashPassword("wholesaler");
    assert.equal(verifyPassword("wholesaler", stored), true);
    assert.equal(verifyPassword("wholesalers", stored), false);
    assert.equal(verifyPassword("wholesaler", ""), false);
  });
});

describe("account HTTPS cookie", () => {
  it("trusts x-forwarded-proto so Secure is set behind the Vercel proxy", () => {
    const forwarded = new Request("http://127.0.0.1/api/account/signin", {
      headers: { "x-forwarded-proto": "https" },
    });
    assert.equal(isHttpsRequest(forwarded), true);
    const local = new Request("http://localhost/api/account/signin");
    assert.equal(isHttpsRequest(local), false);
  });
});
