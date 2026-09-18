import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  createBlobJsonSnapshot,
  createRedisJsonSnapshot,
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
});
