import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { abortable, createInflightCache } from "./inflight-cache.ts";

describe("createInflightCache", () => {
  it("dedupes in-flight loads and reuses a short-TTL hit", async () => {
    const cache = createInflightCache<string>(5_000);
    let loads = 0;
    const load = async () => {
      loads += 1;
      await new Promise((resolve) => setTimeout(resolve, 15));
      return "agthx";
    };

    const [first, second] = await Promise.all([
      cache.remember("agthx", load),
      cache.remember("agthx", load),
    ]);
    assert.equal(first, "agthx");
    assert.equal(second, "agthx");
    assert.equal(loads, 1);
    assert.equal(await cache.remember("agthx", load), "agthx");
    assert.equal(loads, 1);
  });

  it("does not cache a rejected load so the next caller retries", async () => {
    const cache = createInflightCache<string>(5_000);
    let loads = 0;
    await assert.rejects(
      cache.remember("miss", async () => {
        loads += 1;
        throw new Error("upstream");
      }),
      /upstream/,
    );
    assert.equal(
      await cache.remember("miss", async () => {
        loads += 1;
        return "ok";
      }),
      "ok",
    );
    assert.equal(loads, 2);
  });

  it("lets one consumer abort without cancelling the shared load", async () => {
    const cache = createInflightCache<string>(5_000);
    let loads = 0;
    const controller = new AbortController();
    const shared = cache.remember("pair", async () => {
      loads += 1;
      await new Promise((resolve) => setTimeout(resolve, 20));
      return "shared";
    });
    const aborted = cache.remember(
      "pair",
      async () => {
        throw new Error("should not load twice");
      },
      controller.signal,
    );
    controller.abort();
    await assert.rejects(aborted, (error: unknown) => {
      assert.equal(error instanceof DOMException, true);
      assert.equal((error as DOMException).name, "AbortError");
      return true;
    });
    assert.equal(await shared, "shared");
    assert.equal(loads, 1);
  });

  it("expires a value after the TTL", async () => {
    const cache = createInflightCache<number>(5);
    let loads = 0;
    await cache.remember("ttl", async () => {
      loads += 1;
      return 1;
    });
    await new Promise((resolve) => setTimeout(resolve, 10));
    await cache.remember("ttl", async () => {
      loads += 1;
      return 2;
    });
    assert.equal(loads, 2);
  });
});

describe("abortable", () => {
  it("rejects immediately when the signal is already aborted", async () => {
    const controller = new AbortController();
    controller.abort();
    await assert.rejects(
      abortable(Promise.resolve("late"), controller.signal),
      (error: unknown) => {
        assert.equal(error instanceof DOMException, true);
        return true;
      },
    );
  });
});
