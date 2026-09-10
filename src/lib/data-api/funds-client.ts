/**
 * Parse Website BFF GET /api/funds. A down Data API is not an empty catalog.
 * Keep this module free of `@/` so node:test can load it.
 */

import { looksLikeExactTicker } from "./request-ticker.ts";

export type FundsApiClientResult<T = unknown> = {
  items: T[];
  unavailable: boolean;
  notInUniverse?: boolean;
};

export type SearchPickerEmptyState =
  | "searching"
  | "unavailable"
  | "add_to_universe"
  | "no_match";

/**
 * Data 404 / empty exact-ticker /funds is the miss.
 * Exact ticker → Add to universe. Name / partial misses keep “No funds match.”
 */
export function searchPickerEmptyState(input: {
  pending: boolean;
  unavailable: boolean;
  notInUniverse?: boolean;
  exactTicker: boolean;
}): SearchPickerEmptyState {
  if (input.pending) return "searching";
  if (input.unavailable) return "unavailable";
  if (input.notInUniverse || input.exactTicker) return "add_to_universe";
  return "no_match";
}

export function tickerFromFundsItem(item: unknown): string {
  if (!item || typeof item !== "object") return "";
  return String((item as { ticker?: unknown }).ticker ?? "")
    .trim()
    .toUpperCase();
}

export function fundsPageHasExactTicker(
  items: readonly unknown[],
  query: string,
): boolean {
  const key = query.trim().toUpperCase();
  if (!looksLikeExactTicker(key)) return false;
  return items.some((item) => tickerFromFundsItem(item) === key);
}

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
  const record =
    body && typeof body === "object"
      ? (body as { items?: unknown; data?: unknown })
      : null;
  const items = Array.isArray(record?.items)
    ? record.items
    : Array.isArray(record?.data)
      ? record.data
      : [];
  // A live hit must never be dropped because a stale/soft-empty
  // "unavailable" label arrived with the same payload.
  if (items.length) return { items: items as T[], unavailable: false };
  if (isFundsApiUnavailable(ok, body)) return { items: [], unavailable: true };
  return { items: [], unavailable: false };
}

export async function fetchFundsSearch<T = unknown>(
  query: string,
  limit = 20,
  options?: { navOnly?: boolean },
): Promise<FundsApiClientResult<T>> {
  const q = query.trim();
  if (!q) return { items: [], unavailable: false };
  const params = new URLSearchParams();
  params.set("q", q);
  params.set("limit", String(limit));
  params.set("offset", "0");
  // Autocomplete is identity-only so AGTHX (has_estimate=false) stays
  // searchable. Paid History must omit nav_only so /distributions
  // finals/paid hydrate the 5-year matrix.
  if (options?.navOnly !== false) {
    params.set("nav_only", "1");
  }
  try {
    const response = await fetch(`/api/funds?${params.toString()}`, {
      cache: "no-store",
    });
    const body = await response.json().catch(() => null);
    const page = parseFundsApiResponse<T>(response.ok, body);
    if (page.unavailable) return page;
    if (fundsPageHasExactTicker(page.items, q) || !looksLikeExactTicker(q)) {
      return page;
    }
    return { items: page.items, unavailable: false, notInUniverse: true };
  } catch {
    return { items: [], unavailable: true };
  }
}
