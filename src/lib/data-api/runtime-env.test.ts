import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  allowDemoEngine,
  isProductionRuntime,
  readRuntimeEnv,
} from "./runtime-env.ts";

describe("runtime env / demo-engine guard", () => {
  it("reads env dynamically so an empty build-time inline can still see a runtime URL", () => {
    const prior = process.env.NEXT_PUBLIC_DATA_API_URL;
    process.env.NEXT_PUBLIC_DATA_API_URL = "https://data.example.test";
    try {
      assert.equal(readRuntimeEnv("NEXT_PUBLIC_DATA_API_URL"), "https://data.example.test");
    } finally {
      if (prior == null) delete process.env.NEXT_PUBLIC_DATA_API_URL;
      else process.env.NEXT_PUBLIC_DATA_API_URL = prior;
    }
  });

  it("forbids the demo engine in production even when Data API URL is unset", () => {
    const priorUrl = process.env.NEXT_PUBLIC_DATA_API_URL;
    const priorIllustrate = process.env.NEXT_PUBLIC_ILLUSTRATE_URL;
    const priorNode = process.env.NODE_ENV;
    delete process.env.NEXT_PUBLIC_DATA_API_URL;
    delete process.env.NEXT_PUBLIC_ILLUSTRATE_URL;
    process.env.NODE_ENV = "production";
    try {
      assert.equal(isProductionRuntime(), true);
      assert.equal(allowDemoEngine(), false);
    } finally {
      process.env.NODE_ENV = priorNode;
      if (priorUrl == null) delete process.env.NEXT_PUBLIC_DATA_API_URL;
      else process.env.NEXT_PUBLIC_DATA_API_URL = priorUrl;
      if (priorIllustrate == null) delete process.env.NEXT_PUBLIC_ILLUSTRATE_URL;
      else process.env.NEXT_PUBLIC_ILLUSTRATE_URL = priorIllustrate;
    }
  });
});
