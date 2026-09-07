/**
 * Locked draft contract for POST /illustrate (Data team + Aftertax UI).
 * Field names must not drift. The browser never computes tax; it only POSTs this shape.
 */

export const DEFAULT_TAX_RATES: TaxRates = {
  ordinary_income: 0.37,
  long_term_capital_gains: 0.2,
  short_term_capital_gains: 0.37,
  qualified_dividend: 0.2,
  state: 0,
};

/** Advisor-facing starting rates in the panel (sent explicitly on every request). */
export const UI_DEFAULT_TAX_RATES: TaxRates = {
  ordinary_income: 0.37,
  long_term_capital_gains: 0.2,
  short_term_capital_gains: 0.37,
  qualified_dividend: 0.2,
  state: 0.05,
};

export const DEFAULT_HOLDING_DOLLARS = 1_000_000;

export type TaxRates = {
  ordinary_income: number;
  long_term_capital_gains: number;
  short_term_capital_gains: number;
  qualified_dividend: number;
  state: number;
};

export type IllustrateSelector = {
  fund_family?: string;
  fund_identifier?: string;
};

export type IllustrateRequest = {
  holding_dollars: number;
  distribution_ids?: string[];
  selector?: IllustrateSelector;
  nav_per_share?: number | null;
  tax_rates?: TaxRates;
  combine_state_with_federal?: boolean;
};

export type IllustrationComponent = {
  distribution_id: string;
  fund_name: string;
  estimate_type: string;
  amount_unit: string;
  publication_stage: string | null;
  distribution_dollars: number | null;
  distribution_dollars_min: number | null;
  distribution_dollars_max: number | null;
  rate_key: string;
  federal_rate: number;
  state_rate: number;
  effective_rate: number;
  estimated_tax_dollars: number | null;
  estimated_tax_dollars_min: number | null;
  estimated_tax_dollars_max: number | null;
  notes: string | null;
};

export type IllustrationTotals = {
  distribution_dollars: number;
  distribution_dollars_min: number | null;
  distribution_dollars_max: number | null;
  estimated_tax_dollars: number;
  estimated_tax_dollars_min: number | null;
  estimated_tax_dollars_max: number | null;
};

export type IllustrateResponse = {
  tax_rates_applied: TaxRates;
  components: IllustrationComponent[];
  totals: IllustrationTotals;
  warnings: string[];
};

export type IllustrateErrorBody = {
  detail: string;
  code?: string;
};

/**
 * estimate_type → TaxRates key (locked mapping).
 * `total` is treated as ordinary_income unless the row is skipped.
 */
export const RATE_MAPPING: Record<string, keyof TaxRates> = {
  ordinary_income: "ordinary_income",
  special_dividend: "ordinary_income",
  return_of_capital: "ordinary_income",
  other: "ordinary_income",
  long_term_capital_gains: "long_term_capital_gains",
  total_capital_gains: "long_term_capital_gains",
  short_term_capital_gains: "short_term_capital_gains",
  qualified_short_term_gains: "short_term_capital_gains",
  qualified_dividend: "qualified_dividend",
  total: "ordinary_income",
};

export const AMOUNT_UNITS = {
  percent_of_nav: "percent_of_nav",
  per_share: "per_share",
} as const;

export type AmountUnit = (typeof AMOUNT_UNITS)[keyof typeof AMOUNT_UNITS];
