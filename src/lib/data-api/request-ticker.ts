/**
 * Shared client for POST {DATA_API}/request/ticker.
 * Search uses source "search_miss" | "web". Portfolio / Compare can import
 * this helper later with source "portfolio" — do not invent fund data on a miss.
 *
 * Keep this module free of `@/` value imports so node:test can load it.
 */

export const TICKER_REQUEST_PATH = "/request/ticker";

/** Locked intake copy. Do not invent fund data while a ticker is queued. */
export const TICKER_REQUEST = {
  searchMissQueued: "We’ll work on ingesting this.",
  requestQueued: "We’ll add this.",
  issuerSearch: "We’ll search issuer sources...",
  alreadyCovered: (ticker: string) => `${ticker} is already in the universe.`,
  invalid: "Enter a valid fund ticker (1–5 letters).",
  error: "Couldn’t send that request. Try again.",
  formTitle: "Request a fund",
  formHint: "Not in search? Send the ticker and we’ll look for issuer sources.",
  tickerLabel: "Ticker",
  noteLabel: "Note (optional)",
  submit: "Request",
  submitting: "Sending…",
  /** Compare / Portfolio slot miss — not Search “No funds match.” */
  addToUniverse: "Add to universe",
  noFundsMatch: "No funds match.",
  searching: "Searching…",
} as const;

/**
 * Locked `source` enum for POST /request/ticker.
 * - `web` — Request a fund form (Search)
 * - `search_miss` — Search typed an exact ticker with no match
 * - `portfolio` — Portfolio import / Compare slot miss (Modules)
 */
export const TICKER_REQUEST_SOURCES = ["web", "search_miss", "portfolio"] as const;
export type TickerRequestSource = (typeof TICKER_REQUEST_SOURCES)[number];

/** US fund / ETF tickers after uppercase trim. */
const TICKER_SYMBOL = /^[A-Z]{1,5}$/;

export type TickerRequestInput = {
  ticker: string;
  note?: string;
  source?: TickerRequestSource;
};

/** Public helper args. Modules call `requestTicker({ ticker, note?, source })`. */
export type RequestTickerArgs = {
  ticker: string;
  note?: string;
  source: TickerRequestSource;
};

export type TickerRequestBody = {
  ticker: string;
  note?: string;
  source?: TickerRequestSource;
};

export type TickerRequestResult =
  | {
      kind: "queued";
      id: string;
      ticker: string;
      status: "queued";
      message: string;
    }
  | {
      kind: "already_covered";
      ticker: string;
      status: "already_covered";
    }
  | { kind: "invalid"; ticker: string }
  | { kind: "error"; message: string };

const searchMissSent = new Set<string>();
const portfolioMissSent = new Set<string>();

export function tickerRequestUrl(): string {
  const value = process.env.NEXT_PUBLIC_DATA_API_URL?.trim();
  const base = value ? value.replace(/\/$/, "") : "";
  return base ? `${base}${TICKER_REQUEST_PATH}` : `/api${TICKER_REQUEST_PATH}`;
}

export function normalizeTickerSymbol(value: string | null | undefined): string {
  return value?.trim().toUpperCase() ?? "";
}

export function isValidTickerSymbol(value: string | null | undefined): boolean {
  return TICKER_SYMBOL.test(normalizeTickerSymbol(value));
}

/** Whole query is one ticker token — not a fund name or multi-word search. */
export function looksLikeExactTicker(query: string | null | undefined): boolean {
  const trimmed = query?.trim() ?? "";
  if (!trimmed || /\s/.test(trimmed)) return false;
  return TICKER_SYMBOL.test(trimmed.toUpperCase());
}

/** Exact ticker, empty result set, and not already in the local universe. */
export function shouldReportSearchMiss(input: {
  query: string;
  resultCount: number;
  tickerInUniverse: boolean;
}): boolean {
  return (
    looksLikeExactTicker(input.query) &&
    input.resultCount === 0 &&
    !input.tickerInUniverse
  );
}

export function toRequestTickerBody(
  input: TickerRequestInput,
): { ok: true; body: TickerRequestBody } | { ok: false; error: "invalid_ticker" } {
  const ticker = normalizeTickerSymbol(input.ticker);
  if (!TICKER_SYMBOL.test(ticker)) {
    return { ok: false, error: "invalid_ticker" };
  }

  const body: TickerRequestBody = { ticker };
  const note = input.note?.trim();
  if (note) body.note = note;
  if (input.source) body.source = input.source;
  return { ok: true, body };
}

export function tickerRequestFetchInit(body: TickerRequestBody): RequestInit {
  return {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  };
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

export function normalizeTickerRequestResponse(
  status: number,
  raw: unknown,
): TickerRequestResult {
  const row = asRecord(raw);
  const ticker = normalizeTickerSymbol(
    typeof row.ticker === "string" ? row.ticker : "",
  );

  if (status === 422) {
    return { kind: "invalid", ticker };
  }

  if (status === 200 || row.status === "already_covered") {
    return {
      kind: "already_covered",
      ticker,
      status: "already_covered",
    };
  }

  if (status === 201 || row.status === "queued") {
    const message =
      typeof row.message === "string" && row.message.trim()
        ? row.message
        : TICKER_REQUEST.issuerSearch;
    return {
      kind: "queued",
      id: row.id == null ? "" : String(row.id),
      ticker,
      status: "queued",
      message,
    };
  }

  const detail = row.detail ?? row.message;
  return {
    kind: "error",
    message:
      typeof detail === "string" && detail.trim()
        ? detail
        : TICKER_REQUEST.error,
  };
}

export function noticeForTickerRequest(
  result: TickerRequestResult,
  intent: TickerRequestSource = "web",
): string | null {
  switch (result.kind) {
    case "queued":
      if (intent === "search_miss" || intent === "portfolio") {
        return TICKER_REQUEST.searchMissQueued;
      }
      if (intent === "web") return TICKER_REQUEST.requestQueued;
      return result.message || TICKER_REQUEST.issuerSearch;
    case "already_covered":
      return TICKER_REQUEST.alreadyCovered(result.ticker);
    case "invalid":
      return intent === "search_miss" || intent === "portfolio"
        ? null
        : TICKER_REQUEST.invalid;
    case "error":
      return intent === "search_miss" || intent === "portfolio"
        ? null
        : result.message || TICKER_REQUEST.error;
    default:
      return null;
  }
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return {};
  }
}

/**
 * One client for ticker intake. Search, Portfolio import, and Compare
 * slot misses must import this — do not duplicate the fetch.
 *
 *   requestTicker({ ticker: "ABCDX", note: "optional", source: "portfolio" })
 */
export async function requestTicker(
  input: RequestTickerArgs,
): Promise<TickerRequestResult> {
  const prepared = toRequestTickerBody(input);
  if (!prepared.ok) {
    return { kind: "invalid", ticker: normalizeTickerSymbol(input.ticker) };
  }

  const init = tickerRequestFetchInit(prepared.body);
  const endpoint = tickerRequestUrl();
  const fallback = `/api${TICKER_REQUEST_PATH}`;
  const remote = Boolean(process.env.NEXT_PUBLIC_DATA_API_URL?.trim());

  try {
    let response = await fetch(endpoint, init);
    if (remote && !response.ok && response.status >= 500 && fallback !== endpoint) {
      response = await fetch(fallback, init);
    }
    return normalizeTickerRequestResponse(response.status, await readJson(response));
  } catch {
    if (remote && fallback !== endpoint) {
      try {
        const response = await fetch(fallback, init);
        return normalizeTickerRequestResponse(
          response.status,
          await readJson(response),
        );
      } catch {
        /* beta intake is best-effort */
      }
    }
    return { kind: "error", message: TICKER_REQUEST.error };
  }
}

/** Exact ticker token that is not already in the local catalog / universe. */
export function shouldReportPortfolioMiss(input: {
  ticker: string;
  tickerInUniverse: boolean;
}): boolean {
  return looksLikeExactTicker(input.ticker) && !input.tickerInUniverse;
}

/**
 * Compare / Portfolio picker empty row.
 * Exact ticker outside the universe → Add to universe (intake).
 * Name / partial misses keep “No funds match.”
 */
export function tickerMissEmptyLabel(input: {
  query: string;
  tickerInUniverse: boolean;
  pending?: boolean;
}): string {
  if (input.pending) return TICKER_REQUEST.searching;
  if (shouldReportPortfolioMiss({
    ticker: input.query,
    tickerInUniverse: input.tickerInUniverse,
  })) {
    return TICKER_REQUEST.addToUniverse;
  }
  return TICKER_REQUEST.noFundsMatch;
}

async function requestDedupedTicker(
  ticker: string,
  source: Extract<TickerRequestSource, "search_miss" | "portfolio">,
  sent: Set<string>,
): Promise<TickerRequestResult | null> {
  const key = normalizeTickerSymbol(ticker);
  if (!TICKER_SYMBOL.test(key)) {
    return { kind: "invalid", ticker: key };
  }
  if (sent.has(key)) return null;
  sent.add(key);
  const result = await requestTicker({ ticker: key, source });
  if (result.kind === "error") {
    sent.delete(key);
  }
  return result;
}

/** Session-deduped search miss. Retries after a transport error. */
export async function requestTickerOnSearchMiss(
  ticker: string,
): Promise<TickerRequestResult | null> {
  return requestDedupedTicker(ticker, "search_miss", searchMissSent);
}

/**
 * Session-deduped Portfolio import / Compare slot miss.
 * Always POSTs `source: "portfolio"` — do not invent fund data while queued.
 */
export async function requestTickerOnPortfolioMiss(
  ticker: string,
): Promise<TickerRequestResult | null> {
  return requestDedupedTicker(ticker, "portfolio", portfolioMissSent);
}

/**
 * Fire-and-forget slot miss. Deduped; toast uses Search miss copy.
 * Call once per committed unknown ticker — never a second fetch implementation.
 */
export function notifyPortfolioTickerMiss(
  ticker: string,
  tickerInUniverse: boolean,
  onNotice?: (message: string) => void,
): void {
  if (!shouldReportPortfolioMiss({ ticker, tickerInUniverse })) return;
  void requestTickerOnPortfolioMiss(ticker).then((result) => {
    if (!result) return;
    const message = noticeForTickerRequest(result, "portfolio");
    if (message) onNotice?.(message);
  });
}

/** Test helper. */
export function resetTickerRequestDedupe(): void {
  searchMissSent.clear();
  portfolioMissSent.clear();
}
