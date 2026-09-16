import {
  hashPassword,
  isEmail,
  normalizeEmail,
  passwordIsStrong,
  validatePassword,
  verifyPassword,
} from "./passwords.ts";
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
