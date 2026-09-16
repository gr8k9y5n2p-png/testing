/**
 * Modules-owned Portfolio Save/Open helpers.
 *
 * Persist via the shared #190 `/api/saved-assets` contract (`type: "portfolio"`).
 * Do not invent tickers, fund names, NAVs, or estimates — catalog hints only.
 */

import { COMPARE_SLOT_COUNT, filledCompareTickers } from "./compare-workspace.ts";
import { PORTFOLIO_COMPARE_BOOK_DOLLARS } from "./portfolio-compare-types.ts";
import type { PortfolioFundOption } from "./portfolio-compare-types.ts";
import {
  parsePortfolioBooksPayload,
  toPortfolioAssetPayload,
  type PortfolioAssetPayload,
  type PortfolioBooksSnapshot,
  type PortfolioHoldingSnapshot,
} from "../saved-assets/payloads.ts";

export type CompareFundHint = Pick<
  PortfolioFundOption,
  "ticker" | "fundName" | "family" | "nav"
>;

export type CompareWorkspaceSnapshot = {
  tickers: Array<string | undefined | null>;
  holdingDollars: number;
};

/** Extra books keys Compare writes so Open can restore slots + dollars. */
export type ComparePortfolioBooks = PortfolioBooksSnapshot & {
  compareSlots: string[];
  compareHoldingDollars: number;
};

export function emptyPortfolioBooks(
  bookDollars = PORTFOLIO_COMPARE_BOOK_DOLLARS,
): PortfolioBooksSnapshot {
  return {
    bookDollars: bookDollars > 0 ? bookDollars : PORTFOLIO_COMPARE_BOOK_DOLLARS,
    current: [],
    proposed: [],
    currentUnit: "pct",
    proposedUnit: "pct",
  };
}

export function holdingHasTicker(
  row: { ticker?: string | null } | null | undefined,
): boolean {
  return Boolean(row?.ticker?.trim());
}

/** True when Current or Proposed has at least one ticker — never seed demo funds. */
export function portfolioBooksAreSavable(
  books: Pick<PortfolioBooksSnapshot, "current" | "proposed"> | null | undefined,
): boolean {
  if (!books) return false;
  return (
    books.current.some(holdingHasTicker) || books.proposed.some(holdingHasTicker)
  );
}

export function compareWorkspaceIsSavable(
  tickers: Array<string | undefined | null> = [],
): boolean {
  return filledCompareTickers(tickers).length > 0;
}

export function portfolioSavePayloadFromBooks(
  books: PortfolioBooksSnapshot | null | undefined,
  fallbackBookDollars = PORTFOLIO_COMPARE_BOOK_DOLLARS,
): PortfolioAssetPayload {
  return toPortfolioAssetPayload(books ?? emptyPortfolioBooks(fallbackBookDollars));
}

/**
 * Open-dialog subtitle. Reads `{ version, books }` or a flat books object.
 * Counts stored holdings only — does not invent rows.
 */
export function savedPortfolioSubtitle(payload: unknown): string {
  const parsed = parsePortfolioBooksPayload(payload);
  const current = parsed?.current.length ?? 0;
  const proposed = parsed?.proposed.length ?? 0;
  return `Current ${current} · Proposed ${proposed}`;
}

function catalogHint(
  ticker: string,
  funds: CompareFundHint[] = [],
): CompareFundHint | undefined {
  const key = ticker.trim().toUpperCase();
  return funds.find((fund) => fund.ticker.trim().toUpperCase() === key);
}

/**
 * Snapshot Compare slots as a portfolio book. Each filled ticker is a holding
 * at the shared dollars-invested amount. Names / NAV come from the catalog
 * when present; otherwise ticker only — never invented.
 */
export function compareWorkspaceToPortfolioBooks(
  snapshot: CompareWorkspaceSnapshot,
  funds: CompareFundHint[] = [],
): ComparePortfolioBooks {
  const tickers = filledCompareTickers(snapshot.tickers);
  const holdingDollars =
    typeof snapshot.holdingDollars === "number" && snapshot.holdingDollars > 0
      ? snapshot.holdingDollars
      : 0;
  const count = tickers.length;
  const bookDollars = count > 0 && holdingDollars > 0 ? holdingDollars * count : holdingDollars;
  const weightPct = count > 0 ? 100 / count : 0;
  const current: PortfolioHoldingSnapshot[] = tickers.map((ticker) => {
    const hint = catalogHint(ticker, funds);
    const fundName = hint?.fundName?.trim();
    const family = hint?.family?.trim();
    const nav = hint?.nav != null && hint.nav > 0 ? hint.nav : null;
    return {
      id: ticker,
      ticker,
      fundName: fundName || ticker,
      ...(family ? { family } : {}),
      nav,
      weightPct,
      holdingDollars,
    };
  });
  return {
    bookDollars: bookDollars > 0 ? bookDollars : PORTFOLIO_COMPARE_BOOK_DOLLARS,
    current,
    proposed: [],
    currentUnit: "usd",
    proposedUnit: "pct",
    compareSlots: tickers,
    compareHoldingDollars: holdingDollars,
  };
}

function readCompareExtras(payload: unknown): {
  compareSlots: string[];
  compareHoldingDollars: number | null;
} {
  if (!payload || typeof payload !== "object") {
    return { compareSlots: [], compareHoldingDollars: null };
  }
  const root = payload as {
    books?: unknown;
    compareSlots?: unknown;
    compareHoldingDollars?: unknown;
  };
  const books =
    root.books && typeof root.books === "object" && !Array.isArray(root.books)
      ? (root.books as typeof root)
      : root;
  const rawSlots = Array.isArray(books.compareSlots) ? books.compareSlots : [];
  const compareSlots = rawSlots.filter(
    (item): item is string => typeof item === "string" && Boolean(item.trim()),
  );
  const compareHoldingDollars =
    typeof books.compareHoldingDollars === "number" &&
    books.compareHoldingDollars > 0
      ? books.compareHoldingDollars
      : null;
  return { compareSlots, compareHoldingDollars };
}

/**
 * Load a saved portfolio into Compare slots.
 *
 * Tickers come from stored `compareSlots` or Current then Proposed holdings.
 * Dollars invested restore from `compareHoldingDollars` when present; a
 * Portfolio-originated $1M book does not overwrite Compare’s holding.
 * Never invents tickers or estimates.
 */
export function portfolioBooksToCompareWorkspace(
  payload: unknown,
  fallbackHoldingDollars: number,
): CompareWorkspaceSnapshot {
  const extras = readCompareExtras(payload);
  const parsed = parsePortfolioBooksPayload(payload);
  const fromBooks = parsed
    ? [...parsed.current, ...parsed.proposed].map((row) => row.ticker)
    : [];
  const tickers = filledCompareTickers([
    ...extras.compareSlots,
    ...fromBooks,
  ]).slice(0, COMPARE_SLOT_COUNT);
  const holdingDollars =
    extras.compareHoldingDollars != null
      ? extras.compareHoldingDollars
      : fallbackHoldingDollars;
  return { tickers, holdingDollars };
}
