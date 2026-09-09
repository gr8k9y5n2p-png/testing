import { fundSeriesColor } from "@/lib/charts/series-colors";
import { yearEndGrowth } from "@/lib/charts/shared-axis";
import { postIllustrateCompare } from "@/lib/illustrate/compare-client";
import {
  compareSideFromFund,
  compareTaxRequestFields,
  navFromFundMetadata,
  positiveNav,
  trailingCalendarPeriods,
  yoyTaxDragCompareRequest,
} from "@/lib/illustrate/compare-request";
import type { ComparePeriodIn, CompareRequest, CompareResponse } from "@/lib/illustrate/compare-types";
import type { TaxRates } from "@/lib/illustrate/types";
import {
  mapFundsWithOptionalPerformance,
  missingPerformanceTickers,
} from "@/lib/illustrate/growth-tax-series";
import { seedNavLookup } from "@/lib/illustrate/seed-nav";
import { fetchPerformanceIfAvailable } from "@/lib/performance/client";
import {
  DEFAULT_START_DOLLARS,
  type PerformanceQuery,
  type PerformanceResponse,
} from "@/lib/performance/types";

export type { GrowthLineSeries } from "@/lib/illustrate/growth-tax-series";
export {
  annualizedFromRows,
  calendarYearsFromRows,
  growthLinesFromRows,
  taxSeriesFromRows,
  windowedGrowth,
} from "@/lib/illustrate/growth-tax-series";

export type GrowthFundInput = {
  ticker: string;
  label?: string;
  fundIdentifier?: string;
  fundFamily?: string;
  /** Display name only. Compare omits fund_name so Data does not AND-miss. */
  fundName?: string;
  /** Search / fund metadata NAV. Sent on YoY compare when > 0. */
  navPerShare?: number | null;
};

export type LoadedGrowthFund = {
  input: GrowthFundInput;
  color: string;
  performance: PerformanceResponse | null;
  tax: CompareResponse | null;
  /** fund_vs_fund: this fund is `left` or `right`. YoY uses `auto`. */
  taxSide: "left" | "right" | "auto";
};

export type GrowthTaxLoadResult = {
  rows: LoadedGrowthFund[];
  missingTickers: string[];
};

export type GrowthTaxLoaders = {
  loadPerformance: (
    request: PerformanceQuery,
    init?: { signal?: AbortSignal; method?: "GET" | "POST" },
  ) => Promise<PerformanceResponse | null>;
  loadCompare: (
    request: CompareRequest,
    init?: { signal?: AbortSignal },
  ) => Promise<CompareResponse>;
};

const defaultLoaders: GrowthTaxLoaders = {
  loadPerformance: fetchPerformanceIfAvailable,
  loadCompare: postIllustrateCompare,
};

export type GrowthTaxLoadOptions = {
  loaders?: GrowthTaxLoaders;
  taxRates?: TaxRates;
  combineStateWithFederal?: boolean;
};

export async function loadGrowthAndTaxDrag(
  funds: GrowthFundInput[],
  principal: number,
  benchmark: string | null,
  periods: ComparePeriodIn[] | undefined,
  signal: AbortSignal,
  options: GrowthTaxLoadOptions = {},
): Promise<GrowthTaxLoadResult> {
  const loaders = options.loaders ?? defaultLoaders;
  const taxFields = compareTaxRequestFields({
    taxRates: options.taxRates,
    combineStateWithFederal: options.combineStateWithFederal,
  });
  const mapped = await mapFundsWithOptionalPerformance(funds, async (input) => {
    const ticker = input.ticker.trim().toUpperCase();
    const usePost = principal !== DEFAULT_START_DOLLARS;
    const request: PerformanceQuery = {
      ticker,
      fund_identifier: input.fundIdentifier ?? ticker,
      benchmark,
      start_dollars: principal,
      mode: "fixture",
    };
    return loaders.loadPerformance(request, {
      signal,
      method: usePost ? "POST" : "GET",
    });
  });

  const prepared = mapped.map(({ fund: input, performance }, index) => {
    const ticker = input.ticker.trim().toUpperCase();
    const lastClose =
      performance?.fund.points[performance.fund.points.length - 1]?.adj_close;
    const nav =
      navFromFundMetadata(ticker, input.navPerShare, seedNavLookup) ??
      positiveNav(lastClose);
    return { input, index, ticker, performance, nav };
  });

  const yearSet = new Set<number>();
  for (const row of prepared) {
    if (!row.performance) continue;
    for (const point of yearEndGrowth(row.performance.fund.points)) {
      yearSet.add(point.year);
    }
  }
  for (const period of trailingCalendarPeriods()) yearSet.add(period.year);
  const taxPeriods =
    periods && periods.length > 0
      ? periods
      : [...yearSet]
          .sort((a, b) => a - b)
          .map((year) => ({ year }));
  const usablePeriods =
    taxPeriods.length >= 2 ? taxPeriods : trailingCalendarPeriods();

  let pair: CompareResponse | null = null;
  if (prepared.length === 2) {
    const [left, right] = prepared;
    try {
      pair = await loaders.loadCompare(
        {
          mode: "fund_vs_fund",
          holding_dollars: principal,
          ...taxFields,
          latest_as_of_only: true,
          ...(left.nav != null ? { nav_per_share: left.nav } : {}),
          left: {
            ...compareSideFromFund({
              ticker: left.ticker,
              fundName: left.input.fundName,
              family: left.input.fundFamily,
              fundIdentifier: left.input.fundIdentifier ?? left.ticker,
              label: left.input.label ?? left.ticker,
              nav: left.nav,
            }),
            holding_dollars: principal,
          },
          right: {
            ...compareSideFromFund({
              ticker: right.ticker,
              fundName: right.input.fundName,
              family: right.input.fundFamily,
              fundIdentifier: right.input.fundIdentifier ?? right.ticker,
              label: right.input.label ?? right.ticker,
              nav: right.nav,
            }),
            holding_dollars: principal,
          },
          periods: usablePeriods,
        },
        { signal },
      );
    } catch {
      pair = null;
    }
  }

  const rows: LoadedGrowthFund[] = await Promise.all(
    prepared.map(async (row) => {
      let tax: CompareResponse | null = pair;
      let taxSide: LoadedGrowthFund["taxSide"] =
        pair == null ? "auto" : row.index === 0 ? "left" : "right";
      if (!tax) {
        try {
          tax = await loaders.loadCompare(
            yoyTaxDragCompareRequest({
              ticker: row.ticker,
              label: row.input.label ?? row.ticker,
              fundIdentifier: row.input.fundIdentifier ?? row.ticker,
              fundFamily: row.input.fundFamily,
              fundName: row.input.fundName,
              holdingDollars: principal,
              navPerShare: row.nav,
              periods: usablePeriods,
              taxRates: taxFields.tax_rates,
              combineStateWithFederal: taxFields.combine_state_with_federal,
            }),
            { signal },
          );
        } catch {
          tax = null;
        }
        taxSide = "auto";
      }
      return {
        input: row.input,
        color: fundSeriesColor(row.index),
        performance: row.performance,
        tax,
        taxSide,
      };
    }),
  );

  return {
    rows,
    missingTickers: missingPerformanceTickers(rows),
  };
}
