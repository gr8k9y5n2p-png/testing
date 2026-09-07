"use client";

import { useEffect, useMemo, useState } from "react";
import { GrowthOfXChart, type GrowthLineSeries } from "@/components/illustrate/GrowthOfXChart";
import { TaxDragByYearChart } from "@/components/illustrate/TaxDragByYearChart";
import {
  BENCHMARK_COLOR,
  MAX_GROWTH_FUNDS,
  fundSeriesColor,
} from "@/lib/charts/series-colors";
import { cagr, yearEndGrowth, yearEndReturns } from "@/lib/charts/shared-axis";
import { formatUsd } from "@/lib/format";
import { postIllustrateCompare } from "@/lib/illustrate/compare-client";
import type { ComparePeriodIn, CompareResponse } from "@/lib/illustrate/compare-types";
import {
  toNegativeTaxDrag,
  toTaxDragPeriods,
  type TaxDragFundSeries,
} from "@/lib/illustrate/tax-drag-chart";
import { fetchPerformance, postPerformanceGrowth } from "@/lib/performance/client";
import { PERFORMANCE_CATALOG } from "@/lib/performance/mock";
import {
  DEFAULT_START_DOLLARS,
  PERFORMANCE_FIXTURE_TICKERS,
  type PerformanceResponse,
} from "@/lib/performance/types";

export type GrowthFundInput = {
  ticker: string;
  label?: string;
  fundIdentifier?: string;
  fundFamily?: string;
};

export type GrowthAndTaxDragModuleProps = {
  funds?: GrowthFundInput[];
  startDollars?: number;
  benchmark?: string;
  periods?: ComparePeriodIn[];
  className?: string;
  showAnnualized?: boolean;
  allowAddFund?: boolean;
  editablePrincipal?: boolean;
};

const DEFAULT_FUNDS: GrowthFundInput[] = [
  {
    ticker: "AGTHX",
    label: "The Growth Fund of America",
    fundIdentifier: "AGTHX",
    fundFamily: "American Funds",
  },
];

const TAX_FOCUS: Record<string, string> = {
  AGTHX: "Focus on capital gains",
  AMCPX: "Active large growth",
  FBGRX: "Focus on capital gains",
  VFIAX: "Index · lower turnover",
  DODIX: "Ordinary income",
  VTIAX: "International index",
};

type LoadedFund = {
  input: GrowthFundInput;
  color: string;
  performance: PerformanceResponse;
  tax: CompareResponse | null;
};

export function GrowthAndTaxDragModule({
  funds = DEFAULT_FUNDS,
  startDollars = DEFAULT_START_DOLLARS,
  benchmark,
  periods,
  className = "",
  showAnnualized = true,
  allowAddFund = true,
  editablePrincipal = true,
}: GrowthAndTaxDragModuleProps) {
  const [selected, setSelected] = useState<GrowthFundInput[]>(() =>
    funds.length > 0 ? funds : DEFAULT_FUNDS,
  );
  const [principal, setPrincipal] = useState(startDollars);
  const [principalDraft, setPrincipalDraft] = useState(String(startDollars));
  const [addTicker, setAddTicker] = useState("");
  const [unit, setUnit] = useState<"dollars" | "percent">("dollars");
  const [retry, setRetry] = useState(0);
  const [rows, setRows] = useState<LoadedFund[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [settledKey, setSettledKey] = useState<string | null>(null);

  const requestKey = JSON.stringify({
    funds: selected.map((fund) => fundKey(fund)),
    principal,
    benchmark: benchmark ?? null,
    periods: periods ?? null,
  });
  const fetchKey = `${requestKey}:${retry}`;
  const loading = settledKey !== fetchKey;

  useEffect(() => {
    const controller = new AbortController();
    const next = JSON.parse(requestKey) as {
      funds: GrowthFundInput[];
      principal: number;
      benchmark: string | null;
    };

    void loadModule(next.funds, next.principal, next.benchmark, periods, controller.signal)
      .then((loaded) => {
        setRows(loaded);
        setError(null);
        setSettledKey(fetchKey);
      })
      .catch((caught: unknown) => {
        if (caught instanceof DOMException && caught.name === "AbortError") return;
        setRows(null);
        setError(caught instanceof Error ? caught.message : "Growth and tax drag failed");
        setSettledKey(fetchKey);
      });

    return () => controller.abort();
  }, [requestKey, fetchKey, periods]);

  const years = useMemo(() => {
    if (!rows) return [];
    const set = new Set<number>();
    for (const row of rows) {
      for (const point of yearEndGrowth(row.performance.fund.points)) {
        set.add(point.year);
      }
    }
    return [...set].sort((a, b) => a - b);
  }, [rows]);

  const growthSeries = useMemo<GrowthLineSeries[]>(() => {
    if (!rows) return [];
    const lines: GrowthLineSeries[] = rows.map((row) => ({
      id: row.performance.fund_ticker,
      label: row.input.label || row.performance.fund_name,
      color: row.color,
      points:
        unit === "percent"
          ? yearEndReturns(row.performance.fund.points, principal)
          : yearEndGrowth(row.performance.fund.points),
    }));
    const bench = rows[0]?.performance.benchmark;
    if (bench) {
      lines.push({
        id: `bench-${bench.ticker}`,
        label: rows[0].performance.benchmark_tracks || bench.ticker,
        color: BENCHMARK_COLOR,
        dashed: true,
        points:
          unit === "percent"
            ? yearEndReturns(bench.points, principal)
            : yearEndGrowth(bench.points),
      });
    }
    return lines;
  }, [principal, rows, unit]);

  const taxSeries = useMemo<TaxDragFundSeries[]>(() => {
    if (!rows) return [];
    return rows.map((row) => ({
      id: row.performance.fund_ticker,
      label: `${row.input.label || row.performance.fund_name} tax drag`,
      description: TAX_FOCUS[row.performance.fund_ticker],
      color: row.color,
      points: row.tax
        ? toNegativeTaxDrag(
            alignYears(
              toTaxDragPeriods(
                row.tax,
                unit === "percent" ? "effective_tax" : "tax_dollars",
              ),
              years,
            ),
          )
        : years.map((year) => ({ year, value: null })),
    }));
  }, [rows, unit, years]);

  const annualized = useMemo(() => {
    if (!rows || years.length < 2) return [];
    const span = years[years.length - 1] - years[0];
    return growthSeries.map((row) => {
      const first = row.points[0];
      const last = row.points[row.points.length - 1];
      return {
        id: row.id,
        label: row.label,
        value:
          first && last ? cagr(first.value, last.value, Math.max(span, 1)) : null,
      };
    });
  }, [growthSeries, rows, years]);

  function commitPrincipal() {
    const parsed = Number(principalDraft.replace(/[$,\s]/g, ""));
    if (!Number.isFinite(parsed) || parsed <= 0) {
      setPrincipalDraft(String(principal));
      return;
    }
    setPrincipal(parsed);
    setPrincipalDraft(String(parsed));
  }

  function addFund(tickerRaw: string) {
    const ticker = tickerRaw.trim().toUpperCase();
    if (!ticker) return;
    if (selected.some((fund) => fundKey(fund).ticker === ticker)) return;
    if (selected.length >= MAX_GROWTH_FUNDS) return;
    const catalog = PERFORMANCE_CATALOG.find((row) => row.ticker === ticker);
    setSelected((current) => [
      ...current,
      {
        ticker,
        label: catalog?.name ?? ticker,
        fundIdentifier: ticker,
      },
    ]);
    setAddTicker("");
  }

  function removeFund(ticker: string) {
    setSelected((current) =>
      current.length <= 1
        ? current
        : current.filter((fund) => fundKey(fund).ticker !== ticker),
    );
  }

  const remaining = PERFORMANCE_FIXTURE_TICKERS.filter(
    (ticker) => !selected.some((fund) => fundKey(fund).ticker === ticker),
  );

  return (
    <article
      className={`rounded-2xl border border-line bg-surface px-5 py-5 shadow-[0_8px_24px_rgba(26,29,26,0.08)] ${className}`}
    >
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-faint">
            <span aria-hidden className="inline-block size-1.5 rounded-full bg-tax-less" />
            Aftertax
          </p>
          <h2 className="mt-1 font-serif text-xl tracking-tight text-ink">
            Growth and tax drag
          </h2>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div
            className="inline-flex rounded-md border border-line bg-paper p-0.5 text-[11px] font-semibold uppercase tracking-[0.12em]"
            role="group"
            aria-label="Dollars or percent"
          >
            <button
              type="button"
              onClick={() => setUnit("dollars")}
              className={`h-8 rounded px-2.5 ${
                unit === "dollars" ? "bg-accent text-white" : "text-muted"
              }`}
            >
              $
            </button>
            <button
              type="button"
              onClick={() => setUnit("percent")}
              className={`h-8 rounded px-2.5 ${
                unit === "percent" ? "bg-accent text-white" : "text-muted"
              }`}
            >
              %
            </button>
          </div>
          {editablePrincipal ? (
            <label className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-faint">
              Growth of
              <span className="sr-only">dollars</span>
              <input
                type="text"
                inputMode="decimal"
                value={principalDraft}
                onChange={(event) => setPrincipalDraft(event.target.value)}
                onBlur={commitPrincipal}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    event.currentTarget.blur();
                  }
                }}
                className="h-9 w-[7.5rem] rounded-md border border-line bg-paper px-2 text-right font-mono text-sm font-normal normal-case tracking-normal text-ink"
                aria-label="Starting dollars"
              />
            </label>
          ) : (
            <p className="text-sm text-muted">{formatUsd(principal, 0)}</p>
          )}
        </div>
      </header>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        {selected.map((fund, index) => (
          <span
            key={fund.ticker}
            className="inline-flex items-center gap-1.5 rounded-full bg-paper px-2.5 py-1 text-[12px] text-ink ring-1 ring-line"
          >
            <span
              className="inline-block size-2 rounded-full"
              style={{ background: fundSeriesColor(index) }}
            />
            {fund.label || fund.ticker}
            {selected.length > 1 ? (
              <button
                type="button"
                onClick={() => removeFund(fund.ticker)}
                className="ml-0.5 text-faint hover:text-ink"
                aria-label={`Remove ${fund.ticker}`}
              >
                ×
              </button>
            ) : null}
          </span>
        ))}

        {allowAddFund && selected.length < MAX_GROWTH_FUNDS ? (
          <form
            className="flex items-center gap-1.5"
            onSubmit={(event) => {
              event.preventDefault();
              addFund(addTicker);
            }}
          >
            <input
              list="growth-tax-funds"
              value={addTicker}
              onChange={(event) => setAddTicker(event.target.value)}
              placeholder="Add fund"
              className="h-8 w-28 rounded-md border border-line bg-paper px-2 text-sm text-ink placeholder:text-faint"
              aria-label="Add fund ticker"
            />
            <datalist id="growth-tax-funds">
              {remaining.map((ticker) => (
                <option key={ticker} value={ticker} />
              ))}
            </datalist>
            <button
              type="submit"
              className="h-8 rounded-md bg-accent px-2.5 text-[12px] text-white hover:bg-accent-hover"
            >
              Add fund
            </button>
          </form>
        ) : null}
      </div>

      {error ? (
        <div className="mt-5 rounded-md border border-tax-more/20 bg-tax-more-soft px-4 py-4">
          <p className="font-serif text-lg text-tax-more">Module unavailable</p>
          <p className="mt-1 text-sm text-ink">{error}</p>
          <button
            type="button"
            onClick={() => setRetry((value) => value + 1)}
            className="mt-3 h-9 rounded-md bg-accent px-3 text-sm text-white hover:bg-accent-hover"
          >
            Retry
          </button>
        </div>
      ) : (
        <div className="mt-5 flex flex-col gap-6">
          <GrowthOfXChart
            years={years}
            series={growthSeries}
            startDollars={principal}
            unit={unit}
            annualized={annualized}
            showAnnualized={showAnnualized}
            loading={loading}
          />
          <div className="border-t border-line pt-5">
            <TaxDragByYearChart
              series={taxSeries}
              years={years}
              metric={unit === "percent" ? "effective_tax" : "tax_dollars"}
              orientation="down"
              showBarLabels={selected.length <= 2}
              layout="flush"
              title={
                unit === "percent"
                  ? "Estimated annual tax drag (based on hypothetical distributions & tax rates)"
                  : "Estimated annual tax dollars (based on hypothetical distributions & tax rates)"
              }
              loading={loading}
              emptyLabel="No overlapping tax-drag years"
            />
          </div>
        </div>
      )}

      <p className="mt-4 text-[10px] leading-relaxed text-faint">
        Growth from GET /performance and POST /performance/growth. Tax bars from
        POST /illustrate/compare periods. Hypothetical illustration only.
      </p>
    </article>
  );
}

function fundKey(fund: GrowthFundInput): GrowthFundInput {
  return {
    ticker: fund.ticker.trim().toUpperCase(),
    label: fund.label,
    fundIdentifier: fund.fundIdentifier,
    fundFamily: fund.fundFamily,
  };
}

function alignYears(
  points: { year: number; value: number | null }[],
  years: number[],
) {
  return years.map((year) => {
    const match = points.find((point) => point.year === year);
    return { year, value: match?.value ?? null };
  });
}

async function loadModule(
  funds: GrowthFundInput[],
  principal: number,
  benchmark: string | null,
  periods: ComparePeriodIn[] | undefined,
  signal: AbortSignal,
): Promise<LoadedFund[]> {
  return Promise.all(
    funds.map(async (input, index) => {
      const ticker = input.ticker.trim().toUpperCase();
      const usePost = principal !== DEFAULT_START_DOLLARS;
      const request = {
        ticker,
        fund_identifier: input.fundIdentifier ?? ticker,
        benchmark,
        start_dollars: principal,
        mode: "fixture" as const,
      };
      const performance = usePost
        ? await postPerformanceGrowth(request, { signal })
        : await fetchPerformance(request, { signal });

      const yearPoints = yearEndGrowth(performance.fund.points);
      const taxYears =
        periods && periods.length > 0
          ? periods
          : yearPoints.map((point) => ({ year: point.year }));
      const taxPeriods =
        taxYears.length >= 2
          ? taxYears
          : [{ year: 2021 }, { year: 2022 }, { year: 2023 }, { year: 2024 }, { year: 2025 }];

      let tax: CompareResponse | null = null;
      try {
        tax = await postIllustrateCompare(
          {
            mode: "yoy",
            holding_dollars: 10_000,
            combine_state_with_federal: true,
            latest_as_of_only: true,
            selectors: {
              ticker,
              fund_identifier: input.fundIdentifier ?? ticker,
              fund_family: input.fundFamily,
              fund_name: input.label,
            },
            left: {
              label: input.label ?? ticker,
              selectors: {
                ticker,
                fund_identifier: input.fundIdentifier ?? ticker,
                fund_family: input.fundFamily,
                fund_name: input.label,
              },
            },
            periods: taxPeriods,
            tax_rates: {},
          },
          { signal },
        );
      } catch {
        tax = null;
      }

      return {
        input,
        color: fundSeriesColor(index),
        performance,
        tax,
      };
    }),
  );
}
