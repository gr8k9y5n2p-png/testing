/** Shared plot geometry so growth lines and tax bars stay year-aligned. */

export const SHARED_CHART_WIDTH = 800;

export const SHARED_CHART_PAD = {
  top: 18,
  right: 56,
  bottom: 28,
  left: 58,
} as const;

/** Empty share of each year slot — keeps neighboring year groups apart. */
export const YEAR_GUTTER_RATIO = 0.4;
export const MIN_YEAR_GUTTER_PX = 16;
export const BAR_GAP_PX = 3;

export type ChartPad = {
  top: number;
  right: number;
  bottom: number;
  left: number;
};

export type YearLayout = {
  slot: number;
  gutter: number;
  groupW: number;
  barW: number;
  gap: number;
  count: number;
  used: number;
  center: (index: number) => number;
  slotLeft: (index: number) => number;
  groupLeft: (index: number) => number;
  barX: (yearIndex: number, seriesIndex: number) => number;
  barRight: (yearIndex: number, seriesIndex: number) => number;
};

/**
 * One x-scale for both charts.
 * Each year owns a slot. Bars are centered in that slot with a gutter on
 * both sides so year groups never touch. Every fund bar has the same width
 * and a fixed gap — the group is shrunk to fit, never allowed to overflow.
 */
export function yearLayout(
  years: number[],
  seriesCount = 1,
  width = SHARED_CHART_WIDTH,
  pad: ChartPad = SHARED_CHART_PAD,
): YearLayout {
  const inner = Math.max(1, width - pad.left - pad.right);
  const nYears = Math.max(years.length, 1);
  const slot = inner / nYears;
  const gutter = Math.min(
    slot * 0.55,
    Math.max(MIN_YEAR_GUTTER_PX, slot * YEAR_GUTTER_RATIO),
  );
  const groupW = Math.max(1, slot - gutter);
  const count = Math.max(seriesCount, 1);
  const gap = count > 1 ? BAR_GAP_PX : 0;
  const rawBar = (groupW - gap * (count - 1)) / count;
  const barW = Math.max(1, Math.floor(Math.max(0, rawBar) * 10) / 10);
  const used = barW * count + gap * (count - 1);
  const inset = Math.max(0, (groupW - used) / 2);

  const slotLeft = (index: number) => pad.left + slot * index;
  const center = (index: number) => slotLeft(index) + slot / 2;
  const groupLeft = (index: number) => slotLeft(index) + gutter / 2 + inset;
  const barX = (yearIndex: number, seriesIndex: number) =>
    groupLeft(yearIndex) + seriesIndex * (barW + gap);

  return {
    slot,
    gutter,
    groupW,
    barW,
    gap,
    count,
    used,
    center,
    slotLeft,
    groupLeft,
    barX,
    barRight: (yearIndex, seriesIndex) => barX(yearIndex, seriesIndex) + barW,
  };
}

/** True when any bar crosses a year boundary or another bar. */
export function layoutCollides(axis: YearLayout, yearCount: number): boolean {
  if (yearCount <= 0) return false;
  for (let year = 0; year < yearCount; year += 1) {
    const slotStart = axis.slotLeft(year);
    const slotEnd = axis.slotLeft(year) + axis.slot;
    for (let series = 0; series < axis.count; series += 1) {
      const left = axis.barX(year, series);
      const right = axis.barRight(year, series);
      if (left < slotStart + 0.01 || right > slotEnd - 0.01) return true;
      if (series > 0 && left < axis.barRight(year, series - 1) + 0.01) return true;
    }
  }
  return false;
}

export function yearSlot(
  years: number[],
  year: number,
  width = SHARED_CHART_WIDTH,
  pad: ChartPad = SHARED_CHART_PAD,
): { center: number; width: number } {
  const layout = yearLayout(years, 1, width, pad);
  const index = years.indexOf(year);
  const i = index < 0 ? 0 : index;
  return { center: layout.center(i), width: layout.slot };
}

export function yearEndGrowth(points: { date: string; growth_of_x: number }[]) {
  const byYear = new Map<number, { date: string; growth_of_x: number }>();
  for (const point of points) {
    const year = Number(point.date.slice(0, 4));
    if (!Number.isFinite(year)) continue;
    const prior = byYear.get(year);
    if (!prior || point.date >= prior.date) byYear.set(year, point);
  }
  return [...byYear.entries()]
    .sort((a, b) => a[0] - b[0])
    .map(([year, point]) => ({ year, value: point.growth_of_x }));
}

/** Rebase a year-end series so the first visible year equals startDollars. */
export function rebaseWindow(
  points: { year: number; value: number }[],
  startDollars: number,
) {
  if (points.length === 0) return points;
  const base = points[0].value;
  if (!(base > 0)) return points;
  return points.map((point) => ({
    year: point.year,
    value: startDollars * (point.value / base),
  }));
}

export function yearEndReturns(
  points: { date: string; growth_of_x: number }[],
  startDollars: number,
) {
  return yearEndGrowth(points).map((point) => ({
    year: point.year,
    value: startDollars > 0 ? point.value / startDollars - 1 : 0,
  }));
}

/** Sketch window: last complete five calendar years (2021–2025 in current fixtures). */
export function sketchYears(years: number[]): number[] {
  const complete = years.filter((year) => year <= 2025);
  const windowed = complete.filter((year) => year >= 2021);
  if (windowed.length >= 2) return windowed;
  return complete.slice(-5);
}

/** (end / start) ^ (1 / years) − 1 */
export function cagr(start: number, end: number, years: number): number | null {
  if (!(start > 0) || !(end > 0) || !(years > 0)) return null;
  return (end / start) ** (1 / years) - 1;
}
