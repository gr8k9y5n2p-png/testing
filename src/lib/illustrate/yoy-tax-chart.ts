import type { ComparePeriodOut } from "@/lib/illustrate/compare-types";
import { illustrationIsMatched } from "@/lib/illustrate/tax-drag-chart";

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
    periods.map((period) => {
      const totals = period[side]?.totals;
      const matched = illustrationIsMatched(period[side]);
      const tax = numOrNull(totals?.estimated_tax ?? totals?.estimated_tax_dollars);
      return {
        year: period.year,
        // matched + 0.00 is a real zero; unmatched is N/A even when totals are 0.
        value: matched ? (tax ?? 0) : null,
      };
    }),
  );
}
