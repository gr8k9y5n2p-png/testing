import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  BLOB_SNAPSHOT_TIMEOUT_MESSAGE,
  REDIS_CAS_SCRIPT,
  accountsBlobListPrefix,
  accountsBlobVersionPath,
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

  it("compare-and-swap uses EVAL so a stale SET cannot clobber", async () => {
    let stored: string | null = '[{"email":"round@example.com"}]';
    const snapshot = createRedisJsonSnapshot(
      {
        UPSTASH_REDIS_REST_URL: "https://example.upstash.io",
        UPSTASH_REDIS_REST_TOKEN: "token",
      },
      {
        fetchImpl: async (_url, init) => {
          const command = JSON.parse(String(init?.body ?? "[]")) as unknown[];
          if (command[0] === "EVAL") {
            assert.equal(command[1], REDIS_CAS_SCRIPT);
            const expected = String(command[4] ?? "");
            const next = String(command[5] ?? "");
            if ((stored ?? "") !== expected) {
              return new Response(JSON.stringify({ result: 0 }), {
                status: 200,
                headers: { "content-type": "application/json" },
              });
            }
            stored = next;
            return new Response(JSON.stringify({ result: 1 }), {
              status: 200,
              headers: { "content-type": "application/json" },
            });
          }
          return new Response(JSON.stringify({ error: "unknown" }), { status: 400 });
        },
      },
    );
    assert.equal(
      await snapshot.compareAndSwap(
        '[{"email":"stale@example.com"}]',
        '[{"email":"stale@example.com"},{"email":"new@example.com"}]',
      ),
      false,
    );
    assert.match(stored ?? "", /round@example.com/);
    assert.equal(
      await snapshot.compareAndSwap(
        stored,
        '[{"email":"round@example.com"},{"email":"new@example.com"}]',
      ),
      true,
    );
    assert.match(stored ?? "", /new@example.com/);
    assert.match(stored ?? "", /round@example.com/);
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

  it("reads via list + authenticated fetch when pathname get 404s after put", async () => {
    const stored = '[{"email":"ada@example.com"}]\n';
    const blobUrl =
      "https://store.private.blob.vercel-storage.com/aftertax/accounts.json";
    let getCalls = 0;
    const snapshot = createBlobJsonSnapshot(
      { BLOB_READ_WRITE_TOKEN: "vercel_blob_rw_x" },
      {
        async get() {
          getCalls += 1;
          return { statusCode: 404 };
        },
        async put() {
          return { url: blobUrl, downloadUrl: blobUrl };
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
                downloadUrl: blobUrl,
                uploadedAt: "2026-01-02T00:00:00.000Z",
              },
            ],
          };
        },
        fetchImpl: async (input) => {
          const url = String(input);
          if (url === blobUrl || url.startsWith(`${blobUrl}?`)) {
            return new Response(stored, { status: 200 });
          }
          return new Response("missing", { status: 404 });
        },
      },
    );
    assert.match((await snapshot.read()) ?? "", /ada@example.com/);
    assert.equal(getCalls, 0);
  });

  it("reuses the put URL so the next read skips list and get", async () => {
    const stored = '[{"email":"ada@example.com"}]\n';
    const blobUrl =
      "https://store.private.blob.vercel-storage.com/aftertax/accounts.json";
    let getCalls = 0;
    let listCalls = 0;
    let fetchCalls = 0;
    const snapshot = createBlobJsonSnapshot(
      { BLOB_READ_WRITE_TOKEN: "vercel_blob_rw_x" },
      {
        async get() {
          getCalls += 1;
          return { statusCode: 404 };
        },
        async put() {
          return { url: blobUrl, downloadUrl: blobUrl };
        },
        async list() {
          listCalls += 1;
          return { blobs: [] };
        },
        fetchImpl: async (input, init) => {
          fetchCalls += 1;
          const headers = new Headers(init?.headers);
          assert.equal(headers.get("authorization"), "Bearer vercel_blob_rw_x");
          assert.equal(String(input), blobUrl);
          return new Response(stored, { status: 200 });
        },
      },
    );
    await snapshot.write(stored);
    assert.match((await snapshot.read()) ?? "", /ada@example.com/);
    assert.equal(getCalls, 0);
    assert.equal(listCalls, 0);
    assert.equal(fetchCalls, 1);
  });

  it("uses one wall-clock budget so stacked slow list+get cannot reach 20s", async () => {
    const started = Date.now();
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
      { timeoutMs: 50 },
    );
    await assert.rejects(() => snapshot.read(), /timed out/);
    assert.ok(Date.now() - started < 200, "read must fail on the overall budget");
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

  it("prefers a higher generation over a newer unversioned accounts.json", () => {
    const newest = pickNewestAccountBlob(
      [
        {
          pathname: "aftertax/accounts.json",
          url: "https://example/unversioned",
          uploadedAt: "2026-04-01T00:00:00.000Z",
        },
        {
          pathname: "aftertax/accounts.v2.json",
          url: "https://example/v2",
          uploadedAt: "2026-01-01T00:00:00.000Z",
        },
      ],
      "aftertax/accounts.json",
    );
    assert.equal(newest?.url, "https://example/v2");
    assert.equal(accountsBlobVersionPath("aftertax/accounts.json", 2), "aftertax/accounts.v2.json");
  });

  it("compare-and-swap writes the next generation and rejects a stale put", async () => {
    const blobs = new Map<string, string>();
    const snapshot = createBlobJsonSnapshot(
      { BLOB_READ_WRITE_TOKEN: "vercel_blob_rw_x" },
      {
        async get() {
          return { statusCode: 404 };
        },
        async put(pathname, payload, options) {
          if (!options.allowOverwrite && blobs.has(pathname)) {
            const error = new Error("already exists");
            (error as { status?: number }).status = 409;
            throw error;
          }
          blobs.set(pathname, payload);
          return {
            url: `https://store.private.blob.vercel-storage.com/${pathname}`,
            downloadUrl: `https://store.private.blob.vercel-storage.com/${pathname}`,
          };
        },
        async list() {
          return {
            blobs: [...blobs.entries()].map(([pathname, _payload], index) => ({
              pathname,
              url: `https://store.private.blob.vercel-storage.com/${pathname}`,
              downloadUrl: `https://store.private.blob.vercel-storage.com/${pathname}`,
              uploadedAt: new Date(Date.UTC(2026, 0, index + 1)).toISOString(),
            })),
          };
        },
        fetchImpl: async (input) => {
          const url = String(input);
          const pathname = url.replace("https://store.private.blob.vercel-storage.com/", "");
          const body = blobs.get(pathname);
          if (!body) return new Response("missing", { status: 404 });
          return new Response(body, { status: 200 });
        },
      },
    );
    assert.equal(
      await snapshot.compareAndSwap(null, '[{"email":"round@example.com"}]\n'),
      true,
    );
    assert.equal(blobs.has("aftertax/accounts.v1.json"), true);
    assert.equal(
      await snapshot.compareAndSwap(
        '[{"email":"stale@example.com"}]\n',
        '[{"email":"stale@example.com"}]\n',
      ),
      false,
    );
    assert.match((await snapshot.read({ fresh: true })) ?? "", /round@example.com/);
    assert.equal(
      await snapshot.compareAndSwap(
        '[{"email":"round@example.com"}]\n',
        '[{"email":"round@example.com"},{"email":"persist@example.com"}]\n',
      ),
      true,
    );
    assert.equal(blobs.has("aftertax/accounts.v2.json"), true);
    assert.match((await snapshot.read({ fresh: true })) ?? "", /persist@example.com/);
  });
});

describe("blob timeout copy", () => {
  it("uses a user-visible timeout message", () => {
    assert.match(BLOB_SNAPSHOT_TIMEOUT_MESSAGE, /timed out/);
  });
});
