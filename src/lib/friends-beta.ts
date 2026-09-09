/**
 * Friends-beta password gate.
 *
 * Enable by setting FRIENDS_BETA_PASSWORD (or BETA_PASSWORD) in the
 * environment — Vercel Production → Settings → Environment Variables.
 * Unset the var to take the gate off when going public.
 *
 * This is a cheap shared-password lock for the app UI. It is not an
 * account system. Same-origin /api mocks and Render Data API calls
 * are not gated.
 */

import { createHash, createHmac, timingSafeEqual } from "node:crypto";

export const FRIENDS_BETA_COOKIE = "aftertax_friends_beta";
export const FRIENDS_BETA_COOKIE_MAX_AGE_SEC = 14 * 24 * 60 * 60;
export const FRIENDS_BETA_PATH = "/beta";

const SESSION_PAYLOAD = "aftertax.friends-beta.v1";

const PUBLIC_EXACT = new Set([
  FRIENDS_BETA_PATH,
  "/terms",
  "/privacy",
  "/robots.txt",
]);

export function friendsBetaPassword(
  env: NodeJS.ProcessEnv = process.env,
): string | null {
  const raw = env.FRIENDS_BETA_PASSWORD ?? env.BETA_PASSWORD;
  const trimmed = raw?.trim() ?? "";
  return trimmed.length > 0 ? trimmed : null;
}

export function isFriendsBetaGateEnabled(
  env: NodeJS.ProcessEnv = process.env,
): boolean {
  return friendsBetaPassword(env) !== null;
}

export function friendsBetaSessionToken(password: string): string {
  return createHmac("sha256", password).update(SESSION_PAYLOAD).digest("hex");
}

export function isFriendsBetaSessionValid(
  cookie: string | undefined,
  password: string,
): boolean {
  if (!cookie) return false;
  const expected = friendsBetaSessionToken(password);
  const provided = Buffer.from(cookie);
  const wanted = Buffer.from(expected);
  if (provided.length !== wanted.length) return false;
  return timingSafeEqual(provided, wanted);
}

export function passwordsMatch(provided: string, expected: string): boolean {
  const a = createHash("sha256").update(provided).digest();
  const b = createHash("sha256").update(expected).digest();
  return timingSafeEqual(a, b);
}

export function isFriendsBetaPublicPath(pathname: string): boolean {
  if (PUBLIC_EXACT.has(pathname)) return true;
  if (pathname.startsWith("/api/")) return true;
  if (pathname.startsWith("/_next/")) return true;
  return false;
}

/** Only same-origin relative paths. Reject protocol-relative // hosts. */
export function safeNextPath(value: string | null | undefined): string {
  if (!value) return "/";
  if (!value.startsWith("/") || value.startsWith("//")) return "/";
  if (value === FRIENDS_BETA_PATH || value.startsWith(`${FRIENDS_BETA_PATH}?`)) {
    return "/";
  }
  return value;
}

export type FriendsBetaGateDecision =
  | { action: "next" }
  | { action: "home" }
  | { action: "redirect"; next: string };

export function friendsBetaGateDecision(input: {
  password: string | null;
  pathname: string;
  search?: string;
  cookie?: string;
}): FriendsBetaGateDecision {
  if (!input.password) {
    if (input.pathname === FRIENDS_BETA_PATH) return { action: "home" };
    return { action: "next" };
  }
  if (isFriendsBetaPublicPath(input.pathname)) return { action: "next" };
  if (isFriendsBetaSessionValid(input.cookie, input.password)) {
    return { action: "next" };
  }
  const next = `${input.pathname}${input.search ?? ""}`;
  return { action: "redirect", next: safeNextPath(next) };
}

export function friendsBetaCookieOptions(secure: boolean): {
  httpOnly: true;
  sameSite: "lax";
  secure: boolean;
  path: "/";
  maxAge: number;
} {
  return {
    httpOnly: true,
    sameSite: "lax",
    secure,
    path: "/",
    maxAge: FRIENDS_BETA_COOKIE_MAX_AGE_SEC,
  };
}
