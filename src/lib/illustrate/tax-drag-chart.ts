import { formatCompactUsd } from "@/lib/charts/money-axis";
import { formatUsd } from "@/lib/format";
import {
  TAX_DRAG_NA_LABEL,
  type TaxDragMetric,
} from "@/lib/illustrate/tax-drag-map";
export {
  gateCompareUpcoming,
  isAnnouncedStage,
  sideIsAnnounced,
  toUpcomingSummary,
  upcomingLooksLikeAnnualTax,
} from "@/lib/illustrate/upcoming-compare";
export type { UpcomingSummary } from "@/lib/illustrate/upcoming-compare";

export {
  TAX_DRAG_NA_LABEL,
  alignTaxDragYears,
  calendarYearFromUnknown,
  comparePeriodIsCovered,
  comparePeriodCalendarYear,
  illustrationIsMatched,
  illustrationIsUnmatched,
  taxDragLineFromPeriods,
  taxDragValueFromIllustration,
  taxDragValueFromPeriodSide,
  toCompareTaxDragSeries,
  toNegativeTaxDrag,
  toTaxDragPeriods,
  unionTaxDragYears,
} from "@/lib/illustrate/tax-drag-map";
export type {
  TaxDragFundSeries,
  TaxDragLinePoint,
  TaxDragMetric,
  TaxDragYearPoint,
} from "@/lib/illustrate/tax-drag-map";

export function formatTaxDragPoint(
  value: number | null | undefined,
  metric: TaxDragMetric,
): string {
  if (value == null) return TAX_DRAG_NA_LABEL;
  return formatTaxDragValue(value, metric);
}

export function formatTaxDragValue(
  value: number,
  metric: TaxDragMetric,
): string {
  if (metric === "effective_tax") {
    const pct = value * 100;
    if (Math.abs(pct) < 0.005) return "0%";
    const tenths = Number((Math.abs(pct) * 10).toFixed(6));
    const digits = Math.abs(pct) >= 10 || Number.isInteger(tenths) ? 1 : 2;
    return `${pct.toFixed(digits)}%`;
  }
  return Math.abs(value) >= 1000 ? formatCompactUsd(value) : formatUsd(value, 0);
}
