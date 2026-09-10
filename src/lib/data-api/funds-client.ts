/**
 * Parse Website BFF GET /api/funds. A down Data API is not an empty catalog.
 * Keep this module free of `@/` so node:test can load it.
 */

import { parseFundLookupResponse } from "./fund-lookup-parse.ts";
import { looksLikeExactTicker } from "./request-ticker.ts";

export type FundsApiClientResult<T = unknown> = {
  items: T[];
  unavailable: boolean;
  notInUniverse?: boolean;
};

function sourceLabel(body: unknown): string {
  if (!body || typeof body !== "object") return "";
  const source = (body as { source?: { label?: unknown } }).source;
  return String(source?.label ?? "");
}

export function isFundsApiUnavailable(ok: boolean, body: unknown): boolean {
  if (!ok) return true;
  if (!body || typeof body !== "object") return false;
  const record = body as { error?: unknown };
  if (record.error === "upstream") return true;
  return /unavailable/i.test(sourceLabel(body));
}

export function parseFundsApiResponse<T = unknown>(
  ok: boolean,
  body: unknown,
): FundsApiClientResult<T> {
  const unavailable = isFundsApiUnavailable(ok, body);
  if (unavailable) return { items: [], unavailable: true };
  const record = body && typeof body === "object" ? (body as { items?: unknown; data?: unknown }) : null;
  const items = Array.isArray(record?.items)
    ? record.items
    : Array.isArray(record?.data)
      ? record.data
      : [];
  return { items: items as T[], unavailable: false };
}

export async function fetchFundsLookup<T = unknown>(
  ticker: string,
): Promise<FundsApiClientResult<T> & { notInUniverse?: boolean }> {
  const key = ticker.trim().toUpperCase();
  try {
    const response = await fetch(
      `/api/funds/lookup?ticker=${encodeURIComponent(key)}`,
      { cache: "no-store" },
    );
    const body = await response.json().catch(() => null);
    const parsed = parseFundLookupResponse(response.status, body, key);
    if (parsed.kind === "unavailable") {
      return { items: [], unavailable: true };
    }
    if (parsed.kind === "found") {
      return { items: [parsed.fund as T], unavailable: false };
    }
    return { items: [], unavailable: false, notInUniverse: true };
  } catch {
    return { items: [], unavailable: true };
  }
}

export async function fetchFundsSearch<T = unknown>(
  query: string,
  limit = 20,
): Promise<FundsApiClientResult<T>> {
  const q = query.trim();
  if (!q) return { items: [], unavailable: false };
  const params = new URLSearchParams();
  params.set("q", q);
  params.set("limit", String(limit));
  params.set("offset", "0");
  try {
    const response = await fetch(`/api/funds?${params.toString()}`, {
      cache: "no-store",
    });
    const body = await response.json().catch(() => null);
    const page = parseFundsApiResponse<T>(response.ok, body);
    if (page.unavailable || page.items.length || !looksLikeExactTicker(q)) {
      return page;
    }
    return fetchFundsLookup<T>(q);
  } catch {
    return { items: [], unavailable: true };
  }
}
