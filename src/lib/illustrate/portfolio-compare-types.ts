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

/**
 * Data contract shared by GET /distributions and portfolio upcoming payloads.
 * `as_of` stands in for announced until `announced_date` exists. Do not invent dates.
 */
export type PublicationStage =
  | "preliminary_estimate"
  | "updated_estimate"
  | "final"
  | "paid"
  | (string & {});

export type PortfolioDistributionDates = {
  /** Publication / snapshot date. Use as announced until announced_date exists. */
  as_of?: string | null;
  announced_date?: string | null;
  record_date?: string | null;
  ex_date?: string | null;
  payable_date?: string | null;
};

export type PortfolioDistributionRow = PortfolioDistributionDates & {
  distribution_dollars?: number | null;
  estimated_tax?: number | null;
  publication_stage?: PublicationStage | null;
};

/** Data API `holdings[].upcoming`. Null when uncovered or no upcoming dollars. */
export type PortfolioUpcoming = PortfolioDistributionRow;

/**
 * Data API `holdings[].paid_history[]`. Additive vs `upcoming`.
 * Same row shape; Data classifies paid/final or past prelim/updated.
 */
export type PortfolioPaidHistory = PortfolioDistributionRow;

export type PortfolioHoldingIllustrationTotals = {
  distribution_dollars: number;
  estimated_tax: number;
  estimated_tax_dollars?: number;
  effective_tax_on_holding?: number;
};

export type PortfolioHoldingIllustration = {
  components?: Array<
    PortfolioDistributionRow & {
      estimated_tax_dollars?: number | null;
    }
  >;
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
   * Array form is accepted when Data sends more than one snapshot.
   * Unpaid announced only — never a paid-history source.
   */
  upcoming?: PortfolioUpcoming | PortfolioUpcoming[] | null;
  /**
   * Prefer this for Paid History. Additive vs `upcoming`.
   * Present (including `[]`) = Data-classified paid rows; do not derive.
   * Omitted = older payload; fall back to illustration.components / distributions.
   */
  paid_history?: PortfolioPaidHistory | PortfolioPaidHistory[] | null;
  /**
   * Full distribution events for the holding (GET /distributions shape).
   * Temporary Paid History fallback until `paid_history[]` is live.
   */
  distributions?: PortfolioDistributionRow[];
  history?: PortfolioDistributionRow[];
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
