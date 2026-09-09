import { BENCHMARK_COLOR } from "../charts/series-colors.ts";
import {
  cagr,
  rebaseWindow,
  sketchYears,
  yearEndGrowth,
} from "../charts/shared-axis.ts";
import {
  firstUsablePerformance,
  isAbortError,
  performanceFromFetchError,
  performancePackIsUsable,
} from "../performance/coverage.ts";
import type { PerformanceResponse } from "../performance/types.ts";
import type { CompareResponse } from "./compare-types.ts";
import {
  alignTaxDragYears,
  toNegativeTaxDrag,
  toTaxDragPeriods,
  type TaxDragFundSeries,
  type TaxDragMetric,
} from "./tax-drag-map.ts";

export type GrowthLineSeries = {
  id: string;
  label: string;
  color: string;
  dashed?: boolean;
  points: { year: number; value: number }[];
};

export type GrowthSeriesRow = {
  input: { ticker: string };
  color: string;
  performance: PerformanceResponse | null;
  tax: CompareResponse | null;
  taxSide: "left" | "right" | "auto";
};

/** 404 / uncovered / empty pack → null. Abort still throws. */
export function settlePerformancePack(
  pack: PerformanceResponse | null | undefined,
): PerformanceResponse | null {
  return performancePackIsUsable(pack) ? pack : null;
}

export async function mapFundsWithOptionalPerformance<T>(
  funds: T[],
  loadOne: (fund: T) => Promise<PerformanceResponse | null>,
): Promise<Array<{ fund: T; performance: PerformanceResponse | null }>> {
  return Promise.all(
    funds.map(async (fund) => {
      try {
        return { fund, performance: settlePerformancePack(await loadOne(fund)) };
      } catch (error) {
        if (isAbortError(error)) throw error;
        return { fund, performance: performanceFromFetchError(error) };
      }
    }),
  );
}

export function missingPerformanceTickers(rows: GrowthSeriesRow[]): string[] {
  return rows
    .filter((row) => !row.performance)
    .map((row) => row.input.ticker.trim().toUpperCase());
}

export function calendarYearsFromRows(
  rows: GrowthSeriesRow[] | null,
  taxMetric: TaxDragMetric,
): number[] {
  if (!rows) return [];
  const set = new Set<number>();
  for (const row of rows) {
    if (row.performance) {
      for (const point of yearEndGrowth(row.performance.fund.points)) {
        set.add(point.year);
      }
    }
    if (row.tax) {
      for (const point of toTaxDragPeriods(row.tax, taxMetric, row.taxSide)) {
        if (point.year > 0) set.add(point.year);
      }
    }
  }
  return sketchYears([...set].sort((a, b) => a - b));
}

export function windowedGrowth(
  points: { date: string; growth_of_x: number }[],
  years: number[],
  principal: number,
) {
  return rebaseWindow(
    yearEndGrowth(points).filter((point) => years.includes(point.year)),
    principal,
  );
}

export function growthLinesFromRows(
  rows: GrowthSeriesRow[] | null,
  years: number[],
  principal: number,
): GrowthLineSeries[] {
  if (!rows) return [];
  const covered = rows.filter((row) => performancePackIsUsable(row.performance));
  const lines: GrowthLineSeries[] = covered.map((row) => {
    const pack = row.performance as PerformanceResponse;
    return {
      id: pack.fund_ticker || row.input.ticker,
      label: pack.fund_ticker || row.input.ticker,
      color: row.color,
      points: windowedGrowth(pack.fund.points, years, principal),
    };
  });
  const benchPack = firstUsablePerformance(covered);
  const bench = benchPack?.benchmark;
  if (bench && benchPack) {
    lines.push({
      id: `bench-${bench.ticker}`,
      label: benchPack.benchmark_tracks || bench.ticker,
      color: BENCHMARK_COLOR,
      dashed: true,
      points: windowedGrowth(bench.points, years, principal),
    });
  }
  return lines;
}

export function taxSeriesFromRows(
  rows: GrowthSeriesRow[] | null,
  years: number[],
  taxMetric: TaxDragMetric,
): TaxDragFundSeries[] {
  if (!rows) return [];
  return rows.map((row) => {
    const ticker = row.input.ticker.trim().toUpperCase();
    return {
      id: ticker,
      label: ticker,
      color: row.color,
      points: row.tax
        ? toNegativeTaxDrag(
            alignTaxDragYears(toTaxDragPeriods(row.tax, taxMetric, row.taxSide), years),
          )
        : years.map((year) => ({ year, value: null })),
    };
  });
}

export function annualizedFromRows(
  rows: GrowthSeriesRow[] | null,
  years: number[],
  principal: number,
) {
  if (!rows || years.length < 2) return [];
  const span = years[years.length - 1] - years[0];
  return growthLinesFromRows(rows, years, principal).map((row) => {
    const first = row.points[0];
    const last = row.points[row.points.length - 1];
    return {
      id: row.id,
      label: row.label,
      color: row.color,
      value: first && last ? cagr(first.value, last.value, Math.max(span, 1)) : null,
    };
  });
}
