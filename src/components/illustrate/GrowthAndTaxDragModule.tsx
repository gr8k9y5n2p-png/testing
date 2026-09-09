"use client";

import { useEffect, useMemo, useState } from "react";
import { CompactDisclaimer } from "@/components/CompactDisclaimer";
import { GrowthOfXChart } from "@/components/illustrate/GrowthOfXChart";
import { TaxDragByYearChart } from "@/components/illustrate/TaxDragByYearChart";
import {
  MAX_GROWTH_FUNDS,
  fundSeriesColor,
} from "@/lib/charts/series-colors";
import {
  SHARED_CHART_PAD,
  SHARED_CHART_WIDTH,
  yearLayout,
} from "@/lib/charts/shared-axis";
import { formatUsd } from "@/lib/format";
import type { ComparePeriodIn } from "@/lib/illustrate/compare-types";
import {
  annualizedFromRows,
  calendarYearsFromRows,
  growthLinesFromRows,
  loadGrowthAndTaxDrag,
  taxSeriesFromRows,
  type GrowthFundInput,
  type LoadedGrowthFund,
} from "@/lib/illustrate/growth-tax-load";
import { type TaxDragMetric } from "@/lib/illustrate/tax-drag-chart";
import { UI_DEFAULT_TAX_RATES, type TaxRates } from "@/lib/illustrate/types";
import {
  PERFORMANCE_UNAVAILABLE_HINT,
  PERFORMANCE_UNAVAILABLE_LABEL,
} from "@/lib/performance/coverage";
import { shouldOpenFundSuggestions } from "@/components/illustrate/fund-picker-suggestions";
import { DEFAULT_START_DOLLARS, PERFORMANCE_FIXTURE_TICKERS } from "@/lib/performance/types";

export type { GrowthFundInput } from "@/lib/illustrate/growth-tax-load";

export type GrowthAndTaxDragModuleProps = {
  /** Initial series. Empty / omitted starts with no funds until search or Add Fund. */
  funds?: GrowthFundInput[];
  /** Tickers to prepend when search/illustrate selection changes. Does not reset Add Fund extras. */
  seedFunds?: GrowthFundInput[];
  startDollars?: number;
  benchmark?: string;
  periods?: ComparePeriodIn[];
  className?: string;
  showAnnualized?: boolean;
  allowAddFund?: boolean;
  editablePrincipal?: boolean;
  /** Compare slots: replace the series when seedFunds change. */
  lockToSeed?: boolean;
  /** Compare / illustration rates. Defaults to locked top-bracket UI set. */
  taxRates?: TaxRates;
  combineStateWithFederal?: boolean;
};

const SKETCH_DISCLAIMER =
  "Hypothetical illustration based on estimated distributions and assumed tax rates. Estimates only — not tax advice. Past performance does not guarantee future results. Up to 6 funds + benchmark.";

export function GrowthAndTaxDragModule({
  funds = [],
  seedFunds,
  startDollars = DEFAULT_START_DOLLARS,
  benchmark,
  periods,
  className = "",
  showAnnualized = true,
  allowAddFund = true,
  editablePrincipal = true,
  lockToSeed = false,
  taxRates = UI_DEFAULT_TAX_RATES,
  combineStateWithFederal = true,
}: GrowthAndTaxDragModuleProps) {
  const [selected, setSelected] = useState<GrowthFundInput[]>(() =>
    funds.slice(0, MAX_GROWTH_FUNDS),
  );
  const [principal, setPrincipal] = useState(startDollars);
  const [principalDraft, setPrincipalDraft] = useState(formatPrincipal(startDollars));
  const [addTicker, setAddTicker] = useState("");
  const [adding, setAdding] = useState(false);
  const [taxMetric, setTaxMetric] = useState<TaxDragMetric>("effective_tax");
  const [retry, setRetry] = useState(0);
  const [rows, setRows] = useState<LoadedGrowthFund[] | null>(null);
  const [missingTickers, setMissingTickers] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [settledKey, setSettledKey] = useState<string | null>(null);

  const requestKey = JSON.stringify({
    funds: selected.map((fund) => fundKey(fund)),
    principal,
    benchmark: benchmark ?? null,
    periods: periods ?? null,
    taxRates,
    combineStateWithFederal,
  });
  const fetchKey = `${requestKey}:${retry}`;
  const loading = selected.length > 0 && settledKey !== fetchKey;
  const seedKey = JSON.stringify((seedFunds ?? []).map(fundKey));

  useEffect(() => {
    const seeds = JSON.parse(seedKey) as GrowthFundInput[];
    if (lockToSeed) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- Compare slots own the series
      setSelected(seeds.slice(0, MAX_GROWTH_FUNDS));
      return;
    }
    if (seeds.length === 0) return;
    // Homepage remounts pass a new funds[] seed; merge without dropping user adds.
    setSelected((current) => mergeSeedFunds(current, seeds));
  }, [seedKey, lockToSeed]);

  useEffect(() => {
    if (editablePrincipal) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- Compare owns the shared holding
    setPrincipal(startDollars);
    setPrincipalDraft(formatPrincipal(startDollars));
  }, [editablePrincipal, startDollars]);

  useEffect(() => {
    const controller = new AbortController();
    const next = JSON.parse(requestKey) as {
      funds: GrowthFundInput[];
      principal: number;
      benchmark: string | null;
      taxRates: TaxRates;
      combineStateWithFederal: boolean;
    };

    if (next.funds.length === 0) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- empty selection must drop stale series
      setRows([]);
      setMissingTickers([]);
      setError(null);
      setSettledKey(fetchKey);
      return;
    }

    const timer = window.setTimeout(() => {
      void loadGrowthAndTaxDrag(
        next.funds,
        next.principal,
        next.benchmark,
        periods,
        controller.signal,
        {
          taxRates: next.taxRates,
          combineStateWithFederal: next.combineStateWithFederal,
        },
      )
        .then((loaded) => {
          setRows(loaded.rows);
          setMissingTickers(loaded.missingTickers);
          setError(null);
          setSettledKey(fetchKey);
        })
        .catch((caught: unknown) => {
          if (caught instanceof DOMException && caught.name === "AbortError") return;
          // Keep last rows so tax-drag / historical bars are not blanked.
          setMissingTickers(
            next.funds.map((fund) => fund.ticker.trim().toUpperCase()).filter(Boolean),
          );
          setError(caught instanceof Error ? caught.message : "Growth chart failed");
          setSettledKey(fetchKey);
        });
    }, 250);

    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [requestKey, fetchKey, periods]);

  const years = useMemo(
    () => calendarYearsFromRows(rows, taxMetric),
    [rows, taxMetric],
  );

  const growthSeries = useMemo(
    () => growthLinesFromRows(rows, years, principal),
    [principal, rows, years],
  );

  const taxSeries = useMemo(
    () => taxSeriesFromRows(rows, years, taxMetric),
    [rows, taxMetric, years],
  );

  const annualized = useMemo(
    () => annualizedFromRows(rows, years, principal),
    [principal, rows, years],
  );

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
      current.filter((fund) => fundKey(fund).ticker !== ticker),
    );
  }

  const axis = useMemo(
    () => yearLayout(years, selected.length, SHARED_CHART_WIDTH, SHARED_CHART_PAD),
    [selected.length, years],
  );

  const remaining = PERFORMANCE_FIXTURE_TICKERS.filter(
    (ticker) => !selected.some((fund) => fundKey(fund).ticker === ticker),
  );

  return (
    <article
      className={`rounded-2xl border border-line bg-surface px-5 py-5 shadow-[0_8px_24px_rgba(26,29,26,0.08)] ${className}`}
    >
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-faint">
            <span aria-hidden className="inline-block size-1.5 rounded-full bg-tax-less" />
            Aftertax
          </p>
          <h2 className="mt-1 font-serif text-xl tracking-tight text-ink">
            Growth & tax drag
          </h2>
        </div>

        <div className="flex flex-wrap items-end gap-2">
          {editablePrincipal ? (
            <label className="block text-[10px] font-semibold uppercase tracking-[0.12em] text-faint">
              Growth of $
              <span className="relative mt-1 block">
                <span
                  aria-hidden
                  className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 font-mono text-sm text-faint"
                >
                  $
                </span>
                <input
                  type="text"
                  inputMode="decimal"
                  value={principalDraft}
                  onChange={(event) => setPrincipalDraft(event.target.value)}
                  onFocus={() => setPrincipalDraft(String(principal))}
                  onBlur={() => {
                    commitPrincipal();
                  }}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      event.currentTarget.blur();
                    }
                  }}
                  className="block h-9 w-[7.5rem] rounded-md border border-line bg-paper pl-6 pr-2 text-right font-mono text-sm font-normal normal-case tracking-normal text-ink"
                  aria-label="Starting dollars"
                />
              </span>
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
                  {shouldOpenFundSuggestions(addTicker)
                    ? remaining
                        .filter((ticker) =>
                          ticker
                            .toLowerCase()
                            .includes(addTicker.trim().toLowerCase()),
                        )
                        .map((ticker) => (
                          <option key={ticker} value={ticker} />
                        ))
                    : null}
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
          ) : allowAddFund ? (
            <p className="h-9 content-center text-[11px] text-faint">
              {MAX_GROWTH_FUNDS} of {MAX_GROWTH_FUNDS} funds
            </p>
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

      <div className="mt-5 flex flex-col gap-4">
        <div className="rounded-xl border border-line bg-paper/40 px-3 py-3 sm:px-4">
          {error ? (
            <div className="flex min-h-[160px] flex-col justify-center py-4">
              <p className="font-serif text-lg text-ink">{PERFORMANCE_UNAVAILABLE_LABEL}</p>
              <p className="mt-2 text-sm text-muted">{PERFORMANCE_UNAVAILABLE_HINT}</p>
              <button
                type="button"
                onClick={() => setRetry((value) => value + 1)}
                className="mt-3 h-9 w-fit rounded-md bg-accent px-3 text-sm text-white hover:bg-accent-hover"
              >
                Retry
              </button>
            </div>
          ) : (
            <>
              <GrowthOfXChart
                years={years}
                series={growthSeries}
                startDollars={principal}
                unit="dollars"
                annualized={annualized}
                showAnnualized={showAnnualized}
                loading={loading}
                axis={axis}
                emptyLabel={
                  selected.length === 0 ? "No fund series" : PERFORMANCE_UNAVAILABLE_LABEL
                }
                emptyHint={selected.length === 0 ? "" : PERFORMANCE_UNAVAILABLE_HINT}
                onRemoveSeries={removeFund}
              />
              {missingTickers.length > 0 && growthSeries.some((row) => !row.dashed) ? (
                <p className="mt-2 text-[11px] text-faint">
                  {missingTickers.join(", ")}: {PERFORMANCE_UNAVAILABLE_LABEL}
                </p>
              ) : null}
            </>
          )}
        </div>
        <div className="rounded-xl border border-line bg-paper/40 px-3 py-3 sm:px-4">
          <TaxDragByYearChart
            series={taxSeries}
            years={years}
            metric={taxMetric}
            onUnitChange={setTaxMetric}
            orientation="down"
            showBarLabels={selected.length <= 2}
            layout="flush"
            title="Estimated annual tax drag"
            loading={loading}
            onRemoveSeries={removeFund}
            axis={axis}
            emptyLabel={
              selected.length === 0
                ? "No fund series"
                : "No overlapping tax-drag years"
            }
            emptyHint={selected.length === 0 ? "" : undefined}
          />
        </div>
      </div>

      <p className="mt-4 text-[10px] leading-relaxed text-faint">
        {SKETCH_DISCLAIMER}
      </p>
      <CompactDisclaimer className="mt-1 text-[10px] leading-relaxed text-faint" />
    </article>
  );
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
    fundName: fund.fundName,
    navPerShare: fund.navPerShare,
  };
}

function mergeSeedFunds(
  current: GrowthFundInput[],
  seeds: GrowthFundInput[],
): GrowthFundInput[] {
  const seeded = seeds.map(fundKey);
  const seen = new Set(seeded.map((fund) => fund.ticker));
  const rest = current.filter((fund) => !seen.has(fundKey(fund).ticker));
  return [...seeded, ...rest].slice(0, MAX_GROWTH_FUNDS);
}
