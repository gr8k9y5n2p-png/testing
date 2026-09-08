/**
 * Domain model for estimated taxable fund distributions.
 *
 * This layer is intentionally persistence-agnostic so a database or
 * manager-API ingest can replace the in-module seed later.
 */

export const FUND_FAMILIES = [
  "American Funds",
  "Vanguard",
  "Fidelity",
  "T. Rowe Price",
] as const;

export type FundFamily = (typeof FUND_FAMILIES)[number];

export const FUND_CATEGORIES = [
  "Large Growth",
  "Large Value",
  "Large Blend",
  "Foreign Large Blend",
  "Diversified Emerging Markets",
  "Small Blend",
  "Intermediate Core Bond",
  "High Yield Bond",
  "Muni National Intermediate",
  "Moderate Allocation",
] as const;

export type FundCategory = (typeof FUND_CATEGORIES)[number];

import type { DistributionBucket, PaidDistributionEvent } from "./distribution-bucket";

export type { DistributionBucket, PaidDistributionEvent } from "./distribution-bucket";

/** GET /distributions publication_stage. Do not invent announced_date. */
export const PUBLICATION_STAGES = [
  "preliminary_estimate",
  "updated_estimate",
  "final",
  "paid",
] as const;

export type PublicationStage = (typeof PUBLICATION_STAGES)[number];

export interface FundEstimate {
  id: string;
  fundName: string;
  ticker: string;
  cusip: string;
  family: string;
  category: string;
  shareClass: string;
  /** Latest reported NAV used for the % of NAV estimate. */
  nav: number;
  /** Combined estimated taxable distribution, $ per share. */
  estimatedDistributionAmount: number;
  /** Ordinary income / dividend portion, $ per share. */
  estimatedOrdinaryIncome: number;
  /** Short + long-term capital gains portion, $ per share. */
  estimatedCapitalGains: number;
  /** Combined estimate as a percent of NAV. */
  estimatedDistributionPctNav: number;
  /** Date the manager published this estimate (ISO date). */
  publishedAt: string;
  /**
   * GET /distributions `as_of`. UI copy labels this Announced until a
   * literal `announced_date` exists — do not invent that field.
   */
  asOfDate: string;
  /** GET /distributions `record_date`. */
  recordDate: string | null;
  /** GET /distributions `ex_date`. */
  exDate: string | null;
  /** GET /distributions `payable_date`. */
  payableDate: string | null;
  publicationStage: string | null;
  bucket: DistributionBucket;
  /** Paid / final-past snapshots for this ticker. Never mixed into upcoming. */
  paidHistory: PaidDistributionEvent[];
  distributionYear: number;
  /**
   * False when GET /funds says has_estimate=false (or amounts are unknown).
   * UI must show "—" — never invent $0 / 0%.
   */
  hasEstimate?: boolean;
}

export interface FundEstimateView extends FundEstimate {
  /** Mean estimatedDistributionPctNav for peers in the same category and year. */
  categoryAveragePctNav: number;
  /** Percentage-point gap vs. the category average (positive = above). */
  vsCategoryPctNav: number;
}

export interface SearchFilters {
  query?: string;
  family?: string;
  category?: string;
  year?: number;
}

export interface Facets {
  families: string[];
  categories: string[];
  years: number[];
}

export interface HighlightSets {
  mostRecent: FundEstimateView[];
  largest: FundEstimateView[];
  aboveCategory: FundEstimateView[];
  belowCategory: FundEstimateView[];
}

export interface FundPage {
  items: FundEstimateView[];
  total: number;
  limit: number;
  offset: number;
}

export interface DistributionRepository {
  search(filters?: SearchFilters): Promise<FundEstimateView[]>;
  searchPage?(
    query?: SearchFilters & {
      limit?: number;
      offset?: number;
      sort?: string;
      direction?: "asc" | "desc";
    },
  ): Promise<FundPage>;
  highlights(limit?: number): Promise<HighlightSets>;
  facets(): Promise<Facets>;
  getById(id: string): Promise<FundEstimateView | null>;
}

/** Sample-data marker used in API payloads and UI copy. */
export const DATA_SOURCE = {
  kind: "sample" as const,
  label: "Sample / demo data",
  notice:
    "Figures are illustrative seed data for product development. They are not live fund-manager filings and should not be used for tax, trading, or client reporting.",
};
