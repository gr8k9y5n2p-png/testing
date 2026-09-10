/**
 * Parse Data / BFF GET /funds/lookup. Keep free of `@/` for node:test.
 */

import { mapFundsApiItem, type FundsApiItem } from "../../data/funds-list.ts";
import type { FundEstimateView } from "../../data/types.ts";
import {
  resolveCoverageStatus,
  type CoverageStatus,
} from "./coverage-status.ts";
import { normalizeTickerSymbol } from "./request-ticker.ts";

export type FundLookupFound = {
  kind: "found";
  fund: FundEstimateView;
  coverageStatus: CoverageStatus;
};

export type FundLookupMiss = {
  kind: "not_in_universe";
  ticker: string;
  addToUniverse: "POST /request/ticker";
};

export type FundLookupUnavailable = {
  kind: "unavailable";
};

export type FundLookupResult =
  | FundLookupFound
  | FundLookupMiss
  | FundLookupUnavailable;

function isFundsApiItem(row: unknown): row is FundsApiItem {
  if (!row || typeof row !== "object") return false;
  const record = row as Record<string, unknown>;
  return (
    "fund_name" in record ||
    "fund_identifier" in record ||
    "fundName" in record ||
    "ticker" in record ||
    "fund" in record
  );
}

export function parseFundLookupResponse(
  status: number,
  body: unknown,
  ticker: string,
): FundLookupResult {
  const key = normalizeTickerSymbol(ticker);
  if (status >= 500 || status === 0) return { kind: "unavailable" };
  const record = body && typeof body === "object" ? (body as Record<string, unknown>) : {};
  const nested = record.fund && typeof record.fund === "object" ? record.fund : body;
  const published = resolveCoverageStatus({
    coverageStatus:
      record.coverage_status ??
      record.coverageStatus ??
      (nested && typeof nested === "object"
        ? (nested as { coverage_status?: unknown; coverageStatus?: unknown })
            .coverage_status ??
          (nested as { coverageStatus?: unknown }).coverageStatus
        : undefined),
    foundInFunds: status === 200,
  });
  if (status === 404 || published === "not_in_universe") {
    return {
      kind: "not_in_universe",
      ticker: String(record.ticker ?? key).toUpperCase(),
      addToUniverse: "POST /request/ticker",
    };
  }
  if (status === 200) {
    const mapped =
      nested &&
      typeof nested === "object" &&
      typeof (nested as { fundName?: unknown }).fundName === "string" &&
      typeof (nested as { ticker?: unknown }).ticker === "string"
        ? (nested as FundEstimateView)
        : isFundsApiItem(nested)
          ? mapFundsApiItem(nested)
          : isFundsApiItem(body)
            ? mapFundsApiItem(body)
            : null;
    if (mapped) {
      return {
        kind: "found",
        fund: mapped,
        coverageStatus: resolveCoverageStatus({
          coverageStatus: mapped.coverageStatus ?? published,
          foundInFunds: true,
          hasEstimate: mapped.hasEstimate,
        }),
      };
    }
  }
  if (status >= 400) return { kind: "unavailable" };
  return { kind: "not_in_universe", ticker: key, addToUniverse: "POST /request/ticker" };
}
