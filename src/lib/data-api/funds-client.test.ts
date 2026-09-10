import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  fundsPageHasExactTicker,
  parseFundsApiResponse,
  searchPickerEmptyState,
} from "./funds-client.ts";

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

  it("keeps a live AGTHX hit even if a stale unavailable label is present", () => {
    const agthx = { ticker: "AGTHX", hasEstimate: false, fundName: "The Growth Fund of America" };
    const parsed = parseFundsApiResponse(true, {
      source: { kind: "live", label: "Data API /funds unavailable" },
      items: [agthx],
      total: 1,
    });
    assert.equal(parsed.unavailable, false);
    assert.equal((parsed.items[0] as { ticker: string }).ticker, "AGTHX");
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

  it("looks up exact tickers missing from /funds; keeps in-page hits", () => {
    assert.equal(fundsPageHasExactTicker([{ ticker: "AGTHX" }], "AGTHX"), true);
    assert.equal(fundsPageHasExactTicker([{ ticker: "FBGRX" }], "AGTHX"), false);
    assert.equal(fundsPageHasExactTicker([], "ZZZZZ"), false);
  });

  it("empty picker: lookup not_in_universe / exact ticker → Add to universe", () => {
    assert.equal(
      searchPickerEmptyState({
        pending: false,
        unavailable: false,
        notInUniverse: true,
        exactTicker: true,
      }),
      "add_to_universe",
    );
    assert.equal(
      searchPickerEmptyState({
        pending: false,
        unavailable: true,
        exactTicker: true,
      }),
      "unavailable",
    );
    assert.equal(
      searchPickerEmptyState({
        pending: false,
        unavailable: false,
        exactTicker: false,
      }),
      "no_match",
    );
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
