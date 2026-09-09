import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { defaultPerformanceMode, resolvePerformanceMode } from "./mode.ts";

describe("defaultPerformanceMode", () => {
  it("requests live when the Data API host is configured", () => {
    assert.equal(
      defaultPerformanceMode({ NEXT_PUBLIC_DATA_API_URL: "https://data.example" }),
      "live",
    );
  });

  it("keeps fixture for local same-origin mock without the Data API", () => {
    assert.equal(defaultPerformanceMode({}), "fixture");
    assert.equal(defaultPerformanceMode({ NEXT_PUBLIC_DATA_API_URL: "  " }), "fixture");
  });
});

describe("resolvePerformanceMode", () => {
  it("never sends fixture to a configured Data API", () => {
    const remote = { NEXT_PUBLIC_DATA_API_URL: "https://data.example" };
    assert.equal(resolvePerformanceMode(undefined, remote), "live");
    assert.equal(resolvePerformanceMode("", remote), "live");
    assert.equal(resolvePerformanceMode("fixture", remote), "live");
    assert.equal(resolvePerformanceMode("live", remote), "live");
    assert.equal(resolvePerformanceMode("auto", remote), "auto");
  });

  it("honors fixture, live, and auto on the local mock path", () => {
    const local = {};
    assert.equal(resolvePerformanceMode(undefined, local), "fixture");
    assert.equal(resolvePerformanceMode("fixture", local), "fixture");
    assert.equal(resolvePerformanceMode("live", local), "live");
    assert.equal(resolvePerformanceMode("auto", local), "auto");
  });
});
