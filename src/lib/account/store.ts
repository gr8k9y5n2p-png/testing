/**
 * Email/password accounts. JSON file — same persistence pattern as
 * saved-assets. `stripeCustomerId` is reserved for later Checkout link
 * by email. Do not enable billing here.
 */

import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { newAccountId } from "./session.ts";

export type AccountRecord = {
  id: string;
  email: string;
  passwordHash: string;
  /** Reserved. Stripe Checkout later sets `cus_…` on this same email. */
  stripeCustomerId: string | null;
  createdAt: string;
  updatedAt: string;
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
}

export class MemoryAccountStore implements AccountStore {
  protected records: AccountRecord[];

  constructor(records: AccountRecord[] = []) {
    this.records = records;
  }

  async findByEmail(email: string): Promise<AccountRecord | null> {
    const key = email.trim().toLowerCase();
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
      email: input.email.trim().toLowerCase(),
      passwordHash: input.passwordHash,
      stripeCustomerId: null,
      createdAt: stamp,
      updatedAt: stamp,
    };
    this.records.push(row);
    return row;
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
    super(loadAccounts(filePath));
    this.filePath = filePath;
  }

  private persist() {
    mkdirSync(dirname(this.filePath), { recursive: true });
    writeFileSync(this.filePath, `${JSON.stringify(this.records, null, 2)}\n`);
  }

  override async create(input: {
    email: string;
    passwordHash: string;
  }): Promise<AccountRecord> {
    const row = await super.create(input);
    this.persist();
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
  return typeof row.id === "string" && typeof row.email === "string";
}

let singleton: AccountStore | null = null;

export function getAccountStore(): AccountStore {
  if (!singleton) {
    singleton = new JsonFileAccountStore(defaultAccountsPath());
  }
  return singleton;
}
