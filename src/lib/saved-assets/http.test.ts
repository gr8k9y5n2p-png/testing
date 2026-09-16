import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { ACCOUNT_COOKIE, newAccountId, serializeAccountCookie } from "../account/session.ts";
import { handleSavedAssetItem, handleSavedAssetsCollection } from "./http.ts";
import { MemorySavedAssetStore } from "./store.ts";

function cookieHeader(accountId: string): string {
  const setCookie = serializeAccountCookie(accountId, false);
  return setCookie.split(";", 1)[0] ?? `${ACCOUNT_COOKIE}=`;
}

function request(
  url: string,
  init: RequestInit & { accountId?: string } = {},
): Request {
  const headers = new Headers(init.headers);
  if (init.accountId) headers.set("cookie", cookieHeader(init.accountId));
  return new Request(url, { ...init, headers });
}

async function json(response: Response): Promise<Record<string, unknown>> {
  return (await response.json()) as Record<string, unknown>;
}

describe("saved-assets HTTP account scoping", () => {
  it("save + open list round-trip stays on the same account", async () => {
    const store = new MemorySavedAssetStore();
    const userA = newAccountId();
    const create = await handleSavedAssetsCollection(
      request("http://localhost/api/saved-assets", {
        method: "POST",
        accountId: userA,
        body: JSON.stringify({
          type: "list",
          name: "Weekly book",
          payload: { tickers: ["FBGRX", "AGTHX", "ABALX"] },
        }),
      }),
      store,
    );
    assert.equal(create.status, 201);
    const created = await json(create);
    const item = created.item as { id: string; payload: { tickers: string[] } };
    assert.deepEqual(item.payload.tickers, ["FBGRX", "AGTHX", "ABALX"]);

    const listed = await handleSavedAssetsCollection(
      request("http://localhost/api/saved-assets?type=list", { accountId: userA }),
      store,
    );
    const listBody = await json(listed);
    assert.equal(listBody.count, 1);

    const opened = await handleSavedAssetItem(
      request(`http://localhost/api/saved-assets/${item.id}`, { accountId: userA }),
      item.id,
      store,
    );
    const openedBody = await json(opened);
    const openedItem = openedBody.item as { payload: { tickers: string[] } };
    assert.deepEqual(openedItem.payload.tickers, ["FBGRX", "AGTHX", "ABALX"]);
  });

  it("user A cannot read, update, or delete user B", async () => {
    const store = new MemorySavedAssetStore();
    const userA = newAccountId();
    const userB = newAccountId();
    const create = await handleSavedAssetsCollection(
      request("http://localhost/api/saved-assets", {
        method: "POST",
        accountId: userA,
        body: JSON.stringify({
          type: "list",
          name: "A only",
          payload: { tickers: ["FBGRX"] },
        }),
      }),
      store,
    );
    const { item } = (await json(create)) as { item: { id: string } };

    const listB = await handleSavedAssetsCollection(
      request("http://localhost/api/saved-assets?type=list", { accountId: userB }),
      store,
    );
    const listBody = await json(listB);
    assert.equal(listBody.count, 0);

    const getB = await handleSavedAssetItem(
      request(`http://localhost/api/saved-assets/${item.id}`, { accountId: userB }),
      item.id,
      store,
    );
    assert.equal(getB.status, 404);

    const patchB = await handleSavedAssetItem(
      request(`http://localhost/api/saved-assets/${item.id}`, {
        method: "PATCH",
        accountId: userB,
        body: JSON.stringify({ name: "Hijack" }),
      }),
      item.id,
      store,
    );
    assert.equal(patchB.status, 404);

    const deleteB = await handleSavedAssetItem(
      request(`http://localhost/api/saved-assets/${item.id}`, {
        method: "DELETE",
        accountId: userB,
      }),
      item.id,
      store,
    );
    assert.equal(deleteB.status, 404);

    const stillThere = await handleSavedAssetItem(
      request(`http://localhost/api/saved-assets/${item.id}`, { accountId: userA }),
      item.id,
      store,
    );
    assert.equal(stillThere.status, 200);
  });

  it("returns 401 when the request has no account session", async () => {
    const store = new MemorySavedAssetStore();
    const response = await handleSavedAssetsCollection(
      request("http://localhost/api/saved-assets?type=list"),
      store,
    );
    assert.equal(response.status, 401);
    const body = await json(response);
    assert.match(String(body.detail), /Sign in/);
  });

  it("stores a portfolio payload as opaque JSON", async () => {
    const store = new MemorySavedAssetStore();
    const userA = newAccountId();
    const payload = {
      version: 1,
      books: {
        bookDollars: 1_000_000,
        current: [{ ticker: "AGTHX", weightPct: 100, holdingDollars: 1_000_000 }],
        proposed: [{ ticker: "AMCPX", weightPct: 100, holdingDollars: 1_000_000 }],
      },
    };
    const create = await handleSavedAssetsCollection(
      request("http://localhost/api/saved-assets", {
        method: "POST",
        accountId: userA,
        body: JSON.stringify({
          type: "portfolio",
          name: "Proposal",
          payload,
        }),
      }),
      store,
    );
    assert.equal(create.status, 201);
    const created = await json(create);
    assert.deepEqual((created.item as { payload: unknown }).payload, payload);
  });
});
