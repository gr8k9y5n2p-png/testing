"use client";

import { useEffect, useMemo, useState } from "react";
import type { FundEstimateView } from "@/data/types";
import { CompareAnnualTable } from "@/components/illustrate/CompareAnnualTable";
import { CompareDeltaStrip } from "@/components/illustrate/CompareDeltaStrip";
import {
  GrowthAndTaxDragModule,
} from "@/components/illustrate/GrowthAndTaxDragModule";
import { TickerField } from "@/components/illustrate/portfolio-compare/TickerField";
import { UpcomingTable } from "@/components/illustrate/portfolio-compare/UpcomingTable";
import { postIllustrateCompare } from "@/lib/illustrate/compare-client";
import { toTaxDeltaCardModel } from "@/lib/illustrate/compare-map";
import {
  compareSideFromFund,
  trailingCalendarPeriods,
  yoyTaxDragCompareRequest,
} from "@/lib/illustrate/compare-request";
import type { CompareResponse } from "@/lib/illustrate/compare-types";
import {
  deltaStripFromPairMetrics,
  deltaStripFromSingleUpcoming,
  reservedDeltaStrip,
} from "@/lib/illustrate/compare-delta-strip";
import {
  COMPARE_DEFAULT_HOLDING_DOLLARS,
  COMPARE_SLOT_COUNT,
  buildCompareAnnualTable,
  compareHistoryYears,
  filledCompareTickers,
  growthFundsFromSlots,
  padCompareSlots,
  parseCompareHoldingDollars,
  setCompareSlot,
  upcomingRowsFromCompareTickers,
} from "@/lib/illustrate/compare-workspace";
import { resolveFundView } from "@/lib/illustrate/fund-history";
import { toUpcomingSummary } from "@/lib/illustrate/tax-drag-chart";
import type { PortfolioFundOption } from "@/lib/illustrate/portfolio-compare-types";

type LoadedTicker = {
  ticker: string;
  fund: FundEstimateView | null;
  tax: CompareResponse | null;
};

export function CompareWorkspace({
  funds,
  initialTickers = [],
  headingAs: Heading = "h1",
}: {
  funds: FundEstimateView[];
  initialTickers?: Array<string | undefined | null>;
  headingAs?: "h1" | "h2";
}) {
  const [slots, setSlots] = useState(() => padCompareSlots(initialTickers));
  const [holdingDollars, setHoldingDollars] = useState(COMPARE_DEFAULT_HOLDING_DOLLARS);
  const [holdingDraft, setHoldingDraft] = useState(() =>
    formatHoldingInput(COMPARE_DEFAULT_HOLDING_DOLLARS),
  );
  const catalog = useMemo<PortfolioFundOption[]>(
    () =>
      funds.map((fund) => ({
        ticker: fund.ticker,
        fundName: fund.fundName,
        family: fund.family,
        nav: fund.nav > 0 ? fund.nav : null,
      })),
    [funds],
  );
  const growthFunds = useMemo(
    () => growthFundsFromSlots(slots, funds),
    [slots, funds],
  );
  const filledKey = filledCompareTickers(slots).join(",");
  const [loaded, setLoaded] = useState<{
    holdingDollars: number;
    rows: LoadedTicker[];
  }>({ holdingDollars: COMPARE_DEFAULT_HOLDING_DOLLARS, rows: [] });
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [pairMetrics, setPairMetrics] = useState<{
    holdingDollars: number;
    metrics: ReturnType<typeof toTaxDeltaCardModel>["metrics"];
  } | null>(null);

  useEffect(() => {
    const tickers = filledKey ? filledKey.split(",") : [];
    if (tickers.length === 0) {
      return;
    }

    const controller = new AbortController();
    const periods = trailingCalendarPeriods();

    void Promise.all(
      tickers.map(async (ticker) => {
        const fund = resolveFundView(funds, ticker) ?? null;
        try {
          const tax = await postIllustrateCompare(
            yoyTaxDragCompareRequest({
              ticker,
              label: ticker,
              fundIdentifier: fund?.ticker ?? ticker,
              fundFamily: fund?.family,
              fundName: fund?.fundName,
              holdingDollars,
              navPerShare: fund && fund.nav > 0 ? fund.nav : undefined,
              periods,
            }),
            { signal: controller.signal },
          );
          return { ticker, fund, tax };
        } catch (caught) {
          if (caught instanceof DOMException && caught.name === "AbortError") {
            throw caught;
          }
          return { ticker, fund, tax: null };
        }
      }),
    )
      .then((rows) => {
        setLoaded({ holdingDollars, rows });
        setHistoryError(
          rows.every((row) => row.tax == null)
            ? "Calendar-year history is unavailable for these tickers."
            : null,
        );
      })
      .catch((caught: unknown) => {
        if (caught instanceof DOMException && caught.name === "AbortError") return;
        setLoaded({
          holdingDollars,
          rows: tickers.map((ticker) => ({
            ticker,
            fund: resolveFundView(funds, ticker) ?? null,
            tax: null,
          })),
        });
        setHistoryError(
          caught instanceof Error ? caught.message : "Calendar-year history failed",
        );
      });

    return () => controller.abort();
  }, [filledKey, funds, holdingDollars]);

  useEffect(() => {
    const tickers = filledKey ? filledKey.split(",") : [];
    if (tickers.length < 2) {
      return;
    }
    const [leftTicker, rightTicker] = tickers;
    const leftFund = resolveFundView(funds, leftTicker);
    const rightFund = resolveFundView(funds, rightTicker);
    const controller = new AbortController();
    void postIllustrateCompare(
      {
        mode: "fund_vs_fund",
        holding_dollars: holdingDollars,
        combine_state_with_federal: true,
        latest_as_of_only: true,
        left: compareSideFromFund({
          ticker: leftTicker,
          fundName: leftFund?.fundName,
          family: leftFund?.family,
          nav: leftFund?.nav,
          fundIdentifier: leftFund?.ticker ?? leftTicker,
        }),
        right: compareSideFromFund({
          ticker: rightTicker,
          fundName: rightFund?.fundName,
          family: rightFund?.family,
          nav: rightFund?.nav,
          fundIdentifier: rightFund?.ticker ?? rightTicker,
        }),
        periods: trailingCalendarPeriods(),
        tax_rates: {},
      },
      { signal: controller.signal },
    )
      .then((payload) => {
        setPairMetrics({
          holdingDollars,
          metrics: toTaxDeltaCardModel(payload, undefined, { holdingDollars }).metrics,
        });
      })
      .catch((caught: unknown) => {
        if (caught instanceof DOMException && caught.name === "AbortError") return;
        setPairMetrics(null);
      });
    return () => controller.abort();
  }, [filledKey, funds, holdingDollars]);

  const historyMatchesHolding = loaded.holdingDollars === holdingDollars;
  const activeLoaded = useMemo(
    () => (filledKey && historyMatchesHolding ? loaded.rows : []),
    [filledKey, historyMatchesHolding, loaded.rows],
  );
  const annualModel = useMemo(
    () => buildCompareAnnualTable(activeLoaded, compareHistoryYears()),
    [activeLoaded],
  );
  const upcomingRows = useMemo(
    () =>
      upcomingRowsFromCompareTickers(
        activeLoaded.map((item) => ({
          ticker: item.ticker,
          fund: item.fund,
          upcoming: item.tax
            ? toUpcomingSummary(item.tax.summary.upcoming_taxable_distribution, "left")
            : null,
        })),
      ),
    [activeLoaded],
  );
  const activeHistoryError = filledKey ? historyError : null;
  const pairReady = filledKey.split(",").filter(Boolean).length >= 2;
  const stripItems = useMemo(() => {
    if (pairReady && pairMetrics && pairMetrics.holdingDollars === holdingDollars) {
      return deltaStripFromPairMetrics(pairMetrics.metrics, holdingDollars);
    }
    if (activeLoaded.length === 1) {
      return deltaStripFromSingleUpcoming(
        activeLoaded[0]?.tax
          ? toUpcomingSummary(
              activeLoaded[0].tax.summary.upcoming_taxable_distribution,
              "left",
            )
          : null,
        holdingDollars,
      );
    }
    return reservedDeltaStrip(holdingDollars);
  }, [activeLoaded, holdingDollars, pairMetrics, pairReady]);

  function commitHolding(raw: string) {
    const next = parseCompareHoldingDollars(raw, holdingDollars);
    setHoldingDollars(next);
    setHoldingDraft(formatHoldingInput(next));
  }

  return (
    <section id="fund-compare" aria-label="Fund comparison" className="w-full">
      <header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="min-w-0">
          <p className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-faint">
            <span aria-hidden className="inline-block size-1.5 rounded-full bg-tax-less" />
            Aftertax · Compare
          </p>
          <Heading className="mt-1 font-serif text-3xl tracking-tight text-ink">
            Compare funds
          </Heading>
          <p className="mt-2 max-w-2xl text-sm text-muted">
            Start with one ticker — growth, calendar-year history, and upcoming all
            populate for that fund. Each additional filled slot (up to{" "}
            {COMPARE_SLOT_COUNT}) joins every module. Empty slots are ignored.
            Dollars invested is shared — one holding for growth, tax $, history,
            delta, and upcoming. Upcoming is never filled from paid history.
          </p>
        </div>
        <label className="block shrink-0">
          <span className="mb-1.5 block text-[10px] font-semibold uppercase tracking-[0.14em] text-faint">
            Dollars invested
          </span>
          <div className="relative w-[12.5rem]">
            <span
              aria-hidden
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-faint"
            >
              $
            </span>
            <input
              inputMode="decimal"
              value={holdingDraft}
              onChange={(event) => setHoldingDraft(event.target.value)}
              onBlur={(event) => commitHolding(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  event.currentTarget.blur();
                }
              }}
              className="h-11 w-full rounded-md border border-line bg-surface pl-7 pr-3 font-mono text-base text-ink shadow-[0_1px_2px_rgba(26,29,26,0.04)]"
              aria-label="Dollars invested"
            />
          </div>
          <span className="mt-1 block max-w-[12.5rem] text-[10px] leading-snug text-muted">
            Shared starting holding · default $10,000
          </span>
        </label>
      </header>

      <div className="grid w-full grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {slots.map((ticker, index) => {
          const selected = ticker ? resolveFundView(funds, ticker) : null;
          return (
            <label key={`compare-slot-${index}`} className="block min-w-0">
              <span className="mb-1.5 block text-[10px] font-semibold uppercase tracking-[0.14em] text-faint">
                Ticker {index + 1}
              </span>
              <TickerField
                ticker={ticker}
                fundName={selected?.fundName || ""}
                funds={catalog}
                inputId={`compare-slot-${index}`}
                allowEmpty
                onSelect={(fund) => {
                  setSlots((current) => setCompareSlot(current, index, fund.ticker));
                }}
              />
            </label>
          );
        })}
      </div>

      <div className="mt-8 w-full">
        <CompareDeltaStrip items={stripItems} />
      </div>

      <section
        id="growth-and-tax"
        aria-label="Growth of dollars and tax drag"
        className="mt-10 w-full scroll-mt-20"
      >
        <GrowthAndTaxDragModule
          key={filledKey || "empty"}
          funds={growthFunds}
          seedFunds={growthFunds}
          lockToSeed
          allowAddFund={false}
          editablePrincipal={false}
          startDollars={holdingDollars}
        />
      </section>

      <div className="mt-10 w-full">
        {activeHistoryError ? (
          <p className="mb-3 text-sm text-tax-more">{activeHistoryError}</p>
        ) : null}
        <CompareAnnualTable
          model={annualModel}
          loading={Boolean(filledKey) && (!historyMatchesHolding || loaded.rows.length === 0)}
        />
      </div>

      <div className="mt-10 w-full">
        <UpcomingTable
          rows={upcomingRows}
          headingId="compare-upcoming"
        />
      </div>
    </section>
  );
}

function formatHoldingInput(value: number): string {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);
}
