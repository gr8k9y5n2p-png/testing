import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  listsTickersPath,
  mergeTickerLists,
  parseListsQueryTickers,
  parseTickerList,
  removeTicker,
} from "./parse-tickers.ts";

describe("parseTickerList", () => {
  it("splits commas, whitespace, newlines, and semicolons", () => {
    assert.deepEqual(
      parseTickerList("FBGRX, AGTHX;ABALX\nVFIAX FXAIX"),
      ["FBGRX", "AGTHX", "ABALX", "VFIAX", "FXAIX"],
    );
  });

  it("dedupes case-insensitively and keeps first-seen order", () => {
    assert.deepEqual(parseTickerList("fbgrx, AGTHX, FBGRX, agthx"), [
      "FBGRX",
      "AGTHX",
    ]);
  });

  it("normalizes to uppercase and drops empty / non-ticker junk", () => {
    assert.deepEqual(parseTickerList("  fbgrx  , , ;; --- 123 "), ["FBGRX"]);
    assert.deepEqual(parseTickerList(""), []);
    assert.deepEqual(parseTickerList(null), []);
  });

  it("keeps unknown but well-formed tickers instead of dropping them", () => {
    assert.deepEqual(parseTickerList("ZZZZZ, FBGRX"), ["ZZZZZ", "FBGRX"]);
  });
});

describe("mergeTickerLists / removeTicker", () => {
  it("appends a pasted batch without reordering existing tickers", () => {
    assert.deepEqual(mergeTickerLists(["FBGRX"], "AGTHX, ABALX, fbgrx"), [
      "FBGRX",
      "AGTHX",
      "ABALX",
    ]);
  });

  it("removes one ticker and leaves the rest in order", () => {
    assert.deepEqual(removeTicker(["FBGRX", "AGTHX", "ABALX"], "agthx"), [
      "FBGRX",
      "ABALX",
    ]);
  });
});

describe("lists query path", () => {
  it("builds /lists?tickers= from a pasted set", () => {
    assert.equal(listsTickersPath([]), "/lists");
    assert.equal(
      listsTickersPath(["fbgrx", "AGTHX", "ABALX"]),
      "/lists?tickers=FBGRX,AGTHX,ABALX",
    );
  });

  it("reads tickers / ticker query params the same way Compare does", () => {
    assert.deepEqual(
      parseListsQueryTickers({ tickers: "FBGRX,AGTHX", ticker: "ABALX" }),
      ["FBGRX", "AGTHX", "ABALX"],
    );
  });
});
