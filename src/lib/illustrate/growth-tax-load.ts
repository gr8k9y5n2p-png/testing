import { fundSeriesColor } from "../charts/series-colors.ts";
import { yearEndGrowth } from "../charts/shared-axis.ts";
import {
  compareSideFromFund,
  compareTaxRequestFields,
  preferLiveWeeklyNav,
  trailingCalendarPeriods,
  yoyTaxDragCompareRequest,
} from "./compare-request.ts";
import type { ComparePeriodIn, CompareRequest, CompareResponse } from "./compare-types.ts";
import type { TaxRates } from "./types.ts";
import {
  mapFundsWithOptionalPerformance,
  missingPerformanceTickers,
} from "./growth-tax-series.ts";
import { defaultPerformanceMode } from "../performance/mode.ts";
import {
  DEFAULT_START_DOLLARS,
  type PerformanceQuery,
  type PerformanceResponse,
} from "../performance/types.ts";

export type { GrowthLineSeries } from "./growth-tax-series.ts";
export {
  annualizedFromRows,
  calendarYearsFromRows,
  growthLinesFromRows,
  taxSeriesFromRows,
  windowedGrowth,
} from "./growth-tax-series.ts";

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
  /** Live weekly / catalog NAV used for Dist $. Seed only when no live print. */
  navPerShare?: number | null;
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
  async loadPerformance(request, init) {
    const { fetchPerformanceIfAvailable } = await import("@/lib/performance/client");
    return fetchPerformanceIfAvailable(request, init);
  },
  async loadCompare(request, init) {
    const { postIllustrateCompare } = await import("@/lib/illustrate/compare-client");
    return postIllustrateCompare(request, init);
  },
};

export type GrowthTaxPrefetch = {
  ticker: string;
  tax: CompareResponse | null;
  taxSide?: LoadedGrowthFund["taxSide"];
};

export type GrowthTaxLoadOptions = {
  loaders?: GrowthTaxLoaders;
  taxRates?: TaxRates;
  combineStateWithFederal?: boolean;
  /** Compare workspace YoY rows — skip a second compare storm when present. */
  prefetchTax?: GrowthTaxPrefetch[];
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
  const prefetchByTicker = new Map(
    (options.prefetchTax ?? []).map((row) => [
      row.ticker.trim().toUpperCase(),
      row,
    ]),
  );
  const mapped = await mapFundsWithOptionalPerformance(
    funds,
    async (input) => {
      const ticker = input.ticker.trim().toUpperCase();
      const usePost = principal !== DEFAULT_START_DOLLARS;
      const request: PerformanceQuery = {
        ticker,
        fund_identifier: input.fundIdentifier ?? ticker,
        benchmark,
        start_dollars: principal,
        mode: defaultPerformanceMode(),
      };
      return loaders.loadPerformance(request, {
        signal,
        method: usePost ? "POST" : "GET",
      });
    },
    signal,
  );

  const prepared = mapped.map(({ fund: input, performance }, index) => {
    const ticker = input.ticker.trim().toUpperCase();
    const lastClose =
      performance?.fund.points[performance.fund.points.length - 1]?.adj_close;
    const nav = preferLiveWeeklyNav({
      ticker,
      catalogNav: input.navPerShare,
      weeklyNav: lastClose,
    });
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
      const prefetched = prefetchByTicker.get(row.ticker);
      if (prefetched && Object.prototype.hasOwnProperty.call(prefetched, "tax")) {
        return {
          input: row.input,
          color: fundSeriesColor(row.index),
          performance: row.performance,
          tax: prefetched.tax,
          taxSide: prefetched.taxSide ?? "auto",
          navPerShare: row.nav ?? null,
        };
      }
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
        } catch (error) {
          if (signal.aborted) throw error;
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
        navPerShare: row.nav ?? null,
      };
    }),
  );

  return {
    rows,
    missingTickers: missingPerformanceTickers(rows),
  };
}
