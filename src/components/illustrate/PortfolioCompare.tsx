"use client";

import { useEffect, useMemo, useState } from "react";
import { AllocationColumn } from "@/components/illustrate/portfolio-compare/AllocationColumn";
import { SummaryStrip } from "@/components/illustrate/portfolio-compare/SummaryStrip";
import { TaxImpactChart } from "@/components/illustrate/portfolio-compare/TaxImpactChart";
import { UpcomingTable } from "@/components/illustrate/portfolio-compare/UpcomingTable";
import { catalogFunds } from "@/lib/illustrate/portfolio-compare-catalog";
import {
  smokeCurrentHoldings,
  smokeProposedHoldings,
} from "@/lib/illustrate/portfolio-compare-catalog";
import { postIllustratePortfolioCompare } from "@/lib/illustrate/portfolio-compare-client";
import {
  taxImpactBarsForSide,
  upcomingRowsForSide,
} from "@/lib/illustrate/portfolio-compare-map";
import type {
  AllocationUnit,
  PortfolioCompareResponse,
  PortfolioFundOption,
  PortfolioHoldingDraft,
} from "@/lib/illustrate/portfolio-compare-types";
import { PORTFOLIO_COMPARE_BOOK_DOLLARS } from "@/lib/illustrate/portfolio-compare-types";
import type { TaxRates } from "@/lib/illustrate/types";
import { UI_DEFAULT_TAX_RATES } from "@/lib/illustrate/types";

export type PortfolioCompareProps = {
  bookDollars?: number;
  current?: PortfolioHoldingDraft[];
  proposed?: PortfolioHoldingDraft[];
  funds?: PortfolioFundOption[];
  taxRates?: Partial<TaxRates>;
  className?: string;
};

function toApiHoldings(holdings: PortfolioHoldingDraft[]) {
  return holdings
    .filter((holding) => holding.ticker.trim() && holding.weightPct > 0)
    .map((holding) => ({
      ticker: holding.ticker.trim().toUpperCase(),
      fund_identifier: holding.ticker.trim().toUpperCase(),
      fund_name: holding.fundName || undefined,
      fund_family: holding.family,
      weight_pct: holding.weightPct,
    }));
}

function rescaleFromWeights(
  holdings: PortfolioHoldingDraft[],
  bookDollars: number,
): PortfolioHoldingDraft[] {
  return holdings.map((holding) => ({
    ...holding,
    holdingDollars: (holding.weightPct / 100) * bookDollars,
  }));
}

function formatBookInput(value: number): string {
  return value.toLocaleString("en-US");
}

export function PortfolioCompare({
  bookDollars: bookDollarsProp = PORTFOLIO_COMPARE_BOOK_DOLLARS,
  current: currentProp,
  proposed: proposedProp,
  funds: fundsProp,
  taxRates,
  className = "",
}: PortfolioCompareProps) {
  const funds = useMemo(() => catalogFunds(fundsProp ?? []), [fundsProp]);
  const [bookDollars, setBookDollars] = useState(bookDollarsProp);
  const [bookInput, setBookInput] = useState(formatBookInput(bookDollarsProp));
  const [currentUnit, setCurrentUnit] = useState<AllocationUnit>("pct");
  const [proposedUnit, setProposedUnit] = useState<AllocationUnit>("pct");
  const [current, setCurrent] = useState<PortfolioHoldingDraft[]>(
    () => currentProp ?? smokeCurrentHoldings(bookDollarsProp, funds),
  );
  const [proposed, setProposed] = useState<PortfolioHoldingDraft[]>(
    () => proposedProp ?? smokeProposedHoldings(bookDollarsProp, funds),
  );
  const [retry, setRetry] = useState(0);
  const [result, setResult] = useState<PortfolioCompareResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  function commitBook(raw: string) {
    const parsed = Number(raw.replace(/,/g, ""));
    if (!(parsed > 0)) {
      setBookInput(formatBookInput(bookDollars));
      return;
    }
    setBookDollars(parsed);
    setBookInput(formatBookInput(parsed));
    setCurrent((holdings) => rescaleFromWeights(holdings, parsed));
    setProposed((holdings) => rescaleFromWeights(holdings, parsed));
  }

  const currentApi = toApiHoldings(current);
  const proposedApi = toApiHoldings(proposed);
  const canFetch = currentApi.length > 0 && proposedApi.length > 0;
  const requestKey = JSON.stringify({
    bookDollars,
    current: currentApi,
    proposed: proposedApi,
    taxRates: taxRates ?? { state: UI_DEFAULT_TAX_RATES.state },
    retry,
  });

  useEffect(() => {
    if (!canFetch) return;

    const payload = JSON.parse(requestKey) as {
      bookDollars: number;
      current: ReturnType<typeof toApiHoldings>;
      proposed: ReturnType<typeof toApiHoldings>;
      taxRates: Partial<TaxRates>;
    };

    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setLoading(true);
      void postIllustratePortfolioCompare(
        {
          current: {
            label: "Current Allocation",
            book_dollars: payload.bookDollars,
            holdings: payload.current,
          },
          proposed: {
            label: "Proposed Allocation",
            book_dollars: payload.bookDollars,
            holdings: payload.proposed,
          },
          tax_rates: payload.taxRates,
          combine_state_with_federal: true,
        },
        { signal: controller.signal },
      )
        .then((payloadResult) => {
          setResult(payloadResult);
          setError(null);
          setLoading(false);
        })
        .catch((caught: unknown) => {
          if (caught instanceof DOMException && caught.name === "AbortError") return;
          setResult(null);
          setError(caught instanceof Error ? caught.message : "Portfolio compare failed");
          setLoading(false);
        });
    }, 250);

    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [canFetch, requestKey]);

  const currentUpcoming = result
    ? upcomingRowsForSide(result.current, "current")
    : [];
  const proposedUpcoming = result
    ? upcomingRowsForSide(result.proposed, "proposed")
    : [];
  const currentBars = result ? taxImpactBarsForSide(result.current) : [];
  const proposedBars = result ? taxImpactBarsForSide(result.proposed) : [];
  const sample = Boolean(
    result &&
      (result.source === "mock" ||
        result.notes.some((note) => /mock|demo|illustrative/i.test(note))),
  );

  return (
    <article className={`portfolio-compare w-full ${className}`}>
      <header className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-faint">
            <span aria-hidden className="inline-block size-1.5 rounded-full bg-tax-less" />
            Aftertax · {sample || !result ? "Sample" : "Live"}
          </p>
          <h1 className="mt-1 font-serif text-3xl tracking-tight text-ink">
            Portfolio comparison
          </h1>
        </div>
        <label className="block">
          <span className="mb-1.5 block text-[10px] font-semibold uppercase tracking-[0.14em] text-faint">
            Portfolio value
          </span>
          <div className="relative w-[12.5rem]">
            <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-faint">
              $
            </span>
            <input
              inputMode="decimal"
              value={bookInput}
              onChange={(event) => setBookInput(event.target.value)}
              onBlur={(event) => commitBook(event.target.value)}
              className="h-11 w-full rounded-md border border-line bg-surface pl-7 pr-3 font-mono text-base text-ink shadow-[0_1px_2px_rgba(26,29,26,0.04)]"
            />
          </div>
        </label>
      </header>

      <div className="grid grid-cols-1 items-stretch gap-4 lg:grid-cols-2 lg:grid-rows-[auto_auto_auto] lg:[grid-template-areas:'holdings-c_holdings-p'_'charts-c_charts-p'_'tables-c_tables-p']">
        <AllocationColumn
          title="Current allocation"
          holdings={current}
          bookDollars={bookDollars}
          unit={currentUnit}
          funds={funds}
          inputIdPrefix="current"
          onUnitChange={setCurrentUnit}
          onChange={setCurrent}
          className="h-full lg:[grid-area:holdings-c]"
        />
        {!canFetch ? null : loading && !result ? (
          <div
            className="h-44 min-h-44 animate-pulse rounded-2xl border border-line bg-surface lg:h-full lg:[grid-area:charts-c]"
            aria-busy
            aria-label="Loading current tax impact"
          />
        ) : result ? (
          <TaxImpactChart
            headingId="tax-impact-current"
            bars={currentBars}
            className="h-full min-h-44 lg:[grid-area:charts-c]"
          />
        ) : null}
        {!canFetch ? null : loading && !result ? (
          <div
            className="h-48 min-h-48 animate-pulse rounded-2xl border border-line bg-surface lg:h-full lg:[grid-area:tables-c]"
            aria-busy
            aria-label="Loading current upcoming distributions"
          />
        ) : result ? (
          <UpcomingTable
            headingId="upcoming-current"
            rows={currentUpcoming}
            sideLabel="Current"
            className="h-full lg:[grid-area:tables-c]"
          />
        ) : null}

        <AllocationColumn
          title="Proposed allocation"
          holdings={proposed}
          bookDollars={bookDollars}
          unit={proposedUnit}
          funds={funds}
          inputIdPrefix="proposed"
          onUnitChange={setProposedUnit}
          onChange={setProposed}
          className="h-full lg:[grid-area:holdings-p]"
        />
        {!canFetch ? null : loading && !result ? (
          <div
            className="h-44 min-h-44 animate-pulse rounded-2xl border border-line bg-surface lg:h-full lg:[grid-area:charts-p]"
            aria-busy
            aria-label="Loading proposed tax impact"
          />
        ) : result ? (
          <TaxImpactChart
            headingId="tax-impact-proposed"
            bars={proposedBars}
            className="h-full min-h-44 lg:[grid-area:charts-p]"
          />
        ) : null}
        {!canFetch ? null : loading && !result ? (
          <div
            className="h-48 min-h-48 animate-pulse rounded-2xl border border-line bg-surface lg:h-full lg:[grid-area:tables-p]"
            aria-busy
            aria-label="Loading proposed upcoming distributions"
          />
        ) : result ? (
          <UpcomingTable
            headingId="upcoming-proposed"
            rows={proposedUpcoming}
            sideLabel="Proposed"
            className="h-full lg:[grid-area:tables-p]"
          />
        ) : null}
      </div>

      <div className="mt-4">
        {!canFetch ? (
          <p className="rounded-2xl border border-dashed border-line-strong bg-surface px-5 py-4 text-sm text-muted">
            Add at least one weighted holding on each side.
          </p>
        ) : loading && !result ? (
          <div
            className="h-[7.5rem] animate-pulse rounded-2xl border border-line bg-surface"
            aria-busy
            aria-label="Loading portfolio tax summary"
          />
        ) : error ? (
          <div className="rounded-2xl border border-tax-more/20 bg-tax-more-soft px-5 py-4">
            <p className="font-serif text-lg text-tax-more">Compare unavailable</p>
            <p className="mt-1 text-sm text-ink">{error}</p>
            <button
              type="button"
              onClick={() => setRetry((value) => value + 1)}
              className="mt-3 h-9 rounded-md bg-accent px-3 text-sm text-white hover:bg-accent-hover"
            >
              Retry
            </button>
          </div>
        ) : result ? (
          <div className={loading ? "opacity-70" : ""}>
            <SummaryStrip result={result} bookDollars={bookDollars} />
          </div>
        ) : null}
      </div>

      <p className="mt-5 text-center text-[10px] leading-relaxed text-faint">
        Demo data · weights × Portfolio Value → dollars · tax from Data API TBD
      </p>
    </article>
  );
}
