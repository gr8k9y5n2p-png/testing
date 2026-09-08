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
  /**
   * Shipped on Data PR #2 (`5d02120`):
   * - Unmatched: `matched: false` + money totals **null** (N/A, never $0)
   * - Published $0 / 0% NAV: `matched: true` + `"0.00"` → chart 0
   *
   * Live compare can also send `matched: true` with **null**
   * `totals.estimated_tax` while tax lives on the period `deltas.*`.
   * Chart that via `taxDragValueFromIllustration`’s delta fallback —
   * do not treat matched+null-totals as N/A when deltas have a number.
   */
  matched: boolean;
  holding_dollars?: number;
  components?: unknown[];
  totals?: {
    distribution_dollars?: number | null;
    estimated_tax?: number | null;
    estimated_tax_dollars?: number | null;
    estimated_tax_min?: number | null;
    estimated_tax_max?: number | null;
    federal_tax?: number | null;
    state_tax?: number | null;
    effective_tax_on_holding?: number | null;
  };
  notes?: string[];
  /** Some live payloads flatten tax onto the illustration root instead of totals. */
  estimated_tax?: number | null;
  estimated_tax_dollars?: number | null;
  effective_tax_on_holding?: number | null;
};

/** Optional per-side tax when Data omits illustration totals. */
export type CompareDeltaSide = {
  estimated_tax?: number | null;
  estimated_tax_dollars?: number | null;
  effective_tax_on_holding?: number | null;
};

export type CompareDeltas = {
  /** Null when either side is unmatched (Data PR #2) — not a $0 delta. */
  distribution_dollars: number | null;
  distribution_dollars_min?: number | null;
  distribution_dollars_max?: number | null;
  estimated_tax: number | null;
  estimated_tax_dollars?: number | null;
  estimated_tax_min?: number | null;
  estimated_tax_max?: number | null;
  federal_tax?: number | null;
  state_tax?: number | null;
  /** right − left, as a decimal rate (0.008 = 0.8%). Null if a side is N/A. */
  effective_tax_on_holding: number | null;
  effective_tax_on_holding_min?: number | null;
  effective_tax_on_holding_max?: number | null;
  /** Live payloads sometimes nest per-side tax under deltas.left / deltas.right. */
  left?: CompareDeltaSide | null;
  right?: CompareDeltaSide | null;
  left_estimated_tax?: number | null;
  right_estimated_tax?: number | null;
  left_estimated_tax_dollars?: number | null;
  right_estimated_tax_dollars?: number | null;
  left_effective_tax_on_holding?: number | null;
  right_effective_tax_on_holding?: number | null;
};

export type ComparePeriodOut = {
  year: number;
  as_of?: string | null;
  /** Period objects have no root `matched` — only `left.matched` / `right.matched`. */
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
