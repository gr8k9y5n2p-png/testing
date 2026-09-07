export { FundTaxDeltaCompare } from "@/components/illustrate/FundTaxDeltaCompare";
export type { FundTaxDeltaCompareProps } from "@/components/illustrate/FundTaxDeltaCompare";
export { TaxDeltaCompareCard } from "@/components/illustrate/TaxDeltaCompareCard";
export { YoYTaxChart } from "@/components/illustrate/YoYTaxChart";
export type { YoYTaxChartProps } from "@/components/illustrate/YoYTaxChart";
export { toTaxDeltaCardModel } from "@/lib/illustrate/compare-map";
export {
  computeYoyLine,
  toYoYTaxChartModel,
  yoyBarsFromComparePeriods,
} from "@/lib/illustrate/yoy-tax-chart";
export type { YoYTaxChartModel, YoYTaxChartPoint } from "@/lib/illustrate/yoy-tax-chart";
export { postIllustrateCompare } from "@/lib/illustrate/compare-client";
export type {
  CompareRequest,
  CompareResponse,
  CompareSideIn,
} from "@/lib/illustrate/compare-types";
export { PortfolioCompare } from "@/components/illustrate/PortfolioCompare";
export type { PortfolioCompareProps } from "@/components/illustrate/PortfolioCompare";
export { HomepagePortfolioCompare } from "@/components/illustrate/HomepagePortfolioCompare";
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
