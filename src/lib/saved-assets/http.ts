import {
  isHttpsRequest,
  resolveAccountSession,
  serializeAccountCookie,
  type ResolvedAccount,
} from "../account/session.ts";
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

function json(
  body: unknown,
  status: number,
  session: ResolvedAccount,
  request: Request,
): Response {
  const headers = new Headers({ "content-type": "application/json" });
  if (session.issued) {
    headers.append(
      "set-cookie",
      serializeAccountCookie(session.accountId, isHttpsRequest(request)),
    );
  }
  return new Response(JSON.stringify(body), { status, headers });
}

function fail(
  error: unknown,
  session: ResolvedAccount,
  request: Request,
): Response {
  if (error instanceof SavedAssetRequestError) {
    return json({ detail: error.detail }, error.status, session, request);
  }
  return json({ detail: "Couldn’t save that." }, 500, session, request);
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

/** GET/POST /api/saved-assets */
export async function handleSavedAssetsCollection(
  request: Request,
  store: SavedAssetStore,
): Promise<Response> {
  const session = resolveAccountSession(request);
  try {
    if (request.method === "GET") {
      const type = queryType(request);
      const items = await listSavedAssetsForAccount(
        store,
        session.accountId,
        type,
      );
      return json({ items, count: items.length }, 200, session, request);
    }
    if (request.method === "POST") {
      const input = parseWriteBody(await readJson(request));
      const { asset, created } = await saveSavedAssetForAccount(
        store,
        session.accountId,
        input,
      );
      return json({ item: asset }, created ? 201 : 200, session, request);
    }
    return json({ detail: "Method not allowed." }, 405, session, request);
  } catch (error) {
    return fail(error, session, request);
  }
}

/** GET/PATCH/DELETE /api/saved-assets/:id */
export async function handleSavedAssetItem(
  request: Request,
  id: string,
  store: SavedAssetStore,
): Promise<Response> {
  const session = resolveAccountSession(request);
  try {
    if (!id.trim()) {
      throw new SavedAssetRequestError(404, "Saved asset not found.");
    }
    if (request.method === "GET") {
      const item = await getSavedAssetForAccount(store, session.accountId, id);
      return json({ item }, 200, session, request);
    }
    if (request.method === "PATCH") {
      const item = await updateSavedAssetForAccount(
        store,
        session.accountId,
        id,
        await readJson(request),
      );
      return json({ item }, 200, session, request);
    }
    if (request.method === "DELETE") {
      await deleteSavedAssetForAccount(store, session.accountId, id);
      return json({ ok: true }, 200, session, request);
    }
    return json({ detail: "Method not allowed." }, 405, session, request);
  } catch (error) {
    return fail(error, session, request);
  }
}
