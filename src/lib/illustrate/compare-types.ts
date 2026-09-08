/**
 * Locked POST /illustrate/compare contract from PR #2
 * (`cursor/fund-distribution-ingest-api-85ed`). Field names must not drift.
 *
 * Deltas are **right − left** (Fund B − Fund A). See compare-map.ts for the
 * Fund A (left) display mapping used by the YoY tax-delta card.
 */

import type { IllustrateSelector, TaxRates } from "@/lib/illustrate/types";

export const COMPARE_SUMMARY_HOLDING_DOLLARS = 10_000;

export type CompareMode = "fund_vs_fund" | "yoy";

export type CompareSelectors = IllustrateSelector & {
  fund_name?: string;
  as_of?: string;
  publication_stage?: string;
};

export type CompareSideIn = {
  label?: string;
  selectors?: CompareSelectors;
  distribution_ids?: string[];
  holding_dollars?: number;
  /** Required by Data when matched rows are `per_share`. Omit for % of NAV. */
  nav_per_share?: number | null;
  shares?: number | null;
};

export type ComparePeriodIn = {
  year: number;
  as_of?: string | null;
};

export type CompareRequest = {
  mode?: CompareMode | null;
  holding_dollars: number;
  tax_rates?: Partial<TaxRates> | Record<string, never>;
  combine_state_with_federal?: boolean;
  latest_as_of_only?: boolean;
  left?: CompareSideIn;
  right?: CompareSideIn;
  selectors?: CompareSelectors;
  periods?: ComparePeriodIn[];
  /** Top-level NAV for YoY (same fund). Per-side NAV wins in fund_vs_fund. */
  nav_per_share?: number | null;
  shares?: number | null;
};

export type CompareIllustration = {
  label: string;
  matched: boolean;
  holding_dollars?: number;
  components?: unknown[];
  totals?: {
    distribution_dollars?: number;
    estimated_tax?: number;
    estimated_tax_dollars?: number;
    effective_tax_on_holding?: number;
  };
  notes?: string[];
};

export type CompareDeltas = {
  distribution_dollars: number;
  distribution_dollars_min?: number | null;
  distribution_dollars_max?: number | null;
  estimated_tax: number;
  estimated_tax_min?: number | null;
  estimated_tax_max?: number | null;
  federal_tax?: number;
  state_tax?: number;
  /** right − left, as a decimal rate (0.008 = 0.8%). Chart this field. */
  effective_tax_on_holding: number;
  effective_tax_on_holding_min?: number | null;
  effective_tax_on_holding_max?: number | null;
};

export type ComparePeriodOut = {
  year: number;
  as_of?: string | null;
  left: CompareIllustration;
  right: CompareIllustration;
  deltas: CompareDeltas;
};

export type CompareCommonInception = {
  from_year?: number | null;
  to_year?: number | null;
  from_as_of?: string | null;
  to_as_of?: string | null;
};

export type CompareUpcomingDistribution = {
  left_dollars?: number | null;
  right_dollars?: number | null;
  /** right − left, always at the $10k summary holding. */
  delta_dollars?: number | null;
  left_as_of?: string | null;
  right_as_of?: string | null;
  left_publication_stage?: string | null;
  right_publication_stage?: string | null;
};

export type CompareSummary = {
  normalized_holding_dollars: number;
  /** right − left estimated tax, scaled to $10k. */
  total_tax_difference: number;
  /** Mean of period effective_tax_on_holding deltas (decimal rate). */
  annualized_tax_drag_delta: number;
  /** right − left distribution dollars, scaled to $10k. */
  distribution_dollars_difference: number;
  periods_compared: number;
  common_inception: CompareCommonInception;
  upcoming_taxable_distribution?: CompareUpcomingDistribution | null;
};

export type CompareResponse = {
  mode: CompareMode;
  left?: CompareIllustration | null;
  right?: CompareIllustration | null;
  deltas?: CompareDeltas | null;
  periods: ComparePeriodOut[];
  summary: CompareSummary;
  notes: string[];
  /** Present on the local mock only — not part of the Data API. */
  source?: "mock" | "live";
};
