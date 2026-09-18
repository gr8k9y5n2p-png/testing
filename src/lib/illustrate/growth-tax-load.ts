import { fundSeriesColor } from "../charts/series-colors.ts";
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

export type GrowthTaxRowUpdate = {
  input: GrowthFundInput;
  color: string;
  index: number;
  performance?: PerformanceResponse | null;
  tax?: CompareResponse | null;
  taxSide?: LoadedGrowthFund["taxSide"];
  navPerShare?: number | null;
};

export type GrowthTaxLoadOptions = {
  loaders?: GrowthTaxLoaders;
  taxRates?: TaxRates;
  combineStateWithFederal?: boolean;
  /** Compare workspace YoY rows — skip a second compare storm when present. */
  prefetchTax?: GrowthTaxPrefetch[];
  /** Progressive fill: tax can land before performance for the same ticker. */
  onRow?: (update: GrowthTaxRowUpdate) => void;
  /**
   * Compare slots use per-ticker YoY (shared with Upcoming). Homepage 2-fund
   * still issues one fund_vs_fund when prefetch is empty.
   */
  preferYoy?: boolean;
};

export function applyGrowthTaxRowUpdate(
  current: LoadedGrowthFund[] | null,
  update: GrowthTaxRowUpdate,
  order: string[],
): LoadedGrowthFund[] {
  const byTicker = new Map(
    (current ?? []).map((row) => [row.input.ticker.trim().toUpperCase(), row]),
  );
  const key = update.input.ticker.trim().toUpperCase();
  const prev = byTicker.get(key);
  const next: LoadedGrowthFund = {
    input: update.input,
    color: update.color,
    performance:
      "performance" in update
        ? (update.performance ?? null)
        : (prev?.performance ?? null),
    tax: "tax" in update ? (update.tax ?? null) : (prev?.tax ?? null),
    taxSide: update.taxSide ?? prev?.taxSide ?? "auto",
    navPerShare:
      update.navPerShare !== undefined
        ? update.navPerShare
        : (prev?.navPerShare ?? null),
  };
  byTicker.set(key, next);
  return order
    .map((ticker) => byTicker.get(ticker.trim().toUpperCase()))
    .filter((row): row is LoadedGrowthFund => Boolean(row));
}

function prefetchHasTax(
  prefetchByTicker: Map<string, GrowthTaxPrefetch>,
  ticker: string,
): boolean {
  const prefetched = prefetchByTicker.get(ticker);
  return Boolean(
    prefetched && Object.prototype.hasOwnProperty.call(prefetched, "tax"),
  );
}

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
  const prepared = funds.map((input, index) => {
    const ticker = input.ticker.trim().toUpperCase();
    const nav = preferLiveWeeklyNav({
      ticker,
      catalogNav: input.navPerShare,
    });
    return { input, index, ticker, nav };
  });
  const prefetchCoversAll = prepared.every((row) =>
    prefetchHasTax(prefetchByTicker, row.ticker),
  );
  const usablePeriods =
    periods && periods.length >= 2 ? periods : trailingCalendarPeriods();

  let pairPromise: Promise<CompareResponse | null> | null = null;
  if (prepared.length === 2 && !prefetchCoversAll && !options.preferYoy) {
    const [left, right] = prepared;
    pairPromise = loaders
      .loadCompare(
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
      )
      .catch((error) => {
        if (signal.aborted) throw error;
        return null;
      });
  }

  const rows: LoadedGrowthFund[] = await Promise.all(
    prepared.map(async (row) => {
      const color = fundSeriesColor(row.index);
      const prefetched = prefetchByTicker.get(row.ticker);
      const emit = (update: GrowthTaxRowUpdate) => {
        if (signal.aborted) return;
        options.onRow?.(update);
      };

      const usePost = principal !== DEFAULT_START_DOLLARS;
      const performancePromise = mapFundsWithOptionalPerformance(
        [row.input],
        async (input) => {
          const ticker = input.ticker.trim().toUpperCase();
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
      ).then((mapped) => {
        const performance = mapped[0]?.performance ?? null;
        const lastClose =
          performance?.fund.points[performance.fund.points.length - 1]
            ?.adj_close;
        const nav = preferLiveWeeklyNav({
          ticker: row.ticker,
          catalogNav: row.input.navPerShare,
          weeklyNav: lastClose,
        });
        emit({
          input: row.input,
          color,
          index: row.index,
          performance,
          navPerShare: nav ?? null,
        });
        return { performance, nav };
      });

      let taxPromise: Promise<{
        tax: CompareResponse | null;
        taxSide: LoadedGrowthFund["taxSide"];
      }>;
      if (prefetched && Object.prototype.hasOwnProperty.call(prefetched, "tax")) {
        const tax = prefetched.tax;
        const taxSide = prefetched.taxSide ?? "auto";
        emit({
          input: row.input,
          color,
          index: row.index,
          tax,
          taxSide,
          navPerShare: row.nav ?? null,
        });
        taxPromise = Promise.resolve({ tax, taxSide });
      } else if (pairPromise) {
        taxPromise = pairPromise.then((tax) => {
          const taxSide: LoadedGrowthFund["taxSide"] =
            tax == null ? "auto" : row.index === 0 ? "left" : "right";
          emit({
            input: row.input,
            color,
            index: row.index,
            tax,
            taxSide,
            navPerShare: row.nav ?? null,
          });
          return { tax, taxSide };
        });
      } else {
        taxPromise = loaders
          .loadCompare(
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
          )
          .then((tax) => {
            emit({
              input: row.input,
              color,
              index: row.index,
              tax,
              taxSide: "auto",
              navPerShare: row.nav ?? null,
            });
            return { tax, taxSide: "auto" as const };
          })
          .catch((error) => {
            if (signal.aborted) throw error;
            emit({
              input: row.input,
              color,
              index: row.index,
              tax: null,
              taxSide: "auto",
              navPerShare: row.nav ?? null,
            });
            return { tax: null, taxSide: "auto" as const };
          });
      }

      const [perf, taxResult] = await Promise.all([
        performancePromise,
        taxPromise,
      ]);
      return {
        input: row.input,
        color,
        performance: perf.performance,
        tax: taxResult.tax,
        taxSide: taxResult.taxSide,
        navPerShare: perf.nav ?? row.nav ?? null,
      };
    }),
  );

  return {
    rows,
    missingTickers: missingPerformanceTickers(rows),
  };
}
