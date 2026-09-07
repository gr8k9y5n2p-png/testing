/** Shared plot geometry so growth lines and tax bars stay year-aligned. */

export const SHARED_CHART_WIDTH = 720;

export const SHARED_CHART_PAD = {
  top: 18,
  right: 18,
  bottom: 28,
  left: 52,
} as const;

export type ChartPad = {
  top: number;
  right: number;
  bottom: number;
  left: number;
};

export function yearSlot(
  years: number[],
  year: number,
  width = SHARED_CHART_WIDTH,
  pad: ChartPad = SHARED_CHART_PAD,
): { center: number; width: number } {
  const inner = width - pad.left - pad.right;
  const slot = years.length > 0 ? inner / years.length : inner;
  const index = years.indexOf(year);
  const i = index < 0 ? 0 : index;
  return { center: pad.left + slot * i + slot / 2, width: slot };
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

/** (end / start) ^ (1 / years) − 1 */
export function cagr(start: number, end: number, years: number): number | null {
  if (!(start > 0) || !(end > 0) || !(years > 0)) return null;
  return (end / start) ** (1 / years) - 1;
}
