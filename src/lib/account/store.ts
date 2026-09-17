/**
 * Email/password accounts. JSON file — same persistence pattern as
 * saved-assets. `stripeCustomerId` is reserved for later Checkout link
 * by email. Do not enable billing here.
 *
 * The file store reloads from disk on every read/write so sign-in and
 * sign-up (separate Vercel functions, or two Node processes on a shared
 * disk) see the same rows. In-memory-only snapshots made login look like
 * a wrong password after the creating instance went away.
 */

import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { timingSafeEqualHex } from "./passwords.ts";
import { newAccountId } from "./session.ts";

export type AccountRecord = {
  id: string;
  email: string;
  passwordHash: string;
  /** Reserved. Stripe Checkout later sets `cus_…` on this same email. */
  stripeCustomerId: string | null;
  createdAt: string;
  updatedAt: string;
  passwordResetTokenHash?: string | null;
  passwordResetExpiresAt?: string | null;
};

export type PublicAccount = {
  id: string;
  email: string;
  stripeCustomerId: string | null;
};

export function toPublicAccount(row: AccountRecord): PublicAccount {
  return {
    id: row.id,
    email: row.email,
    stripeCustomerId: row.stripeCustomerId,
  };
}

export interface AccountStore {
  findByEmail(email: string): Promise<AccountRecord | null>;
  findById(id: string): Promise<AccountRecord | null>;
  create(input: {
    email: string;
    passwordHash: string;
  }): Promise<AccountRecord>;
  updatePasswordHash(id: string, passwordHash: string): Promise<AccountRecord | null>;
  setPasswordReset(
    id: string,
    tokenHash: string,
    expiresAt: string,
  ): Promise<AccountRecord | null>;
  consumePasswordReset(
    tokenHash: string,
    passwordHash: string,
  ): Promise<AccountRecord | null>;
}

function emailKey(email: string): string {
  return email.trim().toLowerCase();
}

export class MemoryAccountStore implements AccountStore {
  protected records: AccountRecord[];

  constructor(records: AccountRecord[] = []) {
    this.records = records;
  }

  async findByEmail(email: string): Promise<AccountRecord | null> {
    const key = emailKey(email);
    return this.records.find((row) => row.email === key) ?? null;
  }

  async findById(id: string): Promise<AccountRecord | null> {
    return this.records.find((row) => row.id === id) ?? null;
  }

  async create(input: {
    email: string;
    passwordHash: string;
  }): Promise<AccountRecord> {
    const stamp = new Date().toISOString();
    const row: AccountRecord = {
      id: newAccountId(),
      email: emailKey(input.email),
      passwordHash: input.passwordHash,
      stripeCustomerId: null,
      createdAt: stamp,
      updatedAt: stamp,
      passwordResetTokenHash: null,
      passwordResetExpiresAt: null,
    };
    this.records.push(row);
    return row;
  }

  async updatePasswordHash(
    id: string,
    passwordHash: string,
  ): Promise<AccountRecord | null> {
    const row = await this.findById(id);
    if (!row) return null;
    row.passwordHash = passwordHash;
    row.passwordResetTokenHash = null;
    row.passwordResetExpiresAt = null;
    row.updatedAt = new Date().toISOString();
    return row;
  }

  async setPasswordReset(
    id: string,
    tokenHash: string,
    expiresAt: string,
  ): Promise<AccountRecord | null> {
    const row = await this.findById(id);
    if (!row) return null;
    row.passwordResetTokenHash = tokenHash;
    row.passwordResetExpiresAt = expiresAt;
    row.updatedAt = new Date().toISOString();
    return row;
  }

  async consumePasswordReset(
    tokenHash: string,
    passwordHash: string,
  ): Promise<AccountRecord | null> {
    const now = Date.now();
    for (const row of this.records) {
      if (!row.passwordResetTokenHash || !row.passwordResetExpiresAt) continue;
      if (!timingSafeEqualHex(tokenHash, row.passwordResetTokenHash)) continue;
      const expires = Date.parse(row.passwordResetExpiresAt);
      row.passwordResetTokenHash = null;
      row.passwordResetExpiresAt = null;
      row.updatedAt = new Date().toISOString();
      if (!Number.isFinite(expires) || expires < now) {
        return null;
      }
      row.passwordHash = passwordHash;
      return row;
    }
    return null;
  }
}

export function defaultAccountsPath(
  env: NodeJS.ProcessEnv = process.env,
): string {
  const pinned = env.AFTERTAX_ACCOUNTS_PATH?.trim();
  if (pinned) return pinned;
  if (env.VERCEL) return "/tmp/aftertax-accounts.json";
  return join(process.cwd(), ".data", "accounts.json");
}

export class JsonFileAccountStore extends MemoryAccountStore {
  private filePath: string;

  constructor(filePath: string) {
    super([]);
    this.filePath = filePath;
  }

  private hydrate() {
    this.records = loadAccounts(this.filePath);
  }

  private persist() {
    mkdirSync(dirname(this.filePath), { recursive: true });
    writeFileSync(this.filePath, `${JSON.stringify(this.records, null, 2)}\n`);
  }

  override async findByEmail(email: string): Promise<AccountRecord | null> {
    this.hydrate();
    return super.findByEmail(email);
  }

  override async findById(id: string): Promise<AccountRecord | null> {
    this.hydrate();
    return super.findById(id);
  }

  override async create(input: {
    email: string;
    passwordHash: string;
  }): Promise<AccountRecord> {
    this.hydrate();
    const row = await super.create(input);
    this.persist();
    return row;
  }

  override async updatePasswordHash(
    id: string,
    passwordHash: string,
  ): Promise<AccountRecord | null> {
    this.hydrate();
    const row = await super.updatePasswordHash(id, passwordHash);
    if (row) this.persist();
    return row;
  }

  override async setPasswordReset(
    id: string,
    tokenHash: string,
    expiresAt: string,
  ): Promise<AccountRecord | null> {
    this.hydrate();
    const row = await super.setPasswordReset(id, tokenHash, expiresAt);
    if (row) this.persist();
    return row;
  }

  override async consumePasswordReset(
    tokenHash: string,
    passwordHash: string,
  ): Promise<AccountRecord | null> {
    this.hydrate();
    const before = this.records.map((row) => ({
      id: row.id,
      passwordHash: row.passwordHash,
      passwordResetTokenHash: row.passwordResetTokenHash ?? null,
      updatedAt: row.updatedAt,
    }));
    const row = await super.consumePasswordReset(tokenHash, passwordHash);
    const changed = this.records.some((current, index) => {
      const previous = before[index];
      return (
        !previous ||
        current.passwordHash !== previous.passwordHash ||
        (current.passwordResetTokenHash ?? null) !== previous.passwordResetTokenHash ||
        current.updatedAt !== previous.updatedAt
      );
    });
    if (changed) this.persist();
    return row;
  }
}

function loadAccounts(filePath: string): AccountRecord[] {
  try {
    const parsed = JSON.parse(readFileSync(filePath, "utf8")) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(isAccountRecord);
  } catch {
    return [];
  }
}

function isAccountRecord(value: unknown): value is AccountRecord {
  if (!value || typeof value !== "object") return false;
  const row = value as AccountRecord;
  return (
    typeof row.id === "string" &&
    typeof row.email === "string" &&
    typeof row.passwordHash === "string" &&
    row.passwordHash.length > 0
  );
}

let singleton: AccountStore | null = null;

export function getAccountStore(): AccountStore {
  if (!singleton) {
    singleton = new JsonFileAccountStore(defaultAccountsPath());
  }
  return singleton;
}

/** Tests only — reset the process singleton. */
export function resetAccountStoreForTests(): void {
  singleton = null;
}
