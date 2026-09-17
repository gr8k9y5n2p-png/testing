/**
 * Account session (email/password).
 *
 * Friends-beta (`aftertax_friends_beta`) is a shared site password — not a
 * user id. Saved assets require this signed httpOnly cookie:
 *
 *   aftertax_account = <accountId>.<hmac>
 *
 * Issued on sign-up / sign-in only. Not minted anonymously.
 *
 * Stripe Checkout links `stripeCustomerId` on the same account email
 * (`cus_…`). Do not gate Save/Open on Checkout. Soft-wall is usage-based.
 */

import { createHmac, timingSafeEqual } from "node:crypto";

export const ACCOUNT_COOKIE = "aftertax_account";
export const ACCOUNT_COOKIE_MAX_AGE_SEC = 400 * 24 * 60 * 60;
export const ACCOUNT_ID_PREFIX = "acct_";

const ACCOUNT_ID_RE = /^acct_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const STRIPE_CUSTOMER_RE = /^cus_[A-Za-z0-9]+$/;

export function accountSessionSecret(
  env: NodeJS.ProcessEnv = process.env,
): string {
  const pinned = env.AFTERTAX_ACCOUNT_SECRET?.trim();
  if (pinned) return pinned;
  return "aftertax-dev-account-secret";
}

export function newAccountId(): string {
  return `${ACCOUNT_ID_PREFIX}${crypto.randomUUID()}`;
}

export function isAccountId(value: string | null | undefined): value is string {
  if (!value) return false;
  return ACCOUNT_ID_RE.test(value) || STRIPE_CUSTOMER_RE.test(value);
}

export function readCookie(header: string | null | undefined, name: string): string | null {
  if (!header) return null;
  for (const part of header.split(";")) {
    const trimmed = part.trim();
    const eq = trimmed.indexOf("=");
    if (eq <= 0) continue;
    if (trimmed.slice(0, eq) !== name) continue;
    return decodeURIComponent(trimmed.slice(eq + 1));
  }
  return null;
}

export function signAccountId(
  accountId: string,
  secret: string = accountSessionSecret(),
): string {
  const mac = createHmac("sha256", secret).update(accountId).digest("hex");
  return `${accountId}.${mac}`;
}

export function verifyAccountCookie(
  raw: string | null | undefined,
  secret: string = accountSessionSecret(),
): string | null {
  if (!raw) return null;
  const dot = raw.lastIndexOf(".");
  if (dot <= 0) return null;
  const accountId = raw.slice(0, dot);
  const mac = raw.slice(dot + 1);
  if (!isAccountId(accountId) || !mac) return null;
  const expected = createHmac("sha256", secret).update(accountId).digest("hex");
  const a = Buffer.from(mac);
  const b = Buffer.from(expected);
  if (a.length !== b.length) return null;
  if (!timingSafeEqual(a, b)) return null;
  return accountId;
}

export function readAccountIdFromRequest(request: Request): string | null {
  const raw = readCookie(request.headers.get("cookie"), ACCOUNT_COOKIE);
  return verifyAccountCookie(raw);
}

export type ResolvedAccount = {
  accountId: string;
  issued: boolean;
};

/** Signed-in account only. Missing / invalid cookie → null (API returns 401). */
export function resolveAccountSession(request: Request): ResolvedAccount | null {
  const existing = readAccountIdFromRequest(request);
  if (!existing) return null;
  return { accountId: existing, issued: false };
}

export function accountCookieOptions(secure: boolean): {
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
    maxAge: ACCOUNT_COOKIE_MAX_AGE_SEC,
  };
}

export function serializeAccountCookie(accountId: string, secure: boolean): string {
  const options = accountCookieOptions(secure);
  const parts = [
    `${ACCOUNT_COOKIE}=${encodeURIComponent(signAccountId(accountId))}`,
    "Path=/",
    "HttpOnly",
    "SameSite=Lax",
    `Max-Age=${options.maxAge}`,
  ];
  if (options.secure) parts.push("Secure");
  return parts.join("; ");
}

export function serializeClearedAccountCookie(secure: boolean): string {
  const parts = [
    `${ACCOUNT_COOKIE}=`,
    "Path=/",
    "HttpOnly",
    "SameSite=Lax",
    "Max-Age=0",
  ];
  if (secure) parts.push("Secure");
  return parts.join("; ");
}

export function isHttpsRequest(request: Request): boolean {
  const forwarded = request.headers.get("x-forwarded-proto");
  if (forwarded) {
    return forwarded.split(",")[0]?.trim() === "https";
  }
  try {
    return new URL(request.url).protocol === "https:";
  } catch {
    return false;
  }
}
