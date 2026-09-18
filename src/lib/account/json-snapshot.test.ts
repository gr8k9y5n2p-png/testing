import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  BLOB_SNAPSHOT_TIMEOUT_MESSAGE,
  accountsBlobListPrefix,
  createBlobJsonSnapshot,
  createRedisJsonSnapshot,
  pickNewestAccountBlob,
  redisRestConfig,
} from "./json-snapshot.ts";

describe("Redis account snapshot", () => {
  it("reads and writes the JSON document over the REST command API", async () => {
    let stored: string | null = null;
    const snapshot = createRedisJsonSnapshot(
      {
        UPSTASH_REDIS_REST_URL: "https://example.upstash.io",
        UPSTASH_REDIS_REST_TOKEN: "token",
      },
      {
        fetchImpl: async (_url, init) => {
          const command = JSON.parse(String(init?.body ?? "[]")) as unknown[];
          if (command[0] === "GET") {
            return new Response(JSON.stringify({ result: stored }), {
              status: 200,
              headers: { "content-type": "application/json" },
            });
          }
          if (command[0] === "SET") {
            stored = String(command[2]);
            return new Response(JSON.stringify({ result: "OK" }), {
              status: 200,
              headers: { "content-type": "application/json" },
            });
          }
          return new Response(JSON.stringify({ error: "unknown" }), { status: 400 });
        },
      },
    );
    assert.equal(await snapshot.read(), null);
    await snapshot.write('[{"id":"acct_1","email":"ada@example.com"}]\n');
    assert.match((await snapshot.read()) ?? "", /ada@example.com/);
    assert.equal(
      redisRestConfig({
        KV_REST_API_URL: "https://kv.example",
        KV_REST_API_TOKEN: "kv-token",
      })?.url,
      "https://kv.example",
    );
  });
});

describe("Blob account snapshot", () => {
  it("writes a private JSON blob and reads it back with the cache disabled", async () => {
    let stored: string | null = null;
    let lastGetOptions: { useCache?: boolean; access?: string } | null = null;
    let lastPutOptions: { access?: string; allowOverwrite?: boolean; cacheControlMaxAge?: number } | null =
      null;
    const snapshot = createBlobJsonSnapshot(
      { BLOB_READ_WRITE_TOKEN: "vercel_blob_rw_x" },
      {
        async get(_pathname, options) {
          lastGetOptions = options;
          if (stored == null) return null;
          return {
            statusCode: 200,
            stream: new Blob([stored]).stream(),
          };
        },
        async put(_pathname, payload, options) {
          lastPutOptions = options;
          stored = payload;
          return {};
        },
      },
    );
    assert.equal(await snapshot.read(), null);
    await snapshot.write('[{"email":"ada@example.com"}]\n');
    assert.match((await snapshot.read()) ?? "", /ada@example.com/);
    assert.equal(lastGetOptions?.useCache, false);
    assert.equal(lastGetOptions?.access, "private");
    assert.equal(lastPutOptions?.access, "private");
    assert.equal(lastPutOptions?.allowOverwrite, true);
    assert.equal(lastPutOptions?.cacheControlMaxAge, 60);
  });

  it("treats a missing private blob as empty when get 404s and list is empty", async () => {
    const snapshot = createBlobJsonSnapshot(
      { BLOB_READ_WRITE_TOKEN: "vercel_blob_rw_x" },
      {
        async get() {
          return { statusCode: 404 };
        },
        async put() {
          return {};
        },
        async list() {
          return { blobs: [] };
        },
      },
    );
    assert.equal(await snapshot.read(), null);
  });

  it("reads via list + get(url) when pathname get 404s after put", async () => {
    const stored = '[{"email":"ada@example.com"}]\n';
    const blobUrl =
      "https://store.private.blob.vercel-storage.com/aftertax/accounts.json";
    const snapshot = createBlobJsonSnapshot(
      { BLOB_READ_WRITE_TOKEN: "vercel_blob_rw_x" },
      {
        async get(ref) {
          if (ref === blobUrl) {
            return { statusCode: 200, stream: new Blob([stored]).stream() };
          }
          return { statusCode: 404 };
        },
        async put() {
          return {};
        },
        async list() {
          return {
            blobs: [
              {
                pathname: "aftertax/accounts.json",
                url: `${blobUrl}?stale=1`,
                uploadedAt: "2026-01-01T00:00:00.000Z",
              },
              {
                pathname: "aftertax/accounts.json",
                url: blobUrl,
                uploadedAt: "2026-01-02T00:00:00.000Z",
              },
            ],
          };
        },
      },
    );
    assert.match((await snapshot.read()) ?? "", /ada@example.com/);
  });

  it("times out a hanging blob get instead of waiting forever", async () => {
    const snapshot = createBlobJsonSnapshot(
      { BLOB_READ_WRITE_TOKEN: "vercel_blob_rw_x" },
      {
        async get() {
          return new Promise(() => {});
        },
        async put() {
          return new Promise(() => {});
        },
        async list() {
          return new Promise(() => {});
        },
      },
      { timeoutMs: 40 },
    );
    await assert.rejects(() => snapshot.read(), /timed out/);
    await assert.rejects(() => snapshot.write("[]\n"), /timed out/);
  });

  it("picks the newest exact pathname when the list has duplicates", () => {
    assert.equal(accountsBlobListPrefix("aftertax/accounts.json"), "aftertax/accounts");
    const newest = pickNewestAccountBlob(
      [
        {
          pathname: "aftertax/accounts.json",
          url: "https://example/old",
          uploadedAt: "2026-01-01T00:00:00.000Z",
        },
        {
          pathname: "aftertax/accounts.json",
          url: "https://example/new",
          uploadedAt: "2026-03-01T00:00:00.000Z",
        },
        {
          pathname: "aftertax/accounts-suffix.json",
          url: "https://example/suffix",
          uploadedAt: "2026-04-01T00:00:00.000Z",
        },
      ],
      "aftertax/accounts.json",
    );
    assert.equal(newest?.url, "https://example/new");
  });
});

describe("blob timeout copy", () => {
  it("uses a user-visible timeout message", () => {
    assert.match(BLOB_SNAPSHOT_TIMEOUT_MESSAGE, /timed out/);
  });
});
