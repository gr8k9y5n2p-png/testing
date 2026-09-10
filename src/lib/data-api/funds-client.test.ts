import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { parseFundsApiResponse } from "./funds-client.ts";

describe("GET /api/funds client parse", () => {
  it("treats 503 / upstream / unavailable label as down, not an empty catalog", () => {
    assert.deepEqual(
      parseFundsApiResponse(false, {
        error: "upstream",
        source: { label: "Data API /funds unavailable" },
        items: [],
        total: 0,
      }),
      { items: [], unavailable: true },
    );
    assert.deepEqual(
      parseFundsApiResponse(true, {
        source: { kind: "live", label: "Data API /funds unavailable" },
        items: [],
        total: 0,
      }),
      { items: [], unavailable: true },
    );
  });

  it("keeps a live AGTHX hit even when has_estimate is false", () => {
    const agthx = { ticker: "AGTHX", hasEstimate: false, fundName: "The Growth Fund of America" };
    const parsed = parseFundsApiResponse(true, {
      source: { kind: "live", label: "Data API /funds" },
      items: [agthx],
      total: 1,
    });
    assert.equal(parsed.unavailable, false);
    assert.equal(parsed.items.length, 1);
    assert.equal((parsed.items[0] as { ticker: string }).ticker, "AGTHX");
  });

  it("treats a live 200 with total 0 as a real miss, not Data API down", () => {
    const parsed = parseFundsApiResponse(true, {
      source: { kind: "live", label: "Data API /funds" },
      items: [],
      total: 0,
    });
    assert.equal(parsed.unavailable, false);
    assert.deepEqual(parsed.items, []);
  });
});
