import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  FRIENDS_BETA_COOKIE,
  FRIENDS_BETA_PATH,
  friendsBetaCookieOptions,
  friendsBetaGateDecision,
  friendsBetaPassword,
  friendsBetaSessionToken,
  isFriendsBetaGateEnabled,
  isFriendsBetaPublicPath,
  isFriendsBetaSessionValid,
  passwordsMatch,
  safeNextPath,
} from "./friends-beta.ts";

describe("friends-beta password env", () => {
  it("enables when FRIENDS_BETA_PASSWORD is set", () => {
    assert.equal(
      friendsBetaPassword({ FRIENDS_BETA_PASSWORD: "friends-only" }),
      "friends-only",
    );
    assert.equal(
      isFriendsBetaGateEnabled({ FRIENDS_BETA_PASSWORD: "friends-only" }),
      true,
    );
  });

  it("accepts BETA_PASSWORD as an alias", () => {
    assert.equal(friendsBetaPassword({ BETA_PASSWORD: "alias" }), "alias");
  });

  it("prefers FRIENDS_BETA_PASSWORD when both are set", () => {
    assert.equal(
      friendsBetaPassword({
        FRIENDS_BETA_PASSWORD: "primary",
        BETA_PASSWORD: "alias",
      }),
      "primary",
    );
  });

  it("is off when the password is unset or blank", () => {
    assert.equal(friendsBetaPassword({}), null);
    assert.equal(friendsBetaPassword({ FRIENDS_BETA_PASSWORD: "   " }), null);
    assert.equal(isFriendsBetaGateEnabled({}), false);
  });
});

describe("friends-beta session", () => {
  it("accepts a token derived from the current password", () => {
    const token = friendsBetaSessionToken("secret");
    assert.equal(isFriendsBetaSessionValid(token, "secret"), true);
    assert.equal(isFriendsBetaSessionValid(token, "other"), false);
    assert.equal(isFriendsBetaSessionValid(undefined, "secret"), false);
    assert.equal(isFriendsBetaSessionValid("nope", "secret"), false);
  });

  it("compares submitted passwords without inventing a match", () => {
    assert.equal(passwordsMatch("secret", "secret"), true);
    assert.equal(passwordsMatch("wrong", "secret"), false);
    assert.equal(passwordsMatch("", "secret"), false);
  });

  it("sets an httpOnly cookie with a 14-day TTL", () => {
    const options = friendsBetaCookieOptions(true);
    assert.equal(options.httpOnly, true);
    assert.equal(options.sameSite, "lax");
    assert.equal(options.secure, true);
    assert.equal(options.path, "/");
    assert.equal(options.maxAge, 14 * 24 * 60 * 60);
    assert.equal(FRIENDS_BETA_COOKIE, "aftertax_friends_beta");
  });
});

describe("friends-beta public paths and next", () => {
  it("keeps legal pages, the gate, and /api mocks public", () => {
    assert.equal(isFriendsBetaPublicPath("/beta"), true);
    assert.equal(isFriendsBetaPublicPath("/terms"), true);
    assert.equal(isFriendsBetaPublicPath("/privacy"), true);
    assert.equal(isFriendsBetaPublicPath("/api/illustrate"), true);
    assert.equal(isFriendsBetaPublicPath("/api/illustrate/compare"), true);
    assert.equal(isFriendsBetaPublicPath("/"), false);
    assert.equal(isFriendsBetaPublicPath("/portfolio"), false);
    assert.equal(isFriendsBetaPublicPath("/compare"), false);
    assert.equal(isFriendsBetaPublicPath("/lists"), false);
  });

  it("rejects open redirects", () => {
    assert.equal(safeNextPath("//evil.example"), "/");
    assert.equal(safeNextPath("https://evil.example"), "/");
    assert.equal(safeNextPath("/beta"), "/");
    assert.equal(safeNextPath("/compare?tickers=AGTHX"), "/compare?tickers=AGTHX");
  });
});

describe("friends-beta gate decision", () => {
  it("is a no-op when the password env is unset", () => {
    assert.deepEqual(
      friendsBetaGateDecision({ password: null, pathname: "/" }),
      { action: "next" },
    );
  });

  it("sends leftover /beta visits home when the gate is off", () => {
    assert.deepEqual(
      friendsBetaGateDecision({ password: null, pathname: "/beta" }),
      { action: "home" },
    );
  });

  it("challenges home / Compare / Portfolios / Lists without a cookie", () => {
    for (const pathname of ["/", "/portfolio", "/compare", "/lists"]) {
      assert.deepEqual(
        friendsBetaGateDecision({ password: "secret", pathname }),
        { action: "redirect", next: pathname },
      );
    }
  });

  it("stays unlocked when the session cookie matches", () => {
    const cookie = friendsBetaSessionToken("secret");
    assert.deepEqual(
      friendsBetaGateDecision({
        password: "secret",
        pathname: "/",
        cookie,
      }),
      { action: "next" },
    );
  });

  it("does not challenge /api Data mocks or legal pages", () => {
    assert.deepEqual(
      friendsBetaGateDecision({
        password: "secret",
        pathname: "/api/illustrate",
      }),
      { action: "next" },
    );
    assert.deepEqual(
      friendsBetaGateDecision({ password: "secret", pathname: "/terms" }),
      { action: "next" },
    );
    assert.equal(FRIENDS_BETA_PATH, "/beta");
  });
});
