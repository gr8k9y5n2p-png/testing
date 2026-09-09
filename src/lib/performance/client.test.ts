import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import {
  fetchPerformance,
  fetchPerformanceIfAvailable,
  normalizePerformanceResponse,
  postPerformanceGrowth,
} from "./client.ts";

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

function livePack(ticker = "AMCPX") {
  return {
    fund_ticker: ticker,
    fund_identifier: ticker,
    fund_name: ticker,
    asset_class: "equity",
    start_dollars: 10_000,
    start_date: "2024-12-31",
    end_date: "2025-12-31",
    as_of: "2025-12-31",
    frequency: "monthly",
    mode: "live",
    source: "live",
    source_urls: [],
    benchmark_id: "SPY",
    benchmark_label: "S&P 500",
    benchmark_tracks: "S&P 500",
    is_proxy: true,
    fund: {
      ticker,
      name: ticker,
      currency: "USD",
      price_unit: "usd_per_share_adjusted",
      return_unit: "decimal",
      growth_unit: "usd",
      points: [
        {
          date: "2024-12-31",
          adj_close: 40,
          monthly_return: null,
          growth_of_x: 10_000,
        },
        {
          date: "2025-12-31",
          adj_close: 44,
          monthly_return: 0.1,
          growth_of_x: 11_000,
        },
      ],
    },
    benchmark: {
      ticker: "SPY",
      name: "SPY",
      currency: "USD",
      price_unit: "usd_per_share_adjusted",
      return_unit: "decimal",
      growth_unit: "usd",
      points: [
        {
          date: "2024-12-31",
          adj_close: 400,
          monthly_return: null,
          growth_of_x: 10_000,
        },
      ],
    },
    disclaimers: [],
  };
}

afterEach(() => {
  delete process.env[DATA_API_URL];
});

describe("performance client mode + remote fallback", () => {
  it("defaults omitted response mode to live when the Data API is set", () => {
    withDataApiUrl("https://data.example", () => {
      const pack = normalizePerformanceResponse({
        ...livePack(),
        mode: undefined,
      });
      assert.equal(pack.mode, "live");
    });
  });

  it("GETs live mode from the Data API and does not fall back to /api mocks", async () => {
    const seen: string[] = [];
    const prev = globalThis.fetch;
    globalThis.fetch = (async (input: RequestInfo | URL) => {
      const url = String(input);
      seen.push(url);
      const parsed = new URL(url, "https://website.example");
      assert.equal(parsed.searchParams.get("mode"), "live");
      return new Response(JSON.stringify(livePack()), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }) as typeof fetch;

    try {
      await withDataApiUrl("https://data.example", async () => {
        const pack = await fetchPerformance({ ticker: "AMCPX" });
        assert.equal(pack.mode, "live");
        assert.equal(pack.source, "live");
      });
      assert.equal(seen.length, 1);
      assert.match(seen[0], /^https:\/\/data\.example\/performance\?/);
      assert.equal(
        seen.some((url) => url.startsWith("/api/performance")),
        false,
      );
    } finally {
      globalThis.fetch = prev;
    }
  });

  it("rewrites hardcoded fixture to live on the remote host", async () => {
    const seen: string[] = [];
    const prev = globalThis.fetch;
    globalThis.fetch = (async (input: RequestInfo | URL) => {
      const url = String(input);
      seen.push(url);
      const parsed = new URL(url, "https://website.example");
      assert.equal(parsed.searchParams.get("mode"), "live");
      return new Response(JSON.stringify(livePack()), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }) as typeof fetch;

    try {
      await withDataApiUrl("https://data.example", async () => {
        await fetchPerformance({ ticker: "AMCPX", mode: "fixture" });
      });
      assert.equal(seen.length, 1);
    } finally {
      globalThis.fetch = prev;
    }
  });

  it("POSTs live/auto mode and does not use the same-origin mock on 5xx", async () => {
    const seen: { url: string; body?: string }[] = [];
    const prev = globalThis.fetch;
    globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
      seen.push({
        url: String(input),
        body: typeof init?.body === "string" ? init.body : undefined,
      });
      return new Response(JSON.stringify({ detail: "upstream down" }), {
        status: 503,
        headers: { "Content-Type": "application/json" },
      });
    }) as typeof fetch;

    try {
      await withDataApiUrl("https://data.example", async () => {
        const pack = await fetchPerformanceIfAvailable(
          { ticker: "AMCPX", start_dollars: 25_000, mode: "auto" },
          { method: "POST" },
        );
        assert.equal(pack, null);
      });
      assert.equal(seen.length, 1);
      assert.equal(seen[0].url, "https://data.example/performance/growth");
      assert.deepEqual(JSON.parse(seen[0].body ?? "{}"), {
        ticker: "AMCPX",
        start_dollars: 25_000,
        mode: "auto",
      });
    } finally {
      globalThis.fetch = prev;
    }
  });

  it("keeps No Performance on remote 404 / uncovered packs", async () => {
    const prev = globalThis.fetch;
    globalThis.fetch = (async () =>
      new Response(JSON.stringify({ detail: "No performance pack", code: "not_found" }), {
        status: 404,
        headers: { "Content-Type": "application/json" },
      })) as typeof fetch;

    try {
      await withDataApiUrl("https://data.example", async () => {
        const missing = await fetchPerformanceIfAvailable({ ticker: "VIGAX" });
        assert.equal(missing, null);
      });
    } finally {
      globalThis.fetch = prev;
    }
  });

  it("rejects covered:false so callers never invent a series", async () => {
    const prev = globalThis.fetch;
    globalThis.fetch = (async () =>
      new Response(JSON.stringify({ ...livePack("VIGAX"), covered: false, fund: { ...livePack("VIGAX").fund, points: [] } }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })) as typeof fetch;

    try {
      await withDataApiUrl("https://data.example", async () => {
        const missing = await fetchPerformanceIfAvailable({ ticker: "VIGAX" });
        assert.equal(missing, null);
      });
    } finally {
      globalThis.fetch = prev;
    }
  });

  it("still uses local fixture mocks when the Data API is unset", async () => {
    const prev = globalThis.fetch;
    globalThis.fetch = (async () => {
      throw new Error("same-origin mock route unavailable in unit tests");
    }) as typeof fetch;

    try {
      await withDataApiUrl(undefined, async () => {
        const pack = await fetchPerformance({ ticker: "AMCPX" });
        assert.equal(pack.mode, "fixture");
        assert.equal(pack.source, "fixture");
        assert.ok(pack.fund.points.length >= 2);
      });
    } finally {
      globalThis.fetch = prev;
    }
  });

  it("POSTs fixture mode on the local mock path", async () => {
    let body: string | undefined;
    const prev = globalThis.fetch;
    globalThis.fetch = (async (_input: RequestInfo | URL, init?: RequestInit) => {
      body = typeof init?.body === "string" ? init.body : undefined;
      return new Response(JSON.stringify(livePack()), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }) as typeof fetch;

    try {
      await withDataApiUrl(undefined, async () => {
        await postPerformanceGrowth({ ticker: "AMCPX", start_dollars: 25_000 });
      });
      assert.equal(JSON.parse(body ?? "{}").mode, "fixture");
    } finally {
      globalThis.fetch = prev;
    }
  });
});
