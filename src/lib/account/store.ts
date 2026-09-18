/**
 * Email/password accounts. Stripe Checkout links `stripeCustomerId`
 * (`cus_…`) on the same account email. Usage + subscription status live
 * here so logged-in counters survive devices.
 *
 * Persistence:
 *   1. Upstash Redis / Vercel KV when REST URL + token are set
 *   2. Private Vercel Blob when BLOB_READ_WRITE_TOKEN or BLOB_STORE_ID is set
 *   3. JSON file for local/CI (`AFTERTAX_ACCOUNTS_PATH`, else `.data/accounts.json`)
 *
 * #277 reloads the file on every read/write, but Vercel `/tmp` is still
 * per-instance. Production sign-in then treated a miss as a wrong
 * password. Durable backends share one JSON document (same scrypt hashes)
 * across instances. Leftover file rows are merged in once.
 */

import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import {
  emptyUsage,
  isSubscriptionEntitled,
  mergeUsage,
  normalizeUsage,
  type DeviceUsage,
} from "../billing/limits.ts";
import {
  blobConfigured,
  createBlobJsonSnapshot,
  createRedisJsonSnapshot,
  redisRestConfig,
  type JsonSnapshot,
} from "./json-snapshot.ts";
import { timingSafeEqualHex } from "./passwords.ts";
import { newAccountId } from "./session.ts";

export const ACCOUNT_STORE_NOT_CONFIGURED =
  "Account storage is not configured. Set BLOB_READ_WRITE_TOKEN or Upstash Redis on this deployment.";

export type AccountStoreKind = "redis" | "blob" | "file";

export type AccountUsage = DeviceUsage;

export type AccountBillingPatch = {
  stripeCustomerId?: string | null;
  stripeSubscriptionId?: string | null;
  subscriptionStatus?: string | null;
  cancelAtPeriodEnd?: boolean;
  currentPeriodEnd?: string | null;
  usage?: DeviceUsage;
};

export type AccountRecord = {
  id: string;
  email: string;
  passwordHash: string;
  /** Stripe Customer id (`cus_…`) linked to this same email. */
  stripeCustomerId: string | null;
  stripeSubscriptionId: string | null;
  subscriptionStatus: string | null;
  cancelAtPeriodEnd: boolean;
  currentPeriodEnd: string | null;
  usage: DeviceUsage;
  createdAt: string;
  updatedAt: string;
  passwordResetTokenHash?: string | null;
  passwordResetExpiresAt?: string | null;
};

export type PublicAccount = {
  id: string;
  email: string;
  stripeCustomerId: string | null;
  subscribed: boolean;
  subscriptionStatus: string | null;
  cancelAtPeriodEnd: boolean;
  currentPeriodEnd: string | null;
};

export function toPublicAccount(row: AccountRecord): PublicAccount {
  return {
    id: row.id,
    email: row.email,
    stripeCustomerId: row.stripeCustomerId,
    subscribed: isSubscriptionEntitled(row),
    subscriptionStatus: row.subscriptionStatus,
    cancelAtPeriodEnd: row.cancelAtPeriodEnd,
    currentPeriodEnd: row.currentPeriodEnd,
  };
}

export interface AccountStore {
  findByEmail(email: string): Promise<AccountRecord | null>;
  findById(id: string): Promise<AccountRecord | null>;
  findByStripeCustomerId(customerId: string): Promise<AccountRecord | null>;
  create(input: {
    email: string;
    passwordHash: string;
  }): Promise<AccountRecord>;
  updateBilling(
    id: string,
    patch: AccountBillingPatch,
  ): Promise<AccountRecord | null>;
  mergeDeviceUsage(
    id: string,
    device: DeviceUsage,
  ): Promise<AccountRecord | null>;
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
      stripeSubscriptionId: null,
      subscriptionStatus: null,
      cancelAtPeriodEnd: false,
      currentPeriodEnd: null,
      usage: emptyUsage(),
      createdAt: stamp,
      updatedAt: stamp,
      passwordResetTokenHash: null,
      passwordResetExpiresAt: null,
    };
    this.records.push(row);
    return row;
  }

  async findByStripeCustomerId(customerId: string): Promise<AccountRecord | null> {
    const key = customerId.trim();
    if (!key) return null;
    return this.records.find((row) => row.stripeCustomerId === key) ?? null;
  }

  async updateBilling(
    id: string,
    patch: AccountBillingPatch,
  ): Promise<AccountRecord | null> {
    const row = await this.findById(id);
    if (!row) return null;
    if (patch.stripeCustomerId !== undefined) {
      row.stripeCustomerId = patch.stripeCustomerId;
    }
    if (patch.stripeSubscriptionId !== undefined) {
      row.stripeSubscriptionId = patch.stripeSubscriptionId;
    }
    if (patch.subscriptionStatus !== undefined) {
      row.subscriptionStatus = patch.subscriptionStatus;
    }
    if (patch.cancelAtPeriodEnd !== undefined) {
      row.cancelAtPeriodEnd = patch.cancelAtPeriodEnd;
    }
    if (patch.currentPeriodEnd !== undefined) {
      row.currentPeriodEnd = patch.currentPeriodEnd;
    }
    if (patch.usage) {
      row.usage = normalizeUsage(patch.usage);
    }
    row.updatedAt = new Date().toISOString();
    return row;
  }

  async mergeDeviceUsage(
    id: string,
    device: DeviceUsage,
  ): Promise<AccountRecord | null> {
    const row = await this.findById(id);
    if (!row) return null;
    row.usage = mergeUsage(row.usage, normalizeUsage(device));
    row.updatedAt = new Date().toISOString();
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

export const VERCEL_EPHEMERAL_ACCOUNTS_PATH = "/tmp/aftertax-accounts.json";

export function defaultAccountsPath(
  env: NodeJS.ProcessEnv = process.env,
): string {
  const pinned = env.AFTERTAX_ACCOUNTS_PATH?.trim();
  if (pinned) return pinned;
  if (env.VERCEL) return VERCEL_EPHEMERAL_ACCOUNTS_PATH;
  return join(process.cwd(), ".data", "accounts.json");
}

export function resolveAccountStoreKind(
  env: NodeJS.ProcessEnv = process.env,
): AccountStoreKind {
  const forced = env.AFTERTAX_ACCOUNT_STORE?.trim().toLowerCase();
  if (forced === "file") return "file";
  if (forced === "redis") {
    if (!redisRestConfig(env)) {
      throw new Error(
        "AFTERTAX_ACCOUNT_STORE=redis requires UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN (or KV_REST_API_*).",
      );
    }
    return "redis";
  }
  if (forced === "blob") {
    if (!blobConfigured(env)) {
      throw new Error(
        "AFTERTAX_ACCOUNT_STORE=blob requires BLOB_READ_WRITE_TOKEN or BLOB_STORE_ID.",
      );
    }
    return "blob";
  }
  if (redisRestConfig(env)) return "redis";
  if (blobConfigured(env)) return "blob";
  return "file";
}

export function isEphemeralVercelAccountStore(
  env: NodeJS.ProcessEnv = process.env,
): boolean {
  if (resolveAccountStoreKind(env) !== "file") return false;
  if (!env.VERCEL) return false;
  const path = defaultAccountsPath(env);
  return path === VERCEL_EPHEMERAL_ACCOUNTS_PATH || path.startsWith("/tmp/");
}

export function parseAccountRecords(raw: string | null | undefined): AccountRecord[] {
  if (!raw?.trim()) return [];
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(isAccountRecord).map(hydrateAccountRecord);
  } catch {
    return [];
  }
}

export function serializeAccountRecords(records: AccountRecord[]): string {
  return `${JSON.stringify(records, null, 2)}\n`;
}

export function mergeAccountRecords(
  primary: AccountRecord[],
  incoming: AccountRecord[],
): { records: AccountRecord[]; added: number } {
  const byEmail = new Map<string, AccountRecord>();
  for (const row of primary) byEmail.set(row.email, row);
  let added = 0;
  for (const row of incoming) {
    if (!byEmail.has(row.email)) {
      byEmail.set(row.email, row);
      added += 1;
    }
  }
  return { records: [...byEmail.values()], added };
}

export function loadAccountsFromFile(filePath: string): AccountRecord[] {
  try {
    return parseAccountRecords(readFileSync(filePath, "utf8"));
  } catch {
    return [];
  }
}

/** Skip a Blob round-trip when this isolate just read or wrote. */
export const HYDRATE_CACHE_MS = 2_500;

export class SharedJsonAccountStore extends MemoryAccountStore {
  private snapshot: JsonSnapshot;
  private legacyFilePath: string | null;
  private migrated = false;
  private chain: Promise<unknown> = Promise.resolve();
  private cache: { raw: string; at: number } | null = null;

  constructor(
    snapshot: JsonSnapshot,
    options: { legacyFilePath?: string | null } = {},
  ) {
    super([]);
    this.snapshot = snapshot;
    this.legacyFilePath = options.legacyFilePath ?? null;
  }

  private runExclusive<T>(fn: () => Promise<T>): Promise<T> {
    const next = this.chain.then(fn, fn);
    this.chain = next.then(
      () => undefined,
      () => undefined,
    );
    return next;
  }

  private async hydrate(): Promise<void> {
    const cached = this.cache;
    if (cached && Date.now() - cached.at < HYDRATE_CACHE_MS) {
      this.records = parseAccountRecords(cached.raw);
      return;
    }
    const raw = await this.snapshot.read();
    let records = parseAccountRecords(raw);
    this.cache = { raw: raw ?? "[]\n", at: Date.now() };
    if (!this.migrated) {
      this.migrated = true;
      if (this.legacyFilePath) {
        const merged = mergeAccountRecords(
          records,
          loadAccountsFromFile(this.legacyFilePath),
        );
        if (merged.added > 0) {
          records = merged.records;
          const serialized = serializeAccountRecords(records);
          await this.snapshot.write(serialized);
          this.cache = { raw: serialized, at: Date.now() };
          console.info(
            `[account] Migrated ${merged.added} account(s) from the file store into the durable store.`,
          );
        }
      }
    }
    this.records = records;
  }

  private async persist(): Promise<void> {
    const serialized = serializeAccountRecords(this.records);
    await this.snapshot.write(serialized);
    this.cache = { raw: serialized, at: Date.now() };
  }

  override async findByEmail(email: string): Promise<AccountRecord | null> {
    return this.runExclusive(async () => {
      await this.hydrate();
      return super.findByEmail(email);
    });
  }

  override async findById(id: string): Promise<AccountRecord | null> {
    return this.runExclusive(async () => {
      await this.hydrate();
      return super.findById(id);
    });
  }

  override async findByStripeCustomerId(
    customerId: string,
  ): Promise<AccountRecord | null> {
    return this.runExclusive(async () => {
      await this.hydrate();
      return super.findByStripeCustomerId(customerId);
    });
  }

  override async updateBilling(
    id: string,
    patch: AccountBillingPatch,
  ): Promise<AccountRecord | null> {
    return this.runExclusive(async () => {
      await this.hydrate();
      const row = await super.updateBilling(id, patch);
      if (row) await this.persist();
      return row;
    });
  }

  override async mergeDeviceUsage(
    id: string,
    device: DeviceUsage,
  ): Promise<AccountRecord | null> {
    return this.runExclusive(async () => {
      await this.hydrate();
      const row = await super.mergeDeviceUsage(id, device);
      if (row) await this.persist();
      return row;
    });
  }

  override async create(input: {
    email: string;
    passwordHash: string;
  }): Promise<AccountRecord> {
    return this.runExclusive(async () => {
      await this.hydrate();
      const row = await super.create(input);
      await this.persist();
      return row;
    });
  }

  override async updatePasswordHash(
    id: string,
    passwordHash: string,
  ): Promise<AccountRecord | null> {
    return this.runExclusive(async () => {
      await this.hydrate();
      const row = await super.updatePasswordHash(id, passwordHash);
      if (row) await this.persist();
      return row;
    });
  }

  override async setPasswordReset(
    id: string,
    tokenHash: string,
    expiresAt: string,
  ): Promise<AccountRecord | null> {
    return this.runExclusive(async () => {
      await this.hydrate();
      const row = await super.setPasswordReset(id, tokenHash, expiresAt);
      if (row) await this.persist();
      return row;
    });
  }

  override async consumePasswordReset(
    tokenHash: string,
    passwordHash: string,
  ): Promise<AccountRecord | null> {
    return this.runExclusive(async () => {
      await this.hydrate();
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
          (current.passwordResetTokenHash ?? null) !==
            previous.passwordResetTokenHash ||
          current.updatedAt !== previous.updatedAt
        );
      });
      if (changed) await this.persist();
      return row;
    });
  }
}

export class JsonFileAccountStore extends MemoryAccountStore {
  private filePath: string;

  constructor(filePath: string) {
    super([]);
    this.filePath = filePath;
  }

  private hydrate() {
    this.records = loadAccountsFromFile(this.filePath);
  }

  private persist() {
    mkdirSync(dirname(this.filePath), { recursive: true });
    writeFileSync(this.filePath, serializeAccountRecords(this.records));
  }

  override async findByEmail(email: string): Promise<AccountRecord | null> {
    this.hydrate();
    return super.findByEmail(email);
  }

  override async findById(id: string): Promise<AccountRecord | null> {
    this.hydrate();
    return super.findById(id);
  }

  override async findByStripeCustomerId(
    customerId: string,
  ): Promise<AccountRecord | null> {
    this.hydrate();
    return super.findByStripeCustomerId(customerId);
  }

  override async updateBilling(
    id: string,
    patch: AccountBillingPatch,
  ): Promise<AccountRecord | null> {
    this.hydrate();
    const row = await super.updateBilling(id, patch);
    if (row) this.persist();
    return row;
  }

  override async mergeDeviceUsage(
    id: string,
    device: DeviceUsage,
  ): Promise<AccountRecord | null> {
    this.hydrate();
    const row = await super.mergeDeviceUsage(id, device);
    if (row) this.persist();
    return row;
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

function hydrateAccountRecord(value: AccountRecord): AccountRecord {
  return {
    ...value,
    stripeCustomerId:
      typeof value.stripeCustomerId === "string" ? value.stripeCustomerId : null,
    stripeSubscriptionId:
      typeof value.stripeSubscriptionId === "string"
        ? value.stripeSubscriptionId
        : null,
    subscriptionStatus:
      typeof value.subscriptionStatus === "string" ? value.subscriptionStatus : null,
    cancelAtPeriodEnd: Boolean(value.cancelAtPeriodEnd),
    currentPeriodEnd:
      typeof value.currentPeriodEnd === "string" ? value.currentPeriodEnd : null,
    usage: normalizeUsage(value.usage),
  };
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
let warnedEphemeral = false;

export function createAccountStoreFromEnv(
  env: NodeJS.ProcessEnv = process.env,
): AccountStore {
  const kind = resolveAccountStoreKind(env);
  if (kind === "file") {
    if (isEphemeralVercelAccountStore(env) && !warnedEphemeral) {
      warnedEphemeral = true;
      console.warn(
        "[account] Vercel /tmp is ephemeral and not shared across instances. Sign-in will miss accounts written elsewhere. Connect Vercel Blob (BLOB_READ_WRITE_TOKEN or BLOB_STORE_ID) or Upstash Redis (UPSTASH_REDIS_REST_URL + UPSTASH_REDIS_REST_TOKEN).",
      );
    }
    return new JsonFileAccountStore(defaultAccountsPath(env));
  }
  const snapshot =
    kind === "redis"
      ? createRedisJsonSnapshot(env)
      : createBlobJsonSnapshot(env);
  return new SharedJsonAccountStore(snapshot, {
    legacyFilePath: defaultAccountsPath(env),
  });
}

export function getAccountStore(): AccountStore {
  if (!singleton) {
    singleton = createAccountStoreFromEnv();
  }
  return singleton;
}

/** Tests only — reset the process singleton. */
export function resetAccountStoreForTests(): void {
  singleton = null;
  warnedEphemeral = false;
}
