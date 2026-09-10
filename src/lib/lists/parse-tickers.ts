/**
 * Lists paste / type parser. Split on commas, whitespace, newlines, and
 * semicolons. Dedupe case-insensitively; keep first-seen order; uppercase.
 */

import {
  looksLikeExactTicker,
  normalizeTickerSymbol,
} from "../data-api/request-ticker.ts";

const TICKER_SPLIT = /[,;\s]+/;

/** Tokens that look like fund tickers (1–5 letters). Junk text is dropped. */
export function parseTickerList(raw: string | null | undefined): string[] {
  if (!raw) return [];
  const seen = new Set<string>();
  const tickers: string[] = [];
  for (const part of raw.split(TICKER_SPLIT)) {
    const ticker = normalizeTickerSymbol(part);
    if (!ticker || seen.has(ticker) || !looksLikeExactTicker(ticker)) continue;
    seen.add(ticker);
    tickers.push(ticker);
  }
  return tickers;
}

/** Append a pasted / typed batch onto an existing list. Keep input order. */
export function mergeTickerLists(
  current: readonly string[],
  incoming: string | readonly string[],
): string[] {
  const extra =
    typeof incoming === "string"
      ? parseTickerList(incoming)
      : incoming.flatMap((value) => parseTickerList(value));
  const seen = new Set<string>();
  const next: string[] = [];
  for (const ticker of [...current, ...extra]) {
    const key = normalizeTickerSymbol(ticker);
    if (!key || seen.has(key) || !looksLikeExactTicker(key)) continue;
    seen.add(key);
    next.push(key);
  }
  return next;
}

export function removeTicker(
  current: readonly string[],
  ticker: string,
): string[] {
  const key = normalizeTickerSymbol(ticker);
  return current.filter((item) => normalizeTickerSymbol(item) !== key);
}

/** `/lists?tickers=FBGRX,AGTHX` or `/lists` when empty. */
export function listsTickersPath(
  tickers: Array<string | undefined | null> = [],
): string {
  const filled = parseTickerList(tickers.filter(Boolean).join(","));
  if (filled.length === 0) return "/lists";
  return `/lists?tickers=${filled.map(encodeURIComponent).join(",")}`;
}

export function parseListsQueryTickers(params: {
  tickers?: string | string[] | null;
  ticker?: string | string[] | null;
} = {}): string[] {
  const parts = [
    ...(Array.isArray(params.tickers)
      ? params.tickers
      : params.tickers != null
        ? [params.tickers]
        : []),
    ...(Array.isArray(params.ticker)
      ? params.ticker
      : params.ticker != null
        ? [params.ticker]
        : []),
  ];
  return parseTickerList(parts.join(","));
}
