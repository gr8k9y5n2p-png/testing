/**
 * Server-side saved-asset persistence.
 *
 * No database or extra cloud vendor in this repo. Default store is a JSON
 * file (local `.data/saved-assets.json`, Vercel `/tmp/…`). That matches the
 * existing mock/API-file patterns and is enough for friends beta + tests.
 *
 * Vercel’s filesystem is ephemeral — a later Neon/Postgres swap can implement
 * `SavedAssetStore` without changing the HTTP contract. Set SAVED_ASSETS_PATH
 * to pin the file.
 */

import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import type { SavedAsset, SavedAssetPatch, SavedAssetType, SavedAssetWrite } from "./types.ts";

export interface SavedAssetStore {
  list(accountId: string, type?: SavedAssetType): Promise<SavedAsset[]>;
  get(accountId: string, id: string): Promise<SavedAsset | null>;
  create(accountId: string, input: SavedAssetWrite): Promise<SavedAsset>;
  update(
    accountId: string,
    id: string,
    patch: SavedAssetPatch,
  ): Promise<SavedAsset | null>;
  delete(accountId: string, id: string): Promise<boolean>;
  findByName(
    accountId: string,
    type: SavedAssetType,
    name: string,
  ): Promise<SavedAsset | null>;
}

function nowIso(): string {
  return new Date().toISOString();
}

function newId(): string {
  return `sav_${crypto.randomUUID()}`;
}

function nameKey(name: string): string {
  return name.trim().toLowerCase();
}

export class MemorySavedAssetStore implements SavedAssetStore {
  protected records: SavedAsset[];

  constructor(records: SavedAsset[] = []) {
    this.records = records;
  }

  async list(accountId: string, type?: SavedAssetType): Promise<SavedAsset[]> {
    return this.records
      .filter(
        (row) => row.accountId === accountId && (type == null || row.type === type),
      )
      .slice()
      .sort((a, b) => (a.updatedAt < b.updatedAt ? 1 : a.updatedAt > b.updatedAt ? -1 : 0));
  }

  async get(accountId: string, id: string): Promise<SavedAsset | null> {
    return (
      this.records.find((row) => row.accountId === accountId && row.id === id) ??
      null
    );
  }

  async findByName(
    accountId: string,
    type: SavedAssetType,
    name: string,
  ): Promise<SavedAsset | null> {
    const key = nameKey(name);
    return (
      this.records.find(
        (row) =>
          row.accountId === accountId &&
          row.type === type &&
          nameKey(row.name) === key,
      ) ?? null
    );
  }

  async create(accountId: string, input: SavedAssetWrite): Promise<SavedAsset> {
    const stamp = nowIso();
    const row: SavedAsset = {
      id: newId(),
      accountId,
      type: input.type,
      name: input.name.trim(),
      payload: input.payload,
      createdAt: stamp,
      updatedAt: stamp,
    };
    this.records.push(row);
    return row;
  }

  async update(
    accountId: string,
    id: string,
    patch: SavedAssetPatch,
  ): Promise<SavedAsset | null> {
    const row = await this.get(accountId, id);
    if (!row) return null;
    if (patch.name != null) row.name = patch.name.trim();
    if (patch.payload !== undefined) row.payload = patch.payload;
    row.updatedAt = nowIso();
    return row;
  }

  async delete(accountId: string, id: string): Promise<boolean> {
    const index = this.records.findIndex(
      (row) => row.accountId === accountId && row.id === id,
    );
    if (index < 0) return false;
    this.records.splice(index, 1);
    return true;
  }
}

export function defaultSavedAssetsPath(
  env: NodeJS.ProcessEnv = process.env,
): string {
  const pinned = env.SAVED_ASSETS_PATH?.trim();
  if (pinned) return pinned;
  if (env.VERCEL) return "/tmp/aftertax-saved-assets.json";
  return join(process.cwd(), ".data", "saved-assets.json");
}

export class JsonFileSavedAssetStore extends MemorySavedAssetStore {
  private filePath: string;

  constructor(filePath: string) {
    super(loadRecords(filePath));
    this.filePath = filePath;
  }

  private persist() {
    mkdirSync(dirname(this.filePath), { recursive: true });
    writeFileSync(this.filePath, `${JSON.stringify(this.snapshot(), null, 2)}\n`);
  }

  /** Test helper — current rows after writes. */
  snapshot(): SavedAsset[] {
    return this.records;
  }

  override async create(accountId: string, input: SavedAssetWrite) {
    const row = await super.create(accountId, input);
    this.persist();
    return row;
  }

  override async update(
    accountId: string,
    id: string,
    patch: SavedAssetPatch,
  ) {
    const row = await super.update(accountId, id, patch);
    if (row) this.persist();
    return row;
  }

  override async delete(accountId: string, id: string) {
    const removed = await super.delete(accountId, id);
    if (removed) this.persist();
    return removed;
  }
}

function loadRecords(filePath: string): SavedAsset[] {
  try {
    const raw = readFileSync(filePath, "utf8");
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(isPersistedAsset);
  } catch {
    return [];
  }
}

function isPersistedAsset(value: unknown): value is SavedAsset {
  if (!value || typeof value !== "object") return false;
  const row = value as SavedAsset;
  return (
    typeof row.id === "string" &&
    typeof row.accountId === "string" &&
    (row.type === "list" || row.type === "portfolio") &&
    typeof row.name === "string"
  );
}

let singleton: SavedAssetStore | null = null;

export function getSavedAssetStore(): SavedAssetStore {
  if (!singleton) {
    singleton = new JsonFileSavedAssetStore(defaultSavedAssetsPath());
  }
  return singleton;
}

/** Tests only — reset the process singleton. */
export function resetSavedAssetStoreForTests(): void {
  singleton = null;
}
