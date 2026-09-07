"use client";

import { useEffect, useMemo, useState } from "react";
import { GrowthOfXChart, type GrowthLineSeries } from "@/components/illustrate/GrowthOfXChart";
import { TaxDragByYearChart } from "@/components/illustrate/TaxDragByYearChart";
import {
  BENCHMARK_COLOR,
  MAX_GROWTH_FUNDS,
  fundSeriesColor,
} from "@/lib/charts/series-colors";
import {
  cagr,
  rebaseWindow,
  sketchYears,
  yearEndGrowth,
} from "@/lib/charts/shared-axis";
import { formatUsd } from "@/lib/format";
import { postIllustrateCompare } from "@/lib/illustrate/compare-client";
import type { ComparePeriodIn, CompareResponse } from "@/lib/illustrate/compare-types";
import {
  toNegativeTaxDrag,
  toTaxDragPeriods,
  type TaxDragFundSeries,
} from "@/lib/illustrate/tax-drag-chart";
import { fetchPerformance, postPerformanceGrowth } from "@/lib/performance/client";
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
    label: "AGTHX",
    fundIdentifier: "AGTHX",
    fundFamily: "American Funds",
  },
  {
    ticker: "FCNTX",
    label: "FCNTX",
    fundIdentifier: "FCNTX",
    fundFamily: "Fidelity",
  },
];

const SKETCH_DISCLAIMER =
  "Hypothetical illustration based on estimated distributions and assumed tax rates. Estimates only — not tax advice. Past performance does not guarantee future results.";

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
  const [principalDraft, setPrincipalDraft] = useState(formatPrincipal(startDollars));
  const [addTicker, setAddTicker] = useState("");
  const [adding, setAdding] = useState(false);
  const [unit, setUnit] = useState<"mixed" | "dollars" | "percent">("mixed");
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
    return sketchYears([...set].sort((a, b) => a - b));
  }, [rows]);

  const growthSeries = useMemo<GrowthLineSeries[]>(() => {
    if (!rows) return [];
    const asReturn = unit === "percent";
    const lines: GrowthLineSeries[] = rows.map((row) => ({
      id: row.performance.fund_ticker,
      label: row.performance.fund_ticker,
      color: row.color,
      points: windowedGrowth(row.performance.fund.points, years, principal, asReturn),
    }));
    const bench = rows[0]?.performance.benchmark;
    if (bench) {
      lines.push({
        id: `bench-${bench.ticker}`,
        label: rows[0].performance.benchmark_tracks || bench.ticker,
        color: BENCHMARK_COLOR,
        dashed: true,
        points: windowedGrowth(bench.points, years, principal, asReturn),
      });
    }
    return lines;
  }, [principal, rows, unit, years]);

  const taxSeries = useMemo<TaxDragFundSeries[]>(() => {
    if (!rows) return [];
    return rows.map((row) => ({
      id: row.performance.fund_ticker,
      label: row.performance.fund_ticker,
      color: row.color,
      points: row.tax
        ? toNegativeTaxDrag(
            alignYears(
              toTaxDragPeriods(
                row.tax,
                unit === "dollars" ? "tax_dollars" : "effective_tax",
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
    const dollarSeries: {
      id: string;
      label: string;
      color?: string;
      points: { year: number; value: number }[];
    }[] =
      rows.map((row) => ({
        id: row.performance.fund_ticker,
        label: row.performance.fund_ticker,
        color: row.color,
        points: windowedGrowth(row.performance.fund.points, years, principal, false),
      }));
    const bench = rows[0]?.performance.benchmark;
    if (bench) {
      dollarSeries.push({
        id: `bench-${bench.ticker}`,
        label: rows[0].performance.benchmark_tracks || bench.ticker,
        points: windowedGrowth(bench.points, years, principal, false),
      });
    }
    return dollarSeries.map((row) => {
      const first = row.points[0];
      const last = row.points[row.points.length - 1];
      return {
        id: row.id,
        label: row.label,
        color: row.color,
        value:
          first && last ? cagr(first.value, last.value, Math.max(span, 1)) : null,
      };
    });
  }, [principal, rows, years]);

  function commitPrincipal() {
    const parsed = Number(principalDraft.replace(/[$,\s]/g, ""));
    if (!Number.isFinite(parsed) || parsed <= 0) {
      setPrincipalDraft(String(principal));
      return;
    }
    setPrincipal(parsed);
    setPrincipalDraft(formatPrincipal(parsed));
  }

  function addFund(tickerRaw: string) {
    const ticker = tickerRaw.trim().toUpperCase();
    if (!ticker) return;
    if (selected.some((fund) => fundKey(fund).ticker === ticker)) return;
    if (selected.length >= MAX_GROWTH_FUNDS) return;
    setSelected((current) => [
      ...current,
      {
        ticker,
        label: ticker,
        fundIdentifier: ticker,
      },
    ]);
    setAddTicker("");
    setAdding(false);
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

  const growthUnit = unit === "percent" ? "percent" : "dollars";
  const taxMetric = unit === "dollars" ? "tax_dollars" : "effective_tax";

  return (
    <article
      className={`rounded-2xl border border-line bg-surface px-5 py-5 shadow-[0_8px_24px_rgba(26,29,26,0.08)] ${className}`}
    >
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-faint">
            <span aria-hidden className="inline-block size-1.5 rounded-full bg-tax-less" />
            Aftertax · Sample
          </p>
          <h2 className="mt-1 font-serif text-xl tracking-tight text-ink">
            Growth & tax drag
          </h2>
        </div>

        <div className="flex flex-wrap items-end gap-2">
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
            <label className="block text-[10px] font-semibold uppercase tracking-[0.12em] text-faint">
              Growth of $
              <input
                type="text"
                inputMode="decimal"
                value={principalDraft}
                onChange={(event) => setPrincipalDraft(event.target.value)}
                onFocus={() => setPrincipalDraft(String(principal))}
                onBlur={() => {
                  commitPrincipal();
                  setPrincipalDraft(formatPrincipal(principal));
                }}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    event.currentTarget.blur();
                  }
                }}
                className="mt-1 block h-9 w-[7.5rem] rounded-md border border-line bg-paper px-2 text-right font-mono text-sm font-normal normal-case tracking-normal text-ink"
                aria-label="Starting dollars"
              />
            </label>
          ) : (
            <p className="text-sm text-muted">{formatUsd(principal, 0)}</p>
          )}
          {allowAddFund && selected.length < MAX_GROWTH_FUNDS ? (
            adding ? (
              <form
                className="flex items-end gap-1.5"
                onSubmit={(event) => {
                  event.preventDefault();
                  addFund(addTicker);
                }}
              >
                <input
                  list="growth-tax-funds"
                  value={addTicker}
                  onChange={(event) => setAddTicker(event.target.value)}
                  placeholder="Ticker"
                  className="h-9 w-24 rounded-md border border-line bg-paper px-2 text-sm text-ink placeholder:text-faint"
                  aria-label="Add fund ticker"
                  autoFocus
                />
                <datalist id="growth-tax-funds">
                  {remaining.map((ticker) => (
                    <option key={ticker} value={ticker} />
                  ))}
                </datalist>
                <button
                  type="submit"
                  className="h-9 rounded-md bg-accent px-2.5 text-[12px] text-white hover:bg-accent-hover"
                >
                  Add
                </button>
              </form>
            ) : (
              <button
                type="button"
                onClick={() => setAdding(true)}
                className="h-9 rounded-md border border-dashed border-line-strong px-3 text-[12px] text-muted hover:border-ink hover:text-ink"
              >
                + Add Fund
              </button>
            )
          ) : null}
        </div>
      </header>

      {selected.length > 2 ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {selected.map((fund, index) => (
            <span
              key={fund.ticker}
              className="inline-flex items-center gap-1.5 rounded-full bg-paper px-2.5 py-1 text-[12px] text-ink ring-1 ring-line"
            >
              <span
                className="inline-block size-2 rounded-full"
                style={{ background: fundSeriesColor(index) }}
              />
              {fund.ticker}
              <button
                type="button"
                onClick={() => removeFund(fund.ticker)}
                className="text-faint hover:text-ink"
                aria-label={`Remove ${fund.ticker}`}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      ) : null}

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
        <div className="mt-5 flex flex-col gap-4">
          <div className="rounded-xl border border-line bg-paper/40 px-3 py-3 sm:px-4">
            <GrowthOfXChart
              years={years}
              series={growthSeries}
              startDollars={principal}
              unit={growthUnit}
              annualized={annualized}
              showAnnualized={showAnnualized}
              loading={loading}
            />
          </div>
          <div className="rounded-xl border border-line bg-paper/40 px-3 py-3 sm:px-4">
            <TaxDragByYearChart
              series={taxSeries}
              years={years}
              metric={taxMetric}
              orientation="down"
              showBarLabels={selected.length <= 2}
              layout="flush"
              title="Estimated annual tax drag"
              loading={loading}
              emptyLabel="No overlapping tax-drag years"
            />
          </div>
        </div>
      )}

      <p className="mt-4 text-[10px] leading-relaxed text-faint">
        {SKETCH_DISCLAIMER}
      </p>
    </article>
  );
}

function windowedGrowth(
  points: { date: string; growth_of_x: number }[],
  years: number[],
  principal: number,
  asReturn: boolean,
) {
  const rebased = rebaseWindow(
    yearEndGrowth(points).filter((point) => years.includes(point.year)),
    principal,
  );
  if (!asReturn) return rebased;
  return rebased.map((point) => ({
    year: point.year,
    value: principal > 0 ? point.value / principal - 1 : 0,
  }));
}

function formatPrincipal(value: number): string {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);
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
