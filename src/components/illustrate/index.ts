export { FundTaxDeltaCompare } from "@/components/illustrate/FundTaxDeltaCompare";
export type { FundTaxDeltaCompareProps } from "@/components/illustrate/FundTaxDeltaCompare";
export { TaxDeltaCompareCard } from "@/components/illustrate/TaxDeltaCompareCard";
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
  taxDragLineFromPeriods,
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
export type {
  CompareRequest,
  CompareResponse,
  CompareSideIn,
} from "@/lib/illustrate/compare-types";
export {
  fetchPerformance,
  postPerformanceGrowth,
} from "@/lib/performance/client";
export type {
  PerformanceGrowthRequest,
  PerformanceResponse,
} from "@/lib/performance/types";
