import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  FUNDS_SEARCH_PATH,
  fundsPageHasExactTicker,
  fundsSearchNotInUniverse,
  fundsSearchParams,
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
    const agthx = {
      ticker: "AGTHX",
      hasEstimate: false,
      fundName: "The Growth Fund of America",
    };
    const parsed = parseFundsApiResponse(true, {
      source: { kind: "live", label: "Data API /funds unavailable" },
      items: [agthx],
      total: 1,
    });
    assert.equal(parsed.unavailable, false);
    assert.equal((parsed.items[0] as { ticker: string }).ticker, "AGTHX");
  });

  it("keeps a live AGTHX hit even when has_estimate is false", () => {
    const agthx = {
      ticker: "AGTHX",
      hasEstimate: false,
      fundName: "The Growth Fund of America",
    };
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

  it("empty picker: not_in_universe / exact ticker → Add to universe", () => {
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
        unavailable: false,
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

  it("builds the same apex /api/funds?q= autocomplete URL Search uses", () => {
    const params = fundsSearchParams("AGTHX");
    assert.equal(FUNDS_SEARCH_PATH, "/api/funds");
    assert.equal(params.get("q"), "AGTHX");
    assert.equal(params.get("limit"), "20");
    assert.equal(params.get("offset"), "0");
    assert.equal(params.get("nav_only"), "1");
    assert.equal(params.get("upcoming"), null);
    assert.equal(params.get("has_estimate"), null);
    const family = fundsSearchParams("Blackrock");
    assert.equal(family.get("q"), "Blackrock");
    const cased = fundsSearchParams("BlackRock");
    assert.equal(cased.get("q"), "BlackRock");
  });

  it("marks Add to universe only when shared search returned no rows", () => {
    assert.equal(fundsSearchNotInUniverse([], "AGTHX"), true);
    assert.equal(fundsSearchNotInUniverse([], "BLAC"), true);
    assert.equal(
      fundsSearchNotInUniverse(
        [{ ticker: "MDLVX", fundName: "BlackRock Advantage Large Cap Value" }],
        "BLAC",
      ),
      false,
    );
    assert.equal(
      fundsSearchNotInUniverse(
        [{ ticker: "AGTHX", fundName: "The Growth Fund of America" }],
        "AGTHX",
      ),
      false,
    );
    assert.equal(fundsSearchNotInUniverse([], "BlackRock"), false);
  });
});
