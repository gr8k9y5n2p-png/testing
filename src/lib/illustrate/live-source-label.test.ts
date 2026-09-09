import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { isLiveDataSource, sourceEyebrowSuffix } from "./live-source-label.ts";

describe("friends-beta source chrome", () => {
  it("labels Live only when the client stamped the Data API", () => {
    assert.equal(isLiveDataSource("live"), true);
    assert.equal(sourceEyebrowSuffix("live"), " · Live");
  });

  it("stays blank for mock, fixture, and unknown instead of SAMPLE", () => {
    assert.equal(isLiveDataSource("mock"), false);
    assert.equal(isLiveDataSource("fixture"), false);
    assert.equal(isLiveDataSource(undefined), false);
    assert.equal(isLiveDataSource(null), false);
    assert.equal(sourceEyebrowSuffix("mock"), "");
    assert.equal(sourceEyebrowSuffix("fixture"), "");
    assert.equal(sourceEyebrowSuffix(undefined), "");
  });
});
