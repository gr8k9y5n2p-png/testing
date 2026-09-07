import { dataApiUrl, isRemoteDataApi } from "@/lib/data-api/config";
import { IllustrateRequestError } from "@/lib/illustrate/client";
import {
  mockPerformanceResponse,
  PerformanceMockError,
} from "@/lib/performance/mock";
import type {
  PerformanceGrowthRequest,
  PerformancePoint,
  PerformanceQuery,
  PerformanceResponse,
  PerformanceSeriesOut,
} from "@/lib/performance/types";

export function getPerformanceEndpoint(): string {
  return dataApiUrl("/performance");
}

export function getPerformanceGrowthEndpoint(): string {
  return dataApiUrl("/performance/growth");
}

function num(value: unknown, fallback = 0): number {
  if (value == null || value === "") return fallback;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function numOrNull(value: unknown): number | null {
  if (value == null || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

function normalizePoint(raw: unknown): PerformancePoint {
  const row = asRecord(raw);
  return {
    date: String(row.date ?? ""),
    adj_close: num(row.adj_close),
    monthly_return: numOrNull(row.monthly_return),
    growth_of_x: num(row.growth_of_x),
  };
}

function normalizeSeries(raw: unknown, fallbackTicker: string): PerformanceSeriesOut {
  const row = asRecord(raw);
  const pointsRaw = Array.isArray(row.points) ? row.points : [];
  return {
    ticker: String(row.ticker ?? fallbackTicker),
    name: String(row.name ?? fallbackTicker),
    currency: String(row.currency ?? "USD"),
    price_unit: String(row.price_unit ?? "usd_per_share_adjusted"),
    return_unit: String(row.return_unit ?? "decimal"),
    growth_unit: String(row.growth_unit ?? "usd"),
    points: pointsRaw.map(normalizePoint).filter((point) => point.date),
  };
}

export function normalizePerformanceResponse(
  raw: Record<string, unknown>,
): PerformanceResponse {
  const fundTicker = String(raw.fund_ticker ?? "");
  const benchId = String(raw.benchmark_id ?? "SPY");
  const asset =
    raw.asset_class === "fixed_income" || raw.asset_class === "international"
      ? raw.asset_class
      : "equity";

  return {
    fund_ticker: fundTicker,
    fund_identifier: String(raw.fund_identifier ?? fundTicker),
    fund_name: String(raw.fund_name ?? fundTicker),
    asset_class: asset,
    start_dollars: num(raw.start_dollars, 10_000),
    start_date: String(raw.start_date ?? ""),
    end_date: String(raw.end_date ?? ""),
    as_of: String(raw.as_of ?? raw.end_date ?? ""),
    frequency: "monthly",
    mode: String(raw.mode ?? "fixture"),
    source: String(raw.source ?? "live"),
    source_urls: Array.isArray(raw.source_urls) ? raw.source_urls.map(String) : [],
    benchmark_id: benchId,
    benchmark_label: String(raw.benchmark_label ?? benchId),
    benchmark_tracks: String(raw.benchmark_tracks ?? benchId),
    is_proxy: raw.is_proxy !== false,
    fund: normalizeSeries(raw.fund, fundTicker),
    benchmark: normalizeSeries(raw.benchmark, benchId),
    disclaimers: Array.isArray(raw.disclaimers) ? raw.disclaimers.map(String) : [],
  };
}

async function readError(response: Response, fallback: string) {
  let detail = fallback;
  let code: string | undefined;
  try {
    const body = (await response.json()) as { detail?: string; code?: string };
    if (body.detail) detail = body.detail;
    code = body.code;
  } catch {
    /* ignore */
  }
  throw new IllustrateRequestError(detail, response.status, code);
}

function queryString(request: PerformanceQuery): string {
  const params = new URLSearchParams();
  if (request.ticker) params.set("ticker", request.ticker);
  if (request.fund_identifier) params.set("fund_identifier", request.fund_identifier);
  if (request.benchmark) params.set("benchmark", request.benchmark);
  if (request.asset_class) params.set("asset_class", request.asset_class);
  if (request.benchmark_hint) params.set("benchmark_hint", request.benchmark_hint);
  if (request.start_dollars != null) params.set("start_dollars", String(request.start_dollars));
  if (request.start_date) params.set("start_date", request.start_date);
  if (request.end_date) params.set("end_date", request.end_date);
  params.set("mode", request.mode?.trim() || "fixture");
  return params.toString();
}

async function loadPerformance(
  method: "GET" | "POST",
  request: PerformanceQuery,
  init?: { signal?: AbortSignal },
): Promise<PerformanceResponse> {
  const remote = isRemoteDataApi();
  const path = method === "POST" ? "/performance/growth" : `/performance?${queryString(request)}`;
  const endpoint = dataApiUrl(path);
  const fallback = method === "POST" ? "/api/performance/growth" : `/api/performance?${queryString(request)}`;

  const fetchInit: RequestInit = {
    method,
    headers: {
      Accept: "application/json",
      ...(method === "POST" ? { "Content-Type": "application/json" } : {}),
    },
    body: method === "POST" ? JSON.stringify({ ...request, mode: request.mode ?? "fixture" }) : undefined,
    signal: init?.signal,
  };

  let response: Response;
  let usedMock = !remote;
  try {
    response = await fetch(endpoint, fetchInit);
    if (remote && response.status >= 500) {
      response = await fetch(fallback, fetchInit);
      usedMock = true;
    }
  } catch (error) {
    if (remote && !init?.signal?.aborted) {
      response = await fetch(fallback, fetchInit);
      usedMock = true;
    } else if (!remote) {
      try {
        return mockPerformanceResponse(request);
      } catch (caught) {
        if (caught instanceof PerformanceMockError) {
          throw new IllustrateRequestError(caught.message, caught.status);
        }
        throw caught;
      }
    } else {
      throw error;
    }
  }

  if (!response.ok) {
    await readError(response, `Performance failed (${response.status})`);
  }

  const raw = (await response.json()) as Record<string, unknown>;
  const normalized = normalizePerformanceResponse(raw);
  if (usedMock && !normalized.source.startsWith("fixture")) {
    normalized.source = "fixture";
  }
  return normalized;
}

export async function fetchPerformance(
  request: PerformanceQuery,
  init?: { signal?: AbortSignal },
): Promise<PerformanceResponse> {
  return loadPerformance("GET", request, init);
}

export async function postPerformanceGrowth(
  request: PerformanceGrowthRequest,
  init?: { signal?: AbortSignal },
): Promise<PerformanceResponse> {
  return loadPerformance("POST", request, init);
}
