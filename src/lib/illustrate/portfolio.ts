import {
  allowDemoEngine,
  getDataApiBaseUrl,
  sameOriginApiUrl,
} from "@/lib/data-api/config";
import { userFacingNotes } from "@/lib/illustrate/user-facing-notes";
import type { TaxRates } from "@/lib/illustrate/types";

export type PortfolioHoldingIn = {
  holding_dollars: number;
  ticker?: string;
  fund_family?: string;
  fund_identifier?: string;
  fund_name?: string;
  distribution_ids?: string[];
  nav_per_share?: number | null;
};

export type PortfolioIllustrateRequest = {
  holdings: PortfolioHoldingIn[];
  tax_rates?: TaxRates;
  combine_state_with_federal?: boolean;
};

export type PortfolioCoverage = {
  dollars_total: number;
  dollars_covered: number;
  dollars_uncovered: number;
  coverage_pct: number;
};

export type PortfolioGap = {
  ticker?: string | null;
  fund_family?: string | null;
  holding_dollars: number;
  reason: string;
};

export type PortfolioIllustrateResponse = {
  coverage: PortfolioCoverage;
  gaps: PortfolioGap[];
  warnings: string[];
};

function num(value: unknown, fallback = 0): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export function normalizePortfolioResponse(
  raw: Record<string, unknown>,
): PortfolioIllustrateResponse {
  const coverageRaw = (raw.coverage ?? {}) as Record<string, unknown>;
  const gapsRaw = Array.isArray(raw.gaps) ? raw.gaps : [];
  const warnings = userFacingNotes([
    ...(Array.isArray(raw.warnings) ? raw.warnings : []),
    ...(Array.isArray(raw.notes) ? raw.notes : []),
  ]);

  return {
    coverage: {
      dollars_total: num(coverageRaw.dollars_total),
      dollars_covered: num(coverageRaw.dollars_covered),
      dollars_uncovered: num(coverageRaw.dollars_uncovered),
      coverage_pct: num(coverageRaw.coverage_pct),
    },
    gaps: gapsRaw.map((item) => {
      const row = item as Record<string, unknown>;
      return {
        ticker: row.ticker == null ? null : String(row.ticker),
        fund_family: row.fund_family == null ? null : String(row.fund_family),
        holding_dollars: num(row.holding_dollars),
        reason: String(row.reason ?? ""),
      };
    }),
    warnings,
  };
}

export async function postIllustratePortfolio(
  request: PortfolioIllustrateRequest,
  init?: { signal?: AbortSignal },
): Promise<PortfolioIllustrateResponse> {
  const endpoint = sameOriginApiUrl("/illustrate/portfolio");
  const remote = !allowDemoEngine();

  async function post(url: string) {
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(request),
      signal: init?.signal,
    });
  }

  const response = await post(endpoint);
  if (remote && response.status >= 500) {
    throw new Error(`Portfolio illustrate failed (${response.status})`);
  }

  if (!response.ok) {
    throw new Error(`Portfolio illustrate failed (${response.status})`);
  }
  const raw = (await response.json()) as Record<string, unknown>;
  return normalizePortfolioResponse(raw);
}

export { getDataApiBaseUrl };
