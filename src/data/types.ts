/**
 * Domain model for estimated taxable fund distributions.
 *
 * Live Search / Sample Estimates read GET /funds for identity plus
 * GET /distributions for paid / final history and unpaid Upcoming amounts.
 * `seed.ts` is test/mock scoped and must not backfill those UI paths.
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
  /**
   * Latest weekly NAV from GET /funds `nav_per_share`.
   * 0 / omitted means unknown — never invent a print.
   */
  nav: number;
  /** GET /funds `nav_as_of`. Null when weekly NAV is unknown. */
  navAsOf?: string | null;
  /** GET /funds `nav_source` (yahoo_last_close, issuer, fixture). */
  navSource?: string | null;
  /**
   * GET /distributions `nav_on_distribution_day` for this snapshot.
   * Historical % of NAV only. Never today's weekly NAV.
   */
  navOnDistributionDay?: number | null;
  navOnDistributionDayAsOf?: string | null;
  navOnDistributionDaySource?: string | null;
  /**
   * Sum of issuer-published `amount_unit=percent_of_nav` characters.
   * Null when none were published — not the same as 0%.
   */
  publishedPctOfNav?: number | null;
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
   * Catalog hint (`GET /funds.has_estimate`). False means unpaid Upcoming is
   * none. True is not enough to list a fund in Upcoming — that still needs a
   * real unpaid /distributions estimate that has not paid. Paid history must
   * still render paid/final rows when this flag is false. Upcoming UI shows
   * "—" / Undisclosed — never invent $0 from the catalog flag or history.
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

/** Live Data API marker used in Search / Sample Estimates payloads and UI copy. */
export const DATA_SOURCE = {
  kind: "live" as const,
  label: "Live Data API",
  notice:
    "Search and Sample Estimates use GET /funds for identity and GET /distributions for unpaid Upcoming. Missing or uncovered values stay empty, N/A, or Undisclosed — they are not filled from seed or demo math. Historical paid distributions live on Compare / Portfolio Growth & Tax.",
};
