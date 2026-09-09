"use client";

import { useEffect, useMemo, useState } from "react";
import { CompactDisclaimer } from "@/components/CompactDisclaimer";
import { NoticeToast, useNoticeToast } from "@/components/NoticeToast";
import { AllocationColumn } from "@/components/illustrate/portfolio-compare/AllocationColumn";
import { CalendarYearTaxTable } from "@/components/illustrate/portfolio-compare/CalendarYearTaxTable";
import { SummaryStrip } from "@/components/illustrate/portfolio-compare/SummaryStrip";
import { NeedFundPricePrompt } from "@/components/illustrate/NeedFundPricePrompt";
import { UpcomingTable } from "@/components/illustrate/portfolio-compare/UpcomingTable";
import { navFromFundMetadata } from "@/lib/illustrate/compare-request";
import {
  isMissingNavError,
  NEED_FUND_PRICE_COPY,
} from "@/lib/illustrate/illustrate-error";
import { catalogFunds } from "@/lib/illustrate/portfolio-compare-catalog";
import {
  smokeCurrentHoldings,
  smokeProposedHoldings,
} from "@/lib/illustrate/portfolio-compare-catalog";
import { postIllustratePortfolioCompare } from "@/lib/illustrate/portfolio-compare-client";
import {
  upcomingHoldingsForSide,
  withUpcomingNav,
} from "@/lib/illustrate/portfolio-compare-map";
import type {
  AllocationUnit,
  PortfolioCompareResponse,
  PortfolioFundOption,
  PortfolioHoldingDraft,
} from "@/lib/illustrate/portfolio-compare-types";
import { PORTFOLIO_COMPARE_BOOK_DOLLARS } from "@/lib/illustrate/portfolio-compare-types";
import {
  EMPTY_BOOK_INVITE,
  UPCOMING_MODULE_HEADING,
} from "@/lib/illustrate/portfolio-compare-copy";
import { calendarYearTaxTable, defaultPortfolioComparePeriods } from "@/lib/illustrate/portfolio-year-tax";
import type { TaxRates } from "@/lib/illustrate/types";
import { UI_DEFAULT_TAX_RATES } from "@/lib/illustrate/types";

export type PortfolioCompareProps = {
  /** Defaults to $1,000,000. */
  bookDollars?: number;
  /** Defaults to an empty Current book. Advisors add tickers via + Add holding. */
  current?: PortfolioHoldingDraft[];
  /** Defaults to an empty Proposed book. Advisors add tickers via + Add holding. */
  proposed?: PortfolioHoldingDraft[];
  funds?: PortfolioFundOption[];
  taxRates?: Partial<TaxRates>;
  className?: string;
  /** Dedicated Portfolio tab / standalone demo use h1; nested mounts can use h2. */
  headingAs?: "h1" | "h2";
  /** Website wires Export + freemium. Omit to hide the button. */
  onExport?: (result: PortfolioCompareResponse, bookDollars: number) => void;
  exportLabel?: string;
};

function toApiHoldings(holdings: PortfolioHoldingDraft[]) {
  return holdings
    .filter((holding) => holding.ticker.trim() && holding.weightPct > 0)
    .map((holding) => {
      const ticker = holding.ticker.trim().toUpperCase();
      const nav = navFromFundMetadata(ticker, holding.nav);
      return {
        ticker,
        fund_identifier: ticker,
        fund_name: holding.fundName || undefined,
        fund_family: holding.family,
        weight_pct: holding.weightPct,
        ...(nav != null ? { nav_per_share: nav } : {}),
      };
    });
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
  headingAs: Heading = "h1",
  onExport,
  exportLabel = "Export",
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
  const [navNeeded, setNavNeeded] = useState(false);
  const [loading, setLoading] = useState(true);
  const { notice, onNotice, dismissNotice } = useNoticeToast();

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
  const currentFilled = currentApi.length > 0;
  const proposedFilled = proposedApi.length > 0;
  const canFetch = currentFilled || proposedFilled;
  const appliedTaxRates: TaxRates = {
    ...UI_DEFAULT_TAX_RATES,
    ...taxRates,
  };
  const requestKey = JSON.stringify({
    bookDollars,
    current: currentApi,
    proposed: proposedApi,
    taxRates: appliedTaxRates,
    periods: defaultPortfolioComparePeriods(),
    retry,
  });

  useEffect(() => {
    if (!canFetch) return;

    const payload = JSON.parse(requestKey) as {
      bookDollars: number;
      current: ReturnType<typeof toApiHoldings>;
      proposed: ReturnType<typeof toApiHoldings>;
      taxRates: Partial<TaxRates>;
      periods: ReturnType<typeof defaultPortfolioComparePeriods>;
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
          periods: payload.periods,
        },
        { signal: controller.signal },
      )
        .then((payloadResult) => {
          setResult(payloadResult);
          setError(null);
          setNavNeeded(false);
          setLoading(false);
        })
        .catch((caught: unknown) => {
          if (caught instanceof DOMException && caught.name === "AbortError") return;
          if (isMissingNavError(caught)) {
            setNavNeeded(true);
            setError(NEED_FUND_PRICE_COPY);
            setLoading(false);
            return;
          }
          setResult(null);
          setNavNeeded(false);
          setError(caught instanceof Error ? caught.message : "Portfolio compare failed");
          setLoading(false);
        });
    }, 250);

    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [canFetch, requestKey]);

  const navByTicker = Object.fromEntries(
    [...current, ...proposed]
      .filter((holding) => holding.ticker.trim() && holding.nav != null && holding.nav > 0)
      .map((holding) => [holding.ticker.trim().toUpperCase(), holding.nav]),
  );
  const currentUpcomingHoldings = result
    ? withUpcomingNav(upcomingHoldingsForSide(result.current, "current"), navByTicker)
    : [];
  const proposedUpcomingHoldings = result
    ? withUpcomingNav(upcomingHoldingsForSide(result.proposed, "proposed"), navByTicker)
    : [];
  const yearTax = result ? calendarYearTaxTable(result) : null;
  const uniqueNavPrompt = navNeeded
    ? [...current, ...proposed]
        .filter((holding) => holding.ticker.trim() && holding.weightPct > 0)
        .map((holding) => ({
          key: holding.id,
          ticker: holding.ticker.trim().toUpperCase(),
          nav: holding.nav ?? null,
        }))
        .filter(
          (holding, index, list) =>
            list.findIndex((item) => item.ticker === holding.ticker) === index,
        )
    : [];

  return (
    <article className={`portfolio-compare w-full ${className}`}>
      <header className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-faint">
            <span aria-hidden className="inline-block size-1.5 rounded-full bg-tax-less" />
            Aftertax · Portfolio
          </p>
          <Heading className="mt-1 font-serif text-3xl tracking-tight text-ink">
            Portfolio
          </Heading>
        </div>
        <div className="flex flex-wrap items-end gap-3">
          {onExport ? (
            <button
              type="button"
              disabled={!result}
              onClick={() => {
                if (!result) return;
                onExport(result, bookDollars);
              }}
              className="inline-flex h-11 items-center rounded-md border border-line px-4 text-sm text-ink hover:border-line-strong disabled:cursor-not-allowed disabled:opacity-50"
            >
              {exportLabel}
            </button>
          ) : null}
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
        </div>
      </header>

      {navNeeded && uniqueNavPrompt.length > 0 ? (
        <NeedFundPricePrompt
          className="mb-4"
          holdings={uniqueNavPrompt}
          onNavChange={(key, nav) => {
            const ticker = uniqueNavPrompt.find((item) => item.key === key)?.ticker;
            const apply = (rows: PortfolioHoldingDraft[]) =>
              rows.map((row) =>
                row.id === key ||
                (ticker != null && row.ticker.trim().toUpperCase() === ticker)
                  ? { ...row, nav }
                  : row,
              );
            setCurrent(apply);
            setProposed(apply);
          }}
        />
      ) : null}

      <div className="grid grid-cols-1 items-stretch gap-4 lg:grid-cols-2 lg:grid-rows-[auto_auto] lg:[grid-template-areas:'holdings-c_holdings-p'_'upcoming-c_upcoming-p']">
        <AllocationColumn
          title="Current allocation"
          holdings={current}
          bookDollars={bookDollars}
          unit={currentUnit}
          funds={funds}
          inputIdPrefix="current"
          onUnitChange={setCurrentUnit}
          onChange={setCurrent}
          onNotice={onNotice}
          className="h-full lg:[grid-area:holdings-c]"
        />
        {upcomingPanel({
          canFetch,
          sideFilled: currentFilled,
          loading,
          result,
          rows: currentUpcomingHoldings,
          headingId: "upcoming-current",
          sideLabel: "Current",
          gridAreaClass: "lg:[grid-area:upcoming-c]",
          loadingLabel: "Loading current upcoming distributions",
          taxRates: appliedTaxRates,
        })}

        <AllocationColumn
          title="Proposed allocation"
          holdings={proposed}
          bookDollars={bookDollars}
          unit={proposedUnit}
          funds={funds}
          inputIdPrefix="proposed"
          onUnitChange={setProposedUnit}
          onChange={setProposed}
          onNotice={onNotice}
          className="h-full lg:[grid-area:holdings-p]"
        />
        {upcomingPanel({
          canFetch,
          sideFilled: proposedFilled,
          loading,
          result,
          rows: proposedUpcomingHoldings,
          headingId: "upcoming-proposed",
          sideLabel: "Proposed",
          gridAreaClass: "lg:[grid-area:upcoming-p]",
          loadingLabel: "Loading proposed upcoming distributions",
          taxRates: appliedTaxRates,
        })}
      </div>

      <div className="mt-4">
        {!canFetch ? null : loading && !result ? (
          <div
            className="h-56 animate-pulse rounded-2xl border border-line bg-surface"
            aria-busy
            aria-label="Loading calendar-year tax"
          />
        ) : result && yearTax ? (
          <CalendarYearTaxTable model={yearTax} />
        ) : null}
      </div>

      <div className="mt-4">
        {!canFetch ? (
          <p className="rounded-2xl border border-dashed border-line-strong bg-surface px-5 py-4 text-sm text-muted">
            Add at least one weighted holding with + Add holding.
          </p>
        ) : loading && !result ? (
          <div
            className="h-[7.5rem] animate-pulse rounded-2xl border border-line bg-surface"
            aria-busy
            aria-label="Loading portfolio tax summary"
          />
        ) : navNeeded ? null : error ? (
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
        Weights × Portfolio Value → dollars. Missing or uncovered values stay
        N/A or Undisclosed.
      </p>
      <CompactDisclaimer className="mt-1 text-center text-[10px] leading-relaxed text-faint" />
      <NoticeToast message={notice} onDismiss={dismissNotice} />
    </article>
  );
}

function upcomingPanel({
  canFetch,
  sideFilled,
  loading,
  result,
  rows,
  headingId,
  sideLabel,
  gridAreaClass,
  loadingLabel,
  taxRates,
}: {
  canFetch: boolean;
  sideFilled: boolean;
  loading: boolean;
  result: PortfolioCompareResponse | null;
  rows: ReturnType<typeof upcomingHoldingsForSide>;
  headingId: string;
  sideLabel: "Current" | "Proposed";
  gridAreaClass: string;
  loadingLabel: string;
  taxRates: TaxRates;
}) {
  if (!canFetch) return null;
  if (!sideFilled) {
    return (
      <EmptyBookUpcoming
        headingId={headingId}
        sideLabel={sideLabel}
        className={`h-full ${gridAreaClass}`}
      />
    );
  }
  if (loading && !result) {
    return (
      <div
        className={`h-48 min-h-48 animate-pulse rounded-2xl border border-line bg-surface lg:h-full ${gridAreaClass}`}
        aria-busy
        aria-label={loadingLabel}
      />
    );
  }
  if (!result) return null;
  return (
    <UpcomingTable
      headingId={headingId}
      rows={rows}
      sideLabel={sideLabel}
      className={`h-full ${gridAreaClass}`}
      taxRates={taxRates}
      combineStateWithFederal
    />
  );
}

function EmptyBookUpcoming({
  headingId,
  sideLabel,
  className = "",
}: {
  headingId: string;
  sideLabel: "Current" | "Proposed";
  className?: string;
}) {
  return (
    <section
      aria-labelledby={headingId}
      className={`flex flex-col rounded-2xl border border-dashed border-line-strong bg-surface p-3 shadow-[0_8px_24px_rgba(26,29,26,0.06)] sm:p-4 ${className}`}
    >
      <h2 id={headingId} className="font-serif text-lg tracking-tight text-ink">
        {UPCOMING_MODULE_HEADING}
      </h2>
      <p className="mt-3 rounded-xl border border-dashed border-line bg-paper/40 px-3 py-5 text-center text-sm text-muted">
        {EMPTY_BOOK_INVITE}
      </p>
      <p className="mt-2 text-[10px] text-faint">{sideLabel}</p>
    </section>
  );
}
