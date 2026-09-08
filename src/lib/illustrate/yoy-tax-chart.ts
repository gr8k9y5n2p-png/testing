import type { ComparePeriodOut } from "@/lib/illustrate/compare-types";
import { taxDragValueFromPeriodSide } from "@/lib/illustrate/tax-drag-chart";

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

/** Calendar-year bars sorted oldest → newest. Missing years stay as null slots. */
export function sortYoYPoints(points: YoYTaxChartPoint[]): YoYTaxChartPoint[] {
  return [...points].sort((a, b) => a.year - b.year);
}

/**
 * Descending YoY tax line: change vs the last announced calendar year.
 * Unannounced years stay null so the line can skip a gap.
 */
export function computeYoyLine(bars: YoYTaxChartPoint[]): YoYTaxChartPoint[] {
  const sorted = sortYoYPoints(bars);
  let lastAnnounced: number | null = null;
  return sorted.map((point) => {
    if (point.value == null) return { year: point.year, value: null };
    if (lastAnnounced == null) {
      lastAnnounced = point.value;
      return { year: point.year, value: null };
    }
    const delta = point.value - lastAnnounced;
    lastAnnounced = point.value;
    return { year: point.year, value: delta };
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
    periods.map((period) => ({
      year: period.year,
      value: taxDragValueFromPeriodSide(period, side, "tax_dollars"),
    })),
  );
}
