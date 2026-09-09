import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { defaultPerformanceMode, resolvePerformanceMode } from "./mode.ts";

const DATA_API_URL = "NEXT_PUBLIC_DATA_API_URL";

function withDataApiUrl<T>(value: string | undefined, run: () => T): T {
  const previous = process.env[DATA_API_URL];
  if (value == null) delete process.env[DATA_API_URL];
  else process.env[DATA_API_URL] = value;
  try {
    return run();
  } finally {
    if (previous == null) delete process.env[DATA_API_URL];
    else process.env[DATA_API_URL] = previous;
  }
}

afterEach(() => {
  delete process.env[DATA_API_URL];
});

describe("defaultPerformanceMode", () => {
  it("requests live when the Data API host is configured", () => {
    withDataApiUrl("https://data.example", () => {
      assert.equal(defaultPerformanceMode(), "live");
    });
  });

  it("keeps fixture for local same-origin mock without the Data API", () => {
    withDataApiUrl(undefined, () => {
      assert.equal(defaultPerformanceMode(), "fixture");
    });
    withDataApiUrl("  ", () => {
      assert.equal(defaultPerformanceMode(), "fixture");
    });
  });
});

describe("resolvePerformanceMode", () => {
  it("never sends fixture to a configured Data API", () => {
    withDataApiUrl("https://data.example", () => {
      assert.equal(resolvePerformanceMode(undefined), "live");
      assert.equal(resolvePerformanceMode(""), "live");
      assert.equal(resolvePerformanceMode("fixture"), "live");
      assert.equal(resolvePerformanceMode("live"), "live");
      assert.equal(resolvePerformanceMode("auto"), "auto");
    });
  });

  it("honors fixture, live, and auto on the local mock path", () => {
    withDataApiUrl(undefined, () => {
      assert.equal(resolvePerformanceMode(undefined), "fixture");
      assert.equal(resolvePerformanceMode("fixture"), "fixture");
      assert.equal(resolvePerformanceMode("live"), "live");
      assert.equal(resolvePerformanceMode("auto"), "auto");
    });
  });
});
