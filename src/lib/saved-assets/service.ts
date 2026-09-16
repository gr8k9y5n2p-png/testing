import {
  parseListPayload,
  isOpaqueObject,
} from "./payloads.ts";
import type { SavedAssetStore } from "./store.ts";
import {
  isSavedAssetType,
  SAVED_ASSET_NAME_MAX,
  type SavedAsset,
  type SavedAssetPatch,
  type SavedAssetType,
  type SavedAssetWrite,
} from "./types.ts";

export type SavedAssetError = {
  status: number;
  detail: string;
};

export class SavedAssetRequestError extends Error {
  readonly status: number;
  readonly detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

export function normalizeAssetName(raw: unknown): string {
  if (typeof raw !== "string") return "";
  return raw.trim().replace(/\s+/g, " ");
}

export function validateName(raw: unknown): string {
  const name = normalizeAssetName(raw);
  if (!name) {
    throw new SavedAssetRequestError(400, "Name is required.");
  }
  if (name.length > SAVED_ASSET_NAME_MAX) {
    throw new SavedAssetRequestError(
      400,
      `Name must be ${SAVED_ASSET_NAME_MAX} characters or fewer.`,
    );
  }
  return name;
}

export function validatePayload(
  type: SavedAssetType,
  payload: unknown,
): unknown {
  if (type === "list") {
    const parsed = parseListPayload(payload);
    if (!parsed) {
      throw new SavedAssetRequestError(
        400,
        "List payload must be { tickers: string[] }.",
      );
    }
    return parsed;
  }
  if (!isOpaqueObject(payload)) {
    throw new SavedAssetRequestError(
      400,
      "Portfolio payload must be a JSON object Modules owns.",
    );
  }
  return payload;
}

export function parseWriteBody(body: unknown): SavedAssetWrite {
  if (!body || typeof body !== "object") {
    throw new SavedAssetRequestError(400, "Invalid JSON body.");
  }
  const raw = body as { type?: unknown; name?: unknown; payload?: unknown };
  if (!isSavedAssetType(raw.type)) {
    throw new SavedAssetRequestError(400, "type must be list or portfolio.");
  }
  return {
    type: raw.type,
    name: validateName(raw.name),
    payload: validatePayload(raw.type, raw.payload),
  };
}

export function parsePatchBody(
  type: SavedAssetType,
  body: unknown,
): SavedAssetPatch {
  if (!body || typeof body !== "object") {
    throw new SavedAssetRequestError(400, "Invalid JSON body.");
  }
  const raw = body as { name?: unknown; payload?: unknown };
  const patch: SavedAssetPatch = {};
  if (raw.name !== undefined) patch.name = validateName(raw.name);
  if (raw.payload !== undefined) {
    patch.payload = validatePayload(type, raw.payload);
  }
  if (patch.name == null && patch.payload === undefined) {
    throw new SavedAssetRequestError(400, "Nothing to update.");
  }
  return patch;
}

export async function listSavedAssetsForAccount(
  store: SavedAssetStore,
  accountId: string,
  type?: SavedAssetType,
): Promise<SavedAsset[]> {
  return store.list(accountId, type);
}

export async function getSavedAssetForAccount(
  store: SavedAssetStore,
  accountId: string,
  id: string,
): Promise<SavedAsset> {
  const row = await store.get(accountId, id);
  if (!row) {
    throw new SavedAssetRequestError(404, "Saved asset not found.");
  }
  return row;
}

/** Create, or update the existing same-name asset for this account + type. */
export async function saveSavedAssetForAccount(
  store: SavedAssetStore,
  accountId: string,
  input: SavedAssetWrite,
): Promise<{ asset: SavedAsset; created: boolean }> {
  const existing = await store.findByName(accountId, input.type, input.name);
  if (existing) {
    const updated = await store.update(accountId, existing.id, {
      name: input.name,
      payload: input.payload,
    });
    if (!updated) {
      throw new SavedAssetRequestError(404, "Saved asset not found.");
    }
    return { asset: updated, created: false };
  }
  const asset = await store.create(accountId, input);
  return { asset, created: true };
}

export async function updateSavedAssetForAccount(
  store: SavedAssetStore,
  accountId: string,
  id: string,
  body: unknown,
): Promise<SavedAsset> {
  const current = await getSavedAssetForAccount(store, accountId, id);
  const patch = parsePatchBody(current.type, body);
  const updated = await store.update(accountId, id, patch);
  if (!updated) {
    throw new SavedAssetRequestError(404, "Saved asset not found.");
  }
  return updated;
}

export async function deleteSavedAssetForAccount(
  store: SavedAssetStore,
  accountId: string,
  id: string,
): Promise<void> {
  const removed = await store.delete(accountId, id);
  if (!removed) {
    throw new SavedAssetRequestError(404, "Saved asset not found.");
  }
}
