import type { ComparePeriodOut } from "@/lib/illustrate/compare-types";

export type YoYTaxChartPoint = {
  year: number;
  /** Null = no coverage that year. Still occupies a calendar slot. */
  value: number | null;
};

export type YoYTaxChartModel = {
  bars: YoYTaxChartPoint[];
  /** Year-over-year change (this year − prior). First year is null. */
  line: YoYTaxChartPoint[];
};

function numOrNull(value: unknown): number | null {
  if (value == null || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

/** Calendar-year bars sorted oldest → newest. Missing years stay as null slots. */
export function sortYoYPoints(points: YoYTaxChartPoint[]): YoYTaxChartPoint[] {
  return [...points].sort((a, b) => a.year - b.year);
}

/**
 * Descending YoY tax line: change vs the prior calendar year.
 * A year with no value, or no prior value, is null (gap in the line).
 */
export function computeYoyLine(bars: YoYTaxChartPoint[]): YoYTaxChartPoint[] {
  const sorted = sortYoYPoints(bars);
  return sorted.map((point, index) => {
    if (index === 0) return { year: point.year, value: null };
    const prior = sorted[index - 1];
    if (point.value == null || prior.value == null) {
      return { year: point.year, value: null };
    }
    return { year: point.year, value: point.value - prior.value };
  });
}

export function toYoYTaxChartModel(points: YoYTaxChartPoint[]): YoYTaxChartModel {
  const bars = sortYoYPoints(points);
  return { bars, line: computeYoyLine(bars) };
}

/** Map compare periods to calendar-year tax $ for one side (Dollar Illustration / compare). */
export function yoyBarsFromComparePeriods(
  periods: ComparePeriodOut[],
  side: "left" | "right",
): YoYTaxChartPoint[] {
  return sortYoYPoints(
    periods.map((period) => {
      const totals = period[side]?.totals;
      const matched = period[side]?.matched !== false;
      const tax = numOrNull(totals?.estimated_tax ?? totals?.estimated_tax_dollars);
      return {
        year: period.year,
        value: matched ? tax : null,
      };
    }),
  );
}
