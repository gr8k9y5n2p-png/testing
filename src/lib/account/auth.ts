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
import {
  PASSWORD_RESET_TTL_MS,
  passwordResetUrl,
  passwordResetUserDetail,
  resetEmailConfigured,
  resetLinkOrigin,
  sendPasswordResetEmail,
} from "./mail.ts";
import type { AccountStore, PublicAccount } from "./store.ts";
import {
  ACCOUNT_EMAIL_EXISTS,
  ACCOUNT_NOT_DURABLE,
  toPublicAccount,
} from "./store.ts";

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
    throw new AccountAuthError(409, ACCOUNT_EMAIL_EXISTS);
  }
  try {
    await store.create({
      email,
      passwordHash: hashPassword(password),
    });
  } catch (error) {
    if (error instanceof Error && error.message === ACCOUNT_EMAIL_EXISTS) {
      throw new AccountAuthError(409, ACCOUNT_EMAIL_EXISTS);
    }
    if (error instanceof Error && error.message === ACCOUNT_NOT_DURABLE) {
      throw new AccountAuthError(503, ACCOUNT_NOT_DURABLE);
    }
    throw error;
  }
  const persisted = await store.findByEmail(email);
  if (!persisted) {
    throw new AccountAuthError(503, ACCOUNT_NOT_DURABLE);
  }
  return toPublicAccount(persisted);
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

export const PASSWORD_RESET_REQUESTED = passwordResetUserDetail(true);
export const PASSWORD_RESET_MAIL_UNAVAILABLE = passwordResetUserDetail(false);

export async function requestPasswordReset(
  store: AccountStore,
  body: unknown,
  options: {
    origin?: string;
    env?: NodeJS.ProcessEnv;
    sendMail?: typeof sendPasswordResetEmail;
  } = {},
): Promise<{ ok: true; detail: string; mailConfigured: boolean }> {
  if (!body || typeof body !== "object") {
    throw new AccountAuthError(400, "Invalid JSON body.");
  }
  const email = normalizeEmail((body as { email?: unknown }).email);
  if (!isEmail(email)) {
    throw new AccountAuthError(400, "Enter a valid email.");
  }
  const env = options.env ?? process.env;
  const configured = resetEmailConfigured(env);
  const row = await store.findByEmail(email);
  const token = newPasswordResetToken();
  const tokenHash = hashPasswordResetToken(token);
  if (row) {
    const expiresAt = new Date(Date.now() + PASSWORD_RESET_TTL_MS).toISOString();
    await store.setPasswordReset(row.id, tokenHash, expiresAt);
    const origin = resetLinkOrigin(env, options.origin);
    const sendMail = options.sendMail ?? sendPasswordResetEmail;
    await sendMail({ to: row.email, resetUrl: passwordResetUrl(origin, token) }, env);
  }
  return {
    ok: true,
    detail: passwordResetUserDetail(configured),
    mailConfigured: configured,
  };
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
