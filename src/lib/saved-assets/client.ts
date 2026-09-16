/**
 * Browser / Modules helper for `/api/saved-assets`.
 *
 * Lists already uses this. Portfolio / Modules: save `getBooks()` as
 * `{ type: "portfolio", name, payload }` and `parsePortfolioBooksPayload`
 * on open. Do not invent holdings.
 */

import { SAVED_ASSETS_API_PATH } from "./contract.ts";
import type { SavedAsset, SavedAssetType, SavedAssetWrite } from "./types.ts";

export { SAVED_ASSETS_API_PATH };

export type SavedAssetsListResponse = {
  items: SavedAsset[];
  count: number;
};

export type SavedAssetItemResponse = {
  item: SavedAsset;
};

export class SavedAssetsClientError extends Error {
  readonly status: number;
  readonly detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

async function parseError(response: Response): Promise<SavedAssetsClientError> {
  let detail = "Couldn’t complete that.";
  try {
    const body = (await response.json()) as { detail?: string };
    if (typeof body.detail === "string" && body.detail.trim()) {
      detail = body.detail;
    }
  } catch {
    /* keep default */
  }
  return new SavedAssetsClientError(response.status, detail);
}

async function requestJson<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(path, {
    credentials: "same-origin",
    ...init,
    headers: {
      accept: "application/json",
      ...(init?.body ? { "content-type": "application/json" } : {}),
      ...init?.headers,
    },
  });
  if (!response.ok) throw await parseError(response);
  return (await response.json()) as T;
}

export async function listSavedAssets(
  type?: SavedAssetType,
): Promise<SavedAsset[]> {
  const params = new URLSearchParams();
  if (type) params.set("type", type);
  const query = params.toString();
  const path = query
    ? `${SAVED_ASSETS_API_PATH}?${query}`
    : SAVED_ASSETS_API_PATH;
  const body = await requestJson<SavedAssetsListResponse>(path);
  return Array.isArray(body.items) ? body.items : [];
}

export async function getSavedAsset(id: string): Promise<SavedAsset> {
  const body = await requestJson<SavedAssetItemResponse>(
    `${SAVED_ASSETS_API_PATH}/${encodeURIComponent(id)}`,
  );
  return body.item;
}

export async function saveSavedAsset(
  input: SavedAssetWrite,
): Promise<SavedAsset> {
  const body = await requestJson<SavedAssetItemResponse>(SAVED_ASSETS_API_PATH, {
    method: "POST",
    body: JSON.stringify(input),
  });
  return body.item;
}

export async function updateSavedAsset(
  id: string,
  patch: { name?: string; payload?: unknown },
): Promise<SavedAsset> {
  const body = await requestJson<SavedAssetItemResponse>(
    `${SAVED_ASSETS_API_PATH}/${encodeURIComponent(id)}`,
    {
      method: "PATCH",
      body: JSON.stringify(patch),
    },
  );
  return body.item;
}

export async function deleteSavedAsset(id: string): Promise<void> {
  await requestJson<{ ok: boolean }>(
    `${SAVED_ASSETS_API_PATH}/${encodeURIComponent(id)}`,
    { method: "DELETE" },
  );
}
