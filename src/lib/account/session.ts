/**
 * Account identity stub.
 *
 * Auth is not implemented. Friends-beta (`aftertax_friends_beta`) is a shared
 * password gate — not a user id. Saved assets are scoped to this cookie:
 *
 *   aftertax_account = acct_stub_<uuid>
 *
 * Issued on the first `/api/saved-assets` request if missing. Same browser
 * keeps the same id (httpOnly, 400 days). This is the signed-in account path
 * until Stripe Checkout identity exists.
 *
 * Stripe Checkout later (Eric / website billing — do not implement here):
 * 1. When creating a Checkout Session, set `client_reference_id` to the
 *    current cookie accountId (or mint one and Set-Cookie before redirect).
 * 2. On Checkout success / webhook, persist Stripe `customer` (`cus_…`) as
 *    the canonical accountId, or store it beside the stub id and switch the
 *    cookie to `acct_<customer>` / `cus_…`.
 * 3. Saved lists and portfolios stay keyed by `accountId` — linking the stub
 *    id to the Stripe customer keeps existing assets.
 * 4. Soft-wall / Checkout stay off. Do not gate Save/Open on billing.
 */

export const ACCOUNT_COOKIE = "aftertax_account";
export const ACCOUNT_COOKIE_MAX_AGE_SEC = 400 * 24 * 60 * 60;
export const ACCOUNT_ID_PREFIX = "acct_stub_";

const ACCOUNT_ID_RE = /^acct_stub_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const STRIPE_CUSTOMER_RE = /^cus_[A-Za-z0-9]+$/;

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

export function readAccountIdFromRequest(request: Request): string | null {
  const raw = readCookie(request.headers.get("cookie"), ACCOUNT_COOKIE);
  return isAccountId(raw) ? raw : null;
}

export type ResolvedAccount = {
  accountId: string;
  issued: boolean;
};

export function resolveAccountSession(request: Request): ResolvedAccount {
  const existing = readAccountIdFromRequest(request);
  if (existing) return { accountId: existing, issued: false };
  return { accountId: newAccountId(), issued: true };
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
    `${ACCOUNT_COOKIE}=${encodeURIComponent(accountId)}`,
    "Path=/",
    "HttpOnly",
    "SameSite=Lax",
    `Max-Age=${options.maxAge}`,
  ];
  if (options.secure) parts.push("Secure");
  return parts.join("; ");
}

export function isHttpsRequest(request: Request): boolean {
  try {
    return new URL(request.url).protocol === "https:";
  } catch {
    return false;
  }
}
