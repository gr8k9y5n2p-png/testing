import { resolveAccountSession } from "../account/session.ts";
import { LISTS_LOCKED_DETAIL } from "../stripe/lists-access.ts";
import {
  getSavedAssetForAccount,
  listSavedAssetsForAccount,
  parseWriteBody,
  saveSavedAssetForAccount,
  SavedAssetRequestError,
  updateSavedAssetForAccount,
  deleteSavedAssetForAccount,
} from "./service.ts";
import type { SavedAssetStore } from "./store.ts";
import { isSavedAssetType, type SavedAssetType } from "./types.ts";

const SIGN_IN_DETAIL = "Sign in to save lists and portfolios.";

export type SavedAssetAccess = {
  /** Default true so unit tests keep session-only coverage. Routes pass entitlement. */
  listsEntitled?: boolean;
};

function requireListsEntitled(access: SavedAssetAccess): void {
  if (access.listsEntitled === false) {
    throw new SavedAssetRequestError(403, LISTS_LOCKED_DETAIL);
  }
}

function json(body: unknown, status: number): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function fail(error: unknown): Response {
  if (error instanceof SavedAssetRequestError) {
    return json({ detail: error.detail }, error.status);
  }
  return json({ detail: "Couldn’t save that." }, 500);
}

async function readJson(request: Request): Promise<unknown> {
  try {
    return await request.json();
  } catch {
    throw new SavedAssetRequestError(400, "Invalid JSON body.");
  }
}

function queryType(request: Request): SavedAssetType | undefined {
  const { searchParams } = new URL(request.url);
  const raw = searchParams.get("type");
  if (raw == null || raw === "") return undefined;
  if (!isSavedAssetType(raw)) {
    throw new SavedAssetRequestError(400, "type must be list or portfolio.");
  }
  return raw;
}

function requireSession(request: Request): string {
  const session = resolveAccountSession(request);
  if (!session) {
    throw new SavedAssetRequestError(401, SIGN_IN_DETAIL);
  }
  return session.accountId;
}

/** GET/POST /api/saved-assets */
export async function handleSavedAssetsCollection(
  request: Request,
  store: SavedAssetStore,
  access: SavedAssetAccess = {},
): Promise<Response> {
  try {
    const accountId = requireSession(request);
    if (request.method === "GET") {
      const type = queryType(request);
      if (type === "list") requireListsEntitled(access);
      const items = await listSavedAssetsForAccount(store, accountId, type);
      const visible =
        access.listsEntitled === false
          ? items.filter((item) => item.type !== "list")
          : items;
      return json({ items: visible, count: visible.length }, 200);
    }
    if (request.method === "POST") {
      const input = parseWriteBody(await readJson(request));
      if (input.type === "list") requireListsEntitled(access);
      const { asset, created } = await saveSavedAssetForAccount(
        store,
        accountId,
        input,
      );
      return json({ item: asset }, created ? 201 : 200);
    }
    return json({ detail: "Method not allowed." }, 405);
  } catch (error) {
    return fail(error);
  }
}

/** GET/PATCH/DELETE /api/saved-assets/:id */
export async function handleSavedAssetItem(
  request: Request,
  id: string,
  store: SavedAssetStore,
  access: SavedAssetAccess = {},
): Promise<Response> {
  try {
    const accountId = requireSession(request);
    if (!id.trim()) {
      throw new SavedAssetRequestError(404, "Saved asset not found.");
    }
    if (request.method === "GET") {
      const item = await getSavedAssetForAccount(store, accountId, id);
      if (item.type === "list") requireListsEntitled(access);
      return json({ item }, 200);
    }
    if (request.method === "PATCH") {
      const existing = await getSavedAssetForAccount(store, accountId, id);
      if (existing.type === "list") requireListsEntitled(access);
      const item = await updateSavedAssetForAccount(
        store,
        accountId,
        id,
        await readJson(request),
      );
      return json({ item }, 200);
    }
    if (request.method === "DELETE") {
      const existing = await getSavedAssetForAccount(store, accountId, id);
      if (existing.type === "list") requireListsEntitled(access);
      await deleteSavedAssetForAccount(store, accountId, id);
      return json({ ok: true }, 200);
    }
    return json({ detail: "Method not allowed." }, 405);
  } catch (error) {
    return fail(error);
  }
}
