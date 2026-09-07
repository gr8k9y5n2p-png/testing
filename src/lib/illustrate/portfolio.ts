import { getDataApiBaseUrl } from "@/lib/data-api/config";
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

export async function postIllustratePortfolio(
  request: PortfolioIllustrateRequest,
): Promise<PortfolioIllustrateResponse> {
  const base = getDataApiBaseUrl();
  const endpoint = base ? `${base}/illustrate/portfolio` : "/api/illustrate/portfolio";
  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    throw new Error(`Portfolio illustrate failed (${response.status})`);
  }
  return (await response.json()) as PortfolioIllustrateResponse;
}
