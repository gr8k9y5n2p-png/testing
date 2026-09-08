import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import {
  isValidTickerSymbol,
  looksLikeExactTicker,
  normalizeTickerRequestResponse,
  normalizeTickerSymbol,
  noticeForTickerRequest,
  requestTicker,
  requestTickerOnSearchMiss,
  resetTickerRequestDedupe,
  shouldReportSearchMiss,
  TICKER_REQUEST,
  tickerRequestFetchInit,
  tickerRequestUrl,
  toRequestTickerBody,
} from "./request-ticker.ts";

afterEach(() => {
  resetTickerRequestDedupe();
});

describe("ticker request normalize", () => {
  it("uppercases and trims the ticker", () => {
    assert.equal(normalizeTickerSymbol(" abcdx "), "ABCDX");
    assert.equal(normalizeTickerSymbol("agthx"), "AGTHX");
    assert.equal(normalizeTickerSymbol("  "), "");
    assert.equal(normalizeTickerSymbol(null), "");
  });

  it("accepts 1–5 letter tickers only", () => {
    assert.equal(isValidTickerSymbol("A"), true);
    assert.equal(isValidTickerSymbol("ABCDX"), true);
    assert.equal(isValidTickerSymbol(" abcdx "), true);
    assert.equal(isValidTickerSymbol(""), false);
    assert.equal(isValidTickerSymbol("ABCDEF"), false);
    assert.equal(isValidTickerSymbol("AB1"), false);
    assert.equal(isValidTickerSymbol("AB-CD"), false);
    assert.equal(isValidTickerSymbol("AMCPX extra"), false);
  });

  it("reports a miss only for an exact ticker with no local row", () => {
    assert.equal(
      shouldReportSearchMiss({
        query: "ZZZZY",
        resultCount: 0,
        tickerInUniverse: false,
      }),
      true,
    );
    assert.equal(
      shouldReportSearchMiss({
        query: "AMCPX",
        resultCount: 0,
        tickerInUniverse: true,
      }),
      false,
    );
    assert.equal(
      shouldReportSearchMiss({
        query: "growth fund",
        resultCount: 0,
        tickerInUniverse: false,
      }),
      false,
    );
    assert.equal(
      shouldReportSearchMiss({
        query: "ZZZZY",
        resultCount: 3,
        tickerInUniverse: false,
      }),
      false,
    );
  });

  it("treats only a single ticker token as an exact ticker", () => {
    assert.equal(looksLikeExactTicker("abcdx"), true);
    assert.equal(looksLikeExactTicker(" ZZZZZ "), true);
    assert.equal(looksLikeExactTicker("growth fund"), false);
    assert.equal(looksLikeExactTicker("AMCPX Fund"), false);
    assert.equal(looksLikeExactTicker(""), false);
  });

  it("builds POST JSON: ticker required, note/source optional, no extras", () => {
    const queued = toRequestTickerBody({
      ticker: " abcdx ",
      note: "  please ingest  ",
      source: "web",
    });
    assert.deepEqual(queued, {
      ok: true,
      body: { ticker: "ABCDX", note: "please ingest", source: "web" },
    });

    const miss = toRequestTickerBody({ ticker: "zzzzz", source: "search_miss" });
    assert.deepEqual(miss, {
      ok: true,
      body: { ticker: "ZZZZZ", source: "search_miss" },
    });

    const portfolio = toRequestTickerBody({
      ticker: "CGHM",
      source: "portfolio",
    });
    assert.deepEqual(portfolio, {
      ok: true,
      body: { ticker: "CGHM", source: "portfolio" },
    });

    const omitted = toRequestTickerBody({ ticker: "VFIAX", note: "   " });
    assert.deepEqual(omitted, { ok: true, body: { ticker: "VFIAX" } });
    assert.equal("note" in omitted.body, false);
    assert.equal("source" in omitted.body, false);

    const invalid = toRequestTickerBody({ ticker: "not a ticker", source: "web" });
    assert.deepEqual(invalid, { ok: false, error: "invalid_ticker" });
  });

  it("serializes the locked POST shape", () => {
    const init = tickerRequestFetchInit({
      ticker: "ABCDX",
      note: "issuer pdf",
      source: "web",
    });
    assert.equal(init.method, "POST");
    assert.equal(init.body, JSON.stringify({
      ticker: "ABCDX",
      note: "issuer pdf",
      source: "web",
    }));
    const headers = init.headers as Record<string, string>;
    assert.equal(headers["Content-Type"], "application/json");
  });
});

describe("ticker request response normalize", () => {
  it("maps 201 queued, 200 already_covered, 422 invalid", () => {
    assert.deepEqual(
      normalizeTickerRequestResponse(201, {
        id: "req_1",
        ticker: "abcdx",
        status: "queued",
        message: TICKER_REQUEST.issuerSearch,
      }),
      {
        kind: "queued",
        id: "req_1",
        ticker: "ABCDX",
        status: "queued",
        message: TICKER_REQUEST.issuerSearch,
      },
    );

    assert.deepEqual(
      normalizeTickerRequestResponse(200, {
        status: "already_covered",
        ticker: "AMCPX",
      }),
      {
        kind: "already_covered",
        ticker: "AMCPX",
        status: "already_covered",
      },
    );

    assert.deepEqual(normalizeTickerRequestResponse(422, { ticker: "bad" }), {
      kind: "invalid",
      ticker: "BAD",
    });
  });

  it("picks Search vs Request-a-fund notices and stays silent on miss errors", () => {
    assert.equal(
      noticeForTickerRequest(
        {
          kind: "queued",
          id: "1",
          ticker: "ABCDX",
          status: "queued",
          message: TICKER_REQUEST.issuerSearch,
        },
        "search_miss",
      ),
      TICKER_REQUEST.searchMissQueued,
    );
    assert.equal(
      noticeForTickerRequest(
        {
          kind: "queued",
          id: "1",
          ticker: "ABCDX",
          status: "queued",
          message: TICKER_REQUEST.issuerSearch,
        },
        "web",
      ),
      TICKER_REQUEST.requestQueued,
    );
    assert.equal(
      noticeForTickerRequest(
        { kind: "already_covered", ticker: "AGTHX", status: "already_covered" },
        "web",
      ),
      "AGTHX is already in the universe.",
    );
    assert.equal(
      noticeForTickerRequest({ kind: "invalid", ticker: "BAD" }, "search_miss"),
      null,
    );
    assert.equal(
      noticeForTickerRequest({ kind: "error", message: "down" }, "search_miss"),
      null,
    );
  });
});

describe("requestTicker POST", () => {
  it("POSTs normalized JSON to /request/ticker and does not invent fields", async () => {
    const seen: { url: string; method?: string; body?: string }[] = [];
    const prev = globalThis.fetch;
    globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
      seen.push({
        url: String(input),
        method: init?.method,
        body: typeof init?.body === "string" ? init.body : undefined,
      });
      return new Response(
        JSON.stringify({
          id: "req_abcdx",
          ticker: "ABCDX",
          status: "queued",
          message: TICKER_REQUEST.issuerSearch,
        }),
        { status: 201, headers: { "Content-Type": "application/json" } },
      );
    }) as typeof fetch;

    try {
      const result = await requestTicker({
        ticker: " abcdx ",
        note: "  from search  ",
        source: "web",
      });
      assert.equal(result.kind, "queued");
      if (result.kind === "queued") {
        assert.equal(result.id, "req_abcdx");
        assert.equal(result.ticker, "ABCDX");
        assert.equal(result.message, TICKER_REQUEST.issuerSearch);
      }
      assert.equal(seen.length, 1);
      assert.match(seen[0].url, /\/request\/ticker$/);
      assert.equal(seen[0].url, tickerRequestUrl());
      assert.equal(seen[0].method, "POST");
      assert.deepEqual(JSON.parse(seen[0].body ?? "{}"), {
        ticker: "ABCDX",
        note: "from search",
        source: "web",
      });
    } finally {
      globalThis.fetch = prev;
    }
  });

  it("does not POST an invalid ticker", async () => {
    let called = 0;
    const prev = globalThis.fetch;
    globalThis.fetch = (async () => {
      called += 1;
      return new Response("{}", { status: 201 });
    }) as typeof fetch;
    try {
      const result = await requestTicker({ ticker: "too-long-ticker", source: "web" });
      assert.deepEqual(result, { kind: "invalid", ticker: "TOO-LONG-TICKER" });
      assert.equal(called, 0);
    } finally {
      globalThis.fetch = prev;
    }
  });

  it("maps already_covered and 422 from the wire", async () => {
    const prev = globalThis.fetch;
    const replies = [
      new Response(JSON.stringify({ status: "already_covered", ticker: "AMCPX" }), {
        status: 200,
      }),
      new Response(JSON.stringify({ detail: "invalid ticker" }), { status: 422 }),
    ];
    globalThis.fetch = (async () => replies.shift()!) as typeof fetch;
    try {
      const covered = await requestTicker({ ticker: "amcpx", source: "search_miss" });
      assert.deepEqual(covered, {
        kind: "already_covered",
        ticker: "AMCPX",
        status: "already_covered",
      });
      const invalid = await requestTicker({ ticker: "ZZZZZ", source: "web" });
      assert.equal(invalid.kind, "invalid");
    } finally {
      globalThis.fetch = prev;
    }
  });

  it("dedupes search_miss per ticker and retries after transport errors", async () => {
    const urls: string[] = [];
    let failOnce = true;
    const prev = globalThis.fetch;
    globalThis.fetch = (async (input: RequestInfo | URL) => {
      urls.push(String(input));
      if (failOnce) {
        failOnce = false;
        throw new Error("network");
      }
      return new Response(
        JSON.stringify({
          id: "req_zzzzz",
          ticker: "ZZZZZ",
          status: "queued",
          message: TICKER_REQUEST.issuerSearch,
        }),
        { status: 201 },
      );
    }) as typeof fetch;
    try {
      const first = await requestTickerOnSearchMiss("zzzzz");
      assert.equal(first?.kind, "error");
      const second = await requestTickerOnSearchMiss(" ZZZZZ ");
      assert.equal(second?.kind, "queued");
      const third = await requestTickerOnSearchMiss("ZZZZZ");
      assert.equal(third, null);
      assert.equal(urls.length, 2);
      assert.deepEqual(
        urls.map((url) => url.endsWith("/request/ticker")),
        [true, true],
      );
    } finally {
      globalThis.fetch = prev;
    }
  });
});
