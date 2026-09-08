export { FundTaxDeltaCompare } from "@/components/illustrate/FundTaxDeltaCompare";
export type { FundTaxDeltaCompareProps } from "@/components/illustrate/FundTaxDeltaCompare";
export { TaxDeltaCompareCard } from "@/components/illustrate/TaxDeltaCompareCard";
export { YoYTaxChart } from "@/components/illustrate/YoYTaxChart";
export type { YoYTaxChartProps } from "@/components/illustrate/YoYTaxChart";
export {
  GrowthAndTaxDragModule,
} from "@/components/illustrate/GrowthAndTaxDragModule";
export type {
  GrowthAndTaxDragModuleProps,
  GrowthFundInput,
} from "@/components/illustrate/GrowthAndTaxDragModule";
export { MAX_GROWTH_FUNDS } from "@/lib/charts/series-colors";
export { GrowthOfXChart } from "@/components/illustrate/GrowthOfXChart";
export type { ChartUnit } from "@/components/illustrate/GrowthOfXChart";
export {
  TaxDragByYearChart,
  TaxYoYChart,
} from "@/components/illustrate/TaxDragByYearChart";
export type { TaxDragByYearChartProps } from "@/components/illustrate/TaxDragByYearChart";
export { toTaxDeltaCardModel } from "@/lib/illustrate/compare-map";
export {
  computeYoyLine,
  toYoYTaxChartModel,
  yoyBarsFromComparePeriods,
} from "@/lib/illustrate/yoy-tax-chart";
export type { YoYTaxChartModel, YoYTaxChartPoint } from "@/lib/illustrate/yoy-tax-chart";
export {
  TAX_DRAG_NA_LABEL,
  alignTaxDragYears,
  comparePeriodIsCovered,
  comparePeriodCalendarYear,
  formatTaxDragPoint,
  illustrationIsMatched,
  illustrationIsUnmatched,
  taxDragLineFromPeriods,
  taxDragValueFromIllustration,
  taxDragValueFromPeriodSide,
  toCompareTaxDragSeries,
  toNegativeTaxDrag,
  toTaxDragPeriods,
  toUpcomingSummary,
} from "@/lib/illustrate/tax-drag-chart";
export type {
  TaxDragFundSeries,
  TaxDragLinePoint,
  TaxDragMetric,
  TaxDragYearPoint,
  UpcomingSummary,
} from "@/lib/illustrate/tax-drag-chart";
export { postIllustrateCompare } from "@/lib/illustrate/compare-client";
export {
  compareSideFromFund,
  navFromFundMetadata,
  toDataApiCompareBody,
  withPortfolioHoldingNav,
} from "@/lib/illustrate/compare-request";
export { seedNavLookup } from "@/lib/illustrate/seed-nav";
export type {
  CompareRequest,
  CompareResponse,
  CompareSideIn,
} from "@/lib/illustrate/compare-types";
export { PortfolioCompare } from "@/components/illustrate/PortfolioCompare";
export type { PortfolioCompareProps } from "@/components/illustrate/PortfolioCompare";
export { HomepagePortfolioCompare } from "@/components/illustrate/HomepagePortfolioCompare";
export { TickerHistoryLink } from "@/components/illustrate/TickerHistoryLink";
export {
  FUND_HISTORY_HASH,
  firstSearchParam,
  fundHistoryPath,
  growthFundFromTicker,
  resolveFundView,
} from "@/lib/illustrate/fund-history";
export { HomepageFundCompare } from "@/components/illustrate/HomepageFundCompare";
export {
  defaultComparePeer,
  findFundByTicker,
} from "@/lib/illustrate/fund-compare-defaults";
export { postIllustratePortfolioCompare } from "@/lib/illustrate/portfolio-compare-client";
export {
  exportToPdf,
  renderPortfolioComparePrintHtml,
  toPortfolioCompareExportModel,
} from "@/lib/illustrate/portfolio-compare-export";
export type {
  PortfolioCompareExportModel,
  PortfolioCompareExportSide,
} from "@/lib/illustrate/portfolio-compare-export";
export type {
  PortfolioCompareRequest,
  PortfolioCompareResponse,
  PortfolioFundOption,
  PortfolioHoldingDraft,
} from "@/lib/illustrate/portfolio-compare-types";
export {
  fetchPerformance,
  postPerformanceGrowth,
} from "@/lib/performance/client";
export type {
  PerformanceGrowthRequest,
  PerformanceResponse,
} from "@/lib/performance/types";
export {
  requestTicker,
  requestTickerOnPortfolioMiss,
  notifyPortfolioTickerMiss,
  shouldReportPortfolioMiss,
  TICKER_REQUEST_SOURCES,
  noticeForTickerRequest,
} from "@/lib/request-ticker";
export type {
  RequestTickerArgs,
  TickerRequestSource,
  TickerRequestResult,
} from "@/lib/request-ticker";
