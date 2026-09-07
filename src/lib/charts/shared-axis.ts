/** Shared plot geometry so growth lines and tax bars stay year-aligned. */

export const SHARED_CHART_WIDTH = 800;

export const SHARED_CHART_PAD = {
  top: 18,
  right: 18,
  bottom: 28,
  left: 52,
} as const;

/** Empty share of each year slot — keeps neighboring year groups apart. */
export const YEAR_GUTTER_RATIO = 0.3;
export const BAR_GAP_PX = 2;

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
  center: (index: number) => number;
  groupLeft: (index: number) => number;
  barX: (yearIndex: number, seriesIndex: number) => number;
};

export function yearLayout(
  years: number[],
  seriesCount = 1,
  width = SHARED_CHART_WIDTH,
  pad: ChartPad = SHARED_CHART_PAD,
): YearLayout {
  const inner = width - pad.left - pad.right;
  const slot = years.length > 0 ? inner / years.length : inner;
  const gutter = slot * YEAR_GUTTER_RATIO;
  const groupW = Math.max(4, slot - gutter);
  const count = Math.max(seriesCount, 1);
  const gap = count > 1 ? BAR_GAP_PX : 0;
  const barW = Math.max(3, (groupW - gap * (count - 1)) / count);
  const center = (index: number) => pad.left + slot * index + slot / 2;
  const groupLeft = (index: number) => center(index) - (barW * count + gap * (count - 1)) / 2;
  return {
    slot,
    gutter,
    groupW,
    barW,
    gap,
    count,
    center,
    groupLeft,
    barX: (yearIndex, seriesIndex) =>
      groupLeft(yearIndex) + seriesIndex * (barW + gap),
  };
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

export function yearEndReturns(
  points: { date: string; growth_of_x: number }[],
  startDollars: number,
) {
  return yearEndGrowth(points).map((point) => ({
    year: point.year,
    value: startDollars > 0 ? point.value / startDollars - 1 : 0,
  }));
}

/** (end / start) ^ (1 / years) − 1 */
export function cagr(start: number, end: number, years: number): number | null {
  if (!(start > 0) || !(end > 0) || !(years > 0)) return null;
  return (end / start) ** (1 / years) - 1;
}
