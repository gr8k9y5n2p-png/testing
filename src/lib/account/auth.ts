import {
  hashPassword,
  hashPasswordResetToken,
  isEmail,
  isPasswordResetToken,
  newPasswordResetToken,
  normalizeEmail,
  passwordIsStrong,
  validatePassword,
  verifyPassword,
} from "./passwords.ts";
import { PASSWORD_RESET_TTL_MS, passwordResetUrl, sendPasswordResetEmail } from "./mail.ts";
import { publicOrigin } from "../hosts.ts";
import { CONTACT_EMAIL } from "../legal-copy.ts";
import type { AccountStore, PublicAccount } from "./store.ts";
import { toPublicAccount } from "./store.ts";

export class AccountAuthError extends Error {
  readonly status: number;
  readonly detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

export async function signUpAccount(
  store: AccountStore,
  body: unknown,
): Promise<PublicAccount> {
  const { email, password } = readCredentials(body);
  if (await store.findByEmail(email)) {
    throw new AccountAuthError(409, "An account with that email already exists.");
  }
  const row = await store.create({
    email,
    passwordHash: hashPassword(password),
  });
  return toPublicAccount(row);
}

export async function signInAccount(
  store: AccountStore,
  body: unknown,
): Promise<PublicAccount> {
  const { email, password } = readCredentials(body);
  const row = await store.findByEmail(email);
  if (!row || !verifyPassword(password, row.passwordHash)) {
    throw new AccountAuthError(401, "Email or password is wrong.");
  }
  return toPublicAccount(row);
}

export const PASSWORD_RESET_REQUESTED = `If an account exists for that email, we sent a reset link. Check your email. If a message does not arrive, contact ${CONTACT_EMAIL}.`;

export async function requestPasswordReset(
  store: AccountStore,
  body: unknown,
  options: {
    origin?: string;
    sendMail?: typeof sendPasswordResetEmail;
  } = {},
): Promise<{ ok: true; detail: string }> {
  if (!body || typeof body !== "object") {
    throw new AccountAuthError(400, "Invalid JSON body.");
  }
  const email = normalizeEmail((body as { email?: unknown }).email);
  if (!isEmail(email)) {
    throw new AccountAuthError(400, "Enter a valid email.");
  }
  const row = await store.findByEmail(email);
  if (row) {
    const token = newPasswordResetToken();
    const expiresAt = new Date(Date.now() + PASSWORD_RESET_TTL_MS).toISOString();
    await store.setPasswordReset(row.id, hashPasswordResetToken(token), expiresAt);
    const origin = options.origin ?? publicOrigin();
    const sendMail = options.sendMail ?? sendPasswordResetEmail;
    await sendMail({ to: row.email, resetUrl: passwordResetUrl(origin, token) });
  }
  return { ok: true, detail: PASSWORD_RESET_REQUESTED };
}

export async function resetAccountPassword(
  store: AccountStore,
  body: unknown,
): Promise<PublicAccount> {
  if (!body || typeof body !== "object") {
    throw new AccountAuthError(400, "Invalid JSON body.");
  }
  const raw = body as { token?: unknown; password?: unknown };
  const token = typeof raw.token === "string" ? raw.token.trim() : "";
  const password = validatePassword(raw.password);
  if (!isPasswordResetToken(token)) {
    throw new AccountAuthError(400, "This reset link is invalid or has expired.");
  }
  if (!passwordIsStrong(password)) {
    throw new AccountAuthError(400, "Password must be at least 8 characters.");
  }
  const row = await store.consumePasswordReset(
    hashPasswordResetToken(token),
    hashPassword(password),
  );
  if (!row) {
    throw new AccountAuthError(400, "This reset link is invalid or has expired.");
  }
  return toPublicAccount(row);
}

function readCredentials(body: unknown): { email: string; password: string } {
  if (!body || typeof body !== "object") {
    throw new AccountAuthError(400, "Invalid JSON body.");
  }
  const raw = body as { email?: unknown; password?: unknown };
  const email = normalizeEmail(raw.email);
  const password = validatePassword(raw.password);
  if (!isEmail(email)) {
    throw new AccountAuthError(400, "Enter a valid email.");
  }
  if (!passwordIsStrong(password)) {
    throw new AccountAuthError(400, "Password must be at least 8 characters.");
  }
  return { email, password };
}
