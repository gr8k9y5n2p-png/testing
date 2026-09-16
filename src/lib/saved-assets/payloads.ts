/**
 * Payload helpers for saved assets.
 *
 * `list` is owned by Website (ticker symbols only).
 * `portfolio` is opaque JSON Modules owns — we accept any object and offer
 * a snapshot parser that matches PortfolioCompare books.
 */

import { parseTickerList } from "../lists/parse-tickers.ts";
import type { ListAssetPayload } from "./types.ts";

export function parseListPayload(payload: unknown): ListAssetPayload | null {
  if (!payload || typeof payload !== "object") return null;
  const raw = (payload as { tickers?: unknown }).tickers;
  if (!Array.isArray(raw)) return null;
  const tickers = parseTickerList(
    raw
      .filter((item): item is string => typeof item === "string")
      .join(","),
  );
  return { tickers };
}

export type PortfolioHoldingSnapshot = {
  id: string;
  ticker: string;
  fundName: string;
  family?: string;
  nav?: number | null;
  weightPct: number;
  holdingDollars: number;
};

export type PortfolioBooksSnapshot = {
  bookDollars: number;
  current: PortfolioHoldingSnapshot[];
  proposed: PortfolioHoldingSnapshot[];
  currentUnit: "pct" | "usd";
  proposedUnit: "pct" | "usd";
};

function isAllocationUnit(value: unknown): value is "pct" | "usd" {
  return value === "pct" || value === "usd";
}

function parseHolding(value: unknown): PortfolioHoldingSnapshot | null {
  if (!value || typeof value !== "object") return null;
  const row = value as Partial<PortfolioHoldingSnapshot>;
  if (typeof row.ticker !== "string") return null;
  const ticker = row.ticker.trim().toUpperCase();
  if (!ticker) return null;
  const weightPct = typeof row.weightPct === "number" ? row.weightPct : 0;
  const holdingDollars =
    typeof row.holdingDollars === "number" ? row.holdingDollars : 0;
  return {
    id: typeof row.id === "string" && row.id ? row.id : ticker,
    ticker,
    fundName: typeof row.fundName === "string" ? row.fundName : ticker,
    family: typeof row.family === "string" ? row.family : undefined,
    nav: typeof row.nav === "number" && row.nav > 0 ? row.nav : null,
    weightPct,
    holdingDollars,
  };
}

function parseHoldings(value: unknown): PortfolioHoldingSnapshot[] {
  if (!Array.isArray(value)) return [];
  return value
    .map(parseHolding)
    .filter((row): row is PortfolioHoldingSnapshot => row != null);
}

/**
 * Modules-owned portfolio payload. Extra keys are ignored, not invented.
 * Missing books become empty arrays — never seeded with demo tickers.
 */
export function parsePortfolioBooksPayload(
  payload: unknown,
): PortfolioBooksSnapshot | null {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    return null;
  }
  const raw = payload as Partial<PortfolioBooksSnapshot> & {
    book_dollars?: unknown;
  };
  const bookDollars =
    typeof raw.bookDollars === "number" && raw.bookDollars > 0
      ? raw.bookDollars
      : typeof raw.book_dollars === "number" && raw.book_dollars > 0
        ? raw.book_dollars
        : 1_000_000;
  return {
    bookDollars,
    current: parseHoldings(raw.current),
    proposed: parseHoldings(raw.proposed),
    currentUnit: isAllocationUnit(raw.currentUnit) ? raw.currentUnit : "pct",
    proposedUnit: isAllocationUnit(raw.proposedUnit) ? raw.proposedUnit : "pct",
  };
}

export function isOpaqueObject(
  payload: unknown,
): payload is Record<string, unknown> {
  return Boolean(payload) && typeof payload === "object" && !Array.isArray(payload);
}
