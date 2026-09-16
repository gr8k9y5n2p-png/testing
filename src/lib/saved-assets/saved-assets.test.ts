import assert from "node:assert/strict";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, it } from "node:test";
import {
  parseListPayload,
  parsePortfolioBooksPayload,
  toPortfolioAssetPayload,
} from "./payloads.ts";
import {
  PORTFOLIO_PAYLOAD_VERSION,
  SAVED_ASSETS_CONTRACT,
} from "./contract.ts";
import {
  getSavedAssetForAccount,
  saveSavedAssetForAccount,
  SavedAssetRequestError,
} from "./service.ts";
import { JsonFileSavedAssetStore, MemorySavedAssetStore } from "./store.ts";

describe("saved asset store scoping", () => {
  it("user A cannot read user B’s list", async () => {
    const store = new MemorySavedAssetStore();
    const saved = await store.create("acct_stub_aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", {
      type: "list",
      name: "Weekly book",
      payload: { tickers: ["FBGRX", "AGTHX"] },
    });

    assert.equal(
      await store.get("acct_stub_bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb", saved.id),
      null,
    );
    const visible = await store.list(
      "acct_stub_aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
      "list",
    );
    assert.equal(visible.length, 1);
    assert.deepEqual(visible[0]?.payload, { tickers: ["FBGRX", "AGTHX"] });
    assert.deepEqual(
      await store.list("acct_stub_bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb", "list"),
      [],
    );
  });

  it("round-trips a named ticker list and upserts by name", async () => {
    const store = new MemorySavedAssetStore();
    const account = "acct_stub_cccccccc-cccc-4ccc-8ccc-cccccccccccc";
    const first = await saveSavedAssetForAccount(store, account, {
      type: "list",
      name: "Weekly wholesaler book",
      payload: { tickers: ["FBGRX", "AGTHX", "ABALX"] },
    });
    assert.equal(first.created, true);

    const opened = await getSavedAssetForAccount(store, account, first.asset.id);
    assert.deepEqual(parseListPayload(opened.payload), {
      tickers: ["FBGRX", "AGTHX", "ABALX"],
    });

    const again = await saveSavedAssetForAccount(store, account, {
      type: "list",
      name: "weekly wholesaler book",
      payload: { tickers: ["FBGRX", "VFIAX"] },
    });
    assert.equal(again.created, false);
    assert.equal(again.asset.id, first.asset.id);
    assert.deepEqual(parseListPayload(again.asset.payload), {
      tickers: ["FBGRX", "VFIAX"],
    });
    assert.equal((await store.list(account, "list")).length, 1);
  });

  it("stores opaque portfolio JSON without inventing holdings", async () => {
    const store = new MemorySavedAssetStore();
    const account = "acct_stub_dddddddd-dddd-4ddd-8ddd-dddddddddddd";
    const payload = {
      bookDollars: 1_000_000,
      current: [{ ticker: "AGTHX", fundName: "Growth", weightPct: 50, holdingDollars: 500000 }],
      proposed: [],
      extraModulesField: { note: "owned by Modules" },
    };
    const saved = await store.create(account, {
      type: "portfolio",
      name: "Proposal A",
      payload,
    });
    const opened = await store.get(account, saved.id);
    assert.deepEqual(opened?.payload, payload);
    const parsed = parsePortfolioBooksPayload(opened?.payload);
    assert.equal(parsed?.current[0]?.ticker, "AGTHX");
    assert.deepEqual(parsed?.proposed, []);

    const enveloped = toPortfolioAssetPayload({
      bookDollars: 1_000_000,
      current: [],
      proposed: [],
      currentUnit: "pct",
      proposedUnit: "pct",
    });
    assert.equal(enveloped.version, PORTFOLIO_PAYLOAD_VERSION);
    assert.equal(SAVED_ASSETS_CONTRACT.apiPath, "/api/saved-assets");
    assert.deepEqual(
      parsePortfolioBooksPayload(enveloped)?.proposed,
      [],
    );
  });

  it("persists to the JSON file store", async () => {
    const dir = mkdtempSync(join(tmpdir(), "aftertax-saved-"));
    const file = join(dir, "saved-assets.json");
    const first = new JsonFileSavedAssetStore(file);
    const account = "acct_stub_eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee";
    const created = await first.create(account, {
      type: "list",
      name: "File book",
      payload: { tickers: ["AMCPX"] },
    });

    const second = new JsonFileSavedAssetStore(file);
    const loaded = await second.get(account, created.id);
    assert.deepEqual(parseListPayload(loaded?.payload), { tickers: ["AMCPX"] });
  });

  it("404s when another account asks for an id", async () => {
    const store = new MemorySavedAssetStore();
    const saved = await store.create("user-a", {
      type: "list",
      name: "Private",
      payload: { tickers: ["FBGRX"] },
    });
    await assert.rejects(
      () => getSavedAssetForAccount(store, "user-b", saved.id),
      (error: unknown) => {
        assert.ok(error instanceof SavedAssetRequestError);
        assert.equal(error.status, 404);
        return true;
      },
    );
  });
});
