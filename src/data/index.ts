export { getDistributionRepository, SeedDistributionRepository } from "./repository";
export { aggregateDistributions } from "./aggregate-distributions";
export type { DataDistribution } from "./aggregate-distributions";
export {
  hideUpcomingAmounts,
  mergeFundLists,
  mergeFundWithDistributions,
  paidEventsForFund,
  preferFinalPaidEvents,
} from "./hydrate-funds";
export {
  buildSearchTableFunds,
  computeCategoryAverages,
  currentPaidHistoryYear,
  emptyHighlightSets,
  fundFromPaidEvent,
  getFacets,
  getHighlights,
  highlightsCalendarYear,
  HIGHLIGHTS_MIN_YEAR_PEERS,
  OUTLIER_THRESHOLD_PP,
  paidHistoryViews,
  paidHistoryYearOf,
  pickHighlightsCalendarYear,
  searchFunds,
  splitFundsByBucket,
  withPeerContext,
} from "./queries";
export {
  distributionBucket,
  eventDateOf,
  hasDisclosedUpcomingAmount,
  isoDate,
  isPastDistribution,
  isStaleAnnouncedOnly,
  isUpcomingFund,
  publicationStageLabel,
} from "./distribution-bucket";
export { SAMPLE_FUNDS } from "./seed";
export {
  collectTaxYearsFromFunds,
  mergeTaxYears,
  taxYearsFromPayload,
} from "./tax-years";
export {
  FUND_PAGE_SIZE,
  FUND_PAGE_SIZE_MAX,
  clampOffset,
  clampPageSize,
  paginateViews,
  parseFundPageQuery,
} from "./pagination";
export type { FundPageQuery, FundPageResult } from "./pagination";
export type {
  DistributionBucket,
  DistributionRepository,
  Facets,
  FundCategory,
  FundEstimate,
  FundEstimateView,
  FundFamily,
  HighlightSets,
  PaidDistributionEvent,
  PublicationStage,
  SearchFilters,
} from "./types";
export { DATA_SOURCE, FUND_CATEGORIES, FUND_FAMILIES } from "./types";
