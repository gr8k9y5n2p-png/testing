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
import { PORTFOLIO_COMPARE_YEARS } from "./portfolio-compare-years.ts";
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
  signal?: AbortSignal,
): Promise<Array<{ fund: T; performance: PerformanceResponse | null }>> {
  return Promise.all(
    funds.map(async (fund) => {
      try {
        return { fund, performance: settlePerformancePack(await loadOne(fund)) };
      } catch (error) {
        if (isAbortError(error) && signal?.aborted) throw error;
        return {
          fund,
          performance: isAbortError(error) ? null : performanceFromFetchError(error),
        };
      }
    }),
  );
}

export function missingPerformanceTickers(rows: GrowthSeriesRow[]): string[] {
  return rows
    .filter((row) => !row.performance)
    .map((row) => row.input.ticker.trim().toUpperCase());
}

function yearFromAsOf(raw: string | null | undefined): number | null {
  if (raw == null || raw === "") return null;
  const parsed = Number(String(raw).slice(0, 4));
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

/** Prefer compare `common_inception.from_year` / `from_as_of`. Soft if absent. */
export function compareInceptionFromYear(
  tax: CompareResponse | null | undefined,
): number | null {
  const inc = tax?.summary?.common_inception;
  if (!inc) return null;
  if (inc.from_year != null && inc.from_year > 0) return inc.from_year;
  return yearFromAsOf(inc.from_as_of);
}

export function compareInceptionToYear(
  tax: CompareResponse | null | undefined,
): number | null {
  const inc = tax?.summary?.common_inception;
  if (!inc) return null;
  if (inc.to_year != null && inc.to_year > 0) return inc.to_year;
  return yearFromAsOf(inc.to_as_of);
}

/** First usable year for one fund. Soft — no pack and no tax → null. */
export function fundInceptionYear(
  row: GrowthSeriesRow,
  taxMetric: TaxDragMetric,
): number | null {
  const fromApi = compareInceptionFromYear(row.tax);
  if (fromApi != null) return fromApi;
  const years: number[] = [];
  if (performancePackIsUsable(row.performance) && row.performance) {
    for (const point of yearEndGrowth(row.performance.fund.points)) {
      years.push(point.year);
    }
  }
  if (years.length === 0 && row.tax) {
    for (const point of toTaxDragPeriods(row.tax, taxMetric, row.taxSide)) {
      if (point.year > 0) years.push(point.year);
    }
  }
  if (years.length === 0) return null;
  return Math.min(...years);
}

/**
 * Latest first-year across filled tickers. A later-inception fund clips
 * the shared Growth & Tax window so early empty columns are omitted.
 */
export function commonInceptionYear(
  rows: GrowthSeriesRow[] | null,
  taxMetric: TaxDragMetric,
): number | null {
  if (!rows || rows.length === 0) return null;
  const firsts = rows
    .map((row) => fundInceptionYear(row, taxMetric))
    .filter((year): year is number => year != null);
  if (firsts.length === 0) return null;
  return Math.max(...firsts);
}

export function calendarYearsFromRows(
  rows: GrowthSeriesRow[] | null,
  taxMetric: TaxDragMetric,
): number[] {
  if (!rows) return [];
  const set = new Set<number>();
  for (const row of rows) {
    if (row.performance) {
      try {
        for (const point of yearEndGrowth(row.performance.fund.points)) {
          set.add(point.year);
        }
      } catch {
        /* skip a broken pack — do not drop the shared year axis */
      }
    }
    if (row.tax) {
      try {
        for (const point of toTaxDragPeriods(row.tax, taxMetric, row.taxSide)) {
          if (point.year > 0) set.add(point.year);
        }
      } catch {
        /* skip a broken compare payload — keep years from the other funds */
      }
    }
  }
  const fromPacks = sketchYears([...set].sort((a, b) => a - b));
  const sketched =
    fromPacks.length > 0
      ? fromPacks
      : rows.length === 0
        ? []
        : sketchYears([...PORTFOLIO_COMPARE_YEARS]);
  const inception = commonInceptionYear(rows, taxMetric);
  const filled = rows.filter((row) => fundInceptionYear(row, taxMetric) != null);
  const toYears = filled.map((row) => compareInceptionToYear(row.tax));
  const toYear =
    toYears.length > 0 && toYears.every((year): year is number => year != null)
      ? Math.min(...toYears)
      : null;
  return sketched.filter((year) => {
    if (inception != null && year < inception) return false;
    if (toYear != null && year > toYear) return false;
    return true;
  });
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
