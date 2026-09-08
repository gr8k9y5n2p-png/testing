/**
 * Locked POST /illustrate/portfolio/compare contract from PR #2
 * (`cursor/fund-distribution-ingest-api-85ed`). Field names must not drift.
 *
 * v1 is a single snapshot: Current vs Proposed Allocation. Do not send periods[].
 * Deltas are **proposed − current**. Format more/less tax client-side.
 */

import type { TaxRates } from "@/lib/illustrate/types";

export const PORTFOLIO_COMPARE_BOOK_DOLLARS = 1_000_000;

export type PortfolioFundOption = {
  ticker: string;
  fundName: string;
  family?: string;
};

export type PortfolioHoldingIn = {
  ticker?: string;
  fund_family?: string;
  fund_identifier?: string;
  fund_name?: string;
  /** UI percent 0–100. Mutually exclusive with holding_dollars. */
  weight_pct?: number | null;
  holding_dollars?: number | null;
  book_dollars?: number | null;
  distribution_ids?: string[];
  nav_per_share?: number | null;
  shares?: number | null;
};

export type PortfolioCompareSideIn = {
  label?: string;
  book_dollars?: number | null;
  holdings: PortfolioHoldingIn[];
};

export type IllustrationSnapshot = {
  prefer_publication_stages?: string[];
  as_of?: string | null;
  latest_as_of_only?: boolean;
};

export type PortfolioCompareRequest = {
  current: PortfolioCompareSideIn;
  proposed: PortfolioCompareSideIn;
  tax_rates?: Partial<TaxRates> | Record<string, never>;
  combine_state_with_federal?: boolean;
  snapshot?: IllustrationSnapshot;
};

/** Data API `holdings[].upcoming`. Null when uncovered or no upcoming dollars. */
export type PortfolioUpcoming = {
  distribution_dollars?: number | null;
  estimated_tax?: number | null;
  as_of?: string | null;
  publication_stage?: string | null;
};

export type PortfolioHoldingIllustrationTotals = {
  distribution_dollars: number;
  estimated_tax: number;
  estimated_tax_dollars?: number;
  effective_tax_on_holding?: number;
};

export type PortfolioHoldingIllustration = {
  components?: Array<{
    distribution_dollars?: number | null;
    estimated_tax?: number | null;
    estimated_tax_dollars?: number | null;
    as_of?: string | null;
    publication_stage?: string | null;
    ex_date?: string | null;
  }>;
  totals?: PortfolioHoldingIllustrationTotals;
};

export type PortfolioHoldingOut = {
  holding_index: number;
  ticker?: string | null;
  fund_identifier?: string | null;
  fund_family?: string | null;
  fund_name?: string | null;
  holding_dollars: number;
  weight_pct?: number | null;
  covered: boolean;
  publication_stage_used?: string | null;
  warnings: string[];
  illustration?: PortfolioHoldingIllustration | null;
  /**
   * Prefer this for bar charts + heat tables.
   * `null` = no upcoming (do not derive). Omitted = older payload; derive from illustration.
   */
  upcoming?: PortfolioUpcoming | null;
  gap_reason?: string | null;
};

export type PortfolioCoverageOut = {
  dollars_total: number;
  dollars_covered: number;
  dollars_uncovered: number;
  coverage_pct: number;
  holdings_covered?: number;
  holdings_uncovered?: number;
};

export type PortfolioGapOut = {
  holding_index?: number;
  ticker?: string | null;
  fund_identifier?: string | null;
  fund_family?: string | null;
  fund_name?: string | null;
  holding_dollars: number;
  reason: string;
};

export type PortfolioTotalsOut = {
  distribution_dollars: number;
  distribution_dollars_min?: number | null;
  distribution_dollars_max?: number | null;
  estimated_tax: number;
  estimated_tax_dollars?: number;
  estimated_tax_min?: number | null;
  estimated_tax_max?: number | null;
  federal_tax?: number;
  state_tax?: number;
  effective_tax_on_holding: number;
};

export type PortfolioAllocationOut = {
  label: string;
  holdings: PortfolioHoldingOut[];
  totals: PortfolioTotalsOut;
  coverage: PortfolioCoverageOut;
  gaps: PortfolioGapOut[];
  warnings: string[];
  notes?: string[];
};

export type PortfolioCompareDeltas = {
  /** proposed − current, at book dollars. */
  estimated_tax: number;
  distribution_dollars: number;
  effective_tax_on_holding: number;
  coverage_pct: number;
  estimated_tax_min?: number | null;
  estimated_tax_max?: number | null;
  distribution_dollars_min?: number | null;
  distribution_dollars_max?: number | null;
};

export type PortfolioCompareSummary = {
  normalized_book_dollars: number;
  estimated_tax: number;
  distribution_dollars: number;
  effective_tax_on_holding: number;
  coverage_pct: number;
};

export type PortfolioCompareResponse = {
  current: PortfolioAllocationOut;
  proposed: PortfolioAllocationOut;
  deltas: PortfolioCompareDeltas;
  summary: PortfolioCompareSummary;
  notes: string[];
  /** Present on the local mock only — not part of the Data API. */
  source?: "mock" | "live";
};

export type AllocationUnit = "pct" | "usd";

export type PortfolioHoldingDraft = {
  id: string;
  ticker: string;
  fundName: string;
  family?: string;
  /** UI percent 0–100. */
  weightPct: number;
  holdingDollars: number;
};
