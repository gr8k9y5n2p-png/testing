"use client";

import { useEffect, useMemo, useState } from "react";
import type { FundEstimateView } from "@/data/types";
import { CompareAnnualTable } from "@/components/illustrate/CompareAnnualTable";
import {
  GrowthAndTaxDragModule,
} from "@/components/illustrate/GrowthAndTaxDragModule";
import { TickerField } from "@/components/illustrate/portfolio-compare/TickerField";
import { UpcomingTable } from "@/components/illustrate/portfolio-compare/UpcomingTable";
import { postIllustrateCompare } from "@/lib/illustrate/compare-client";
import {
  trailingCalendarPeriods,
  yoyTaxDragCompareRequest,
} from "@/lib/illustrate/compare-request";
import type { CompareResponse } from "@/lib/illustrate/compare-types";
import {
  COMPARE_SLOT_COUNT,
  buildCompareAnnualTable,
  compareHistoryYears,
  filledCompareTickers,
  growthFundsFromSlots,
  padCompareSlots,
  setCompareSlot,
  upcomingRowsFromCompareTickers,
} from "@/lib/illustrate/compare-workspace";
import { resolveFundView } from "@/lib/illustrate/fund-history";
import { toUpcomingSummary } from "@/lib/illustrate/tax-drag-chart";
import type { PortfolioFundOption } from "@/lib/illustrate/portfolio-compare-types";
import { DEFAULT_START_DOLLARS } from "@/lib/performance/types";

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
  const [loaded, setLoaded] = useState<LoadedTicker[]>([]);
  const [historyError, setHistoryError] = useState<string | null>(null);

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
              holdingDollars: DEFAULT_START_DOLLARS,
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
        setLoaded(rows);
        setHistoryError(
          rows.every((row) => row.tax == null)
            ? "Calendar-year history is unavailable for these tickers."
            : null,
        );
      })
      .catch((caught: unknown) => {
        if (caught instanceof DOMException && caught.name === "AbortError") return;
        setLoaded(tickers.map((ticker) => ({
          ticker,
          fund: resolveFundView(funds, ticker) ?? null,
          tax: null,
        })));
        setHistoryError(
          caught instanceof Error ? caught.message : "Calendar-year history failed",
        );
      });

    return () => controller.abort();
  }, [filledKey, funds]);

  const activeLoaded = useMemo(
    () => (filledKey ? loaded : []),
    [filledKey, loaded],
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

  return (
    <section id="fund-compare" aria-label="Fund comparison" className="w-full">
      <header className="mb-6">
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
          Upcoming is never filled from paid history.
        </p>
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
          startDollars={DEFAULT_START_DOLLARS}
        />
      </section>

      <div className="mt-10 w-full">
        {activeHistoryError ? (
          <p className="mb-3 text-sm text-tax-more">{activeHistoryError}</p>
        ) : null}
        <CompareAnnualTable
          model={annualModel}
          loading={Boolean(filledKey) && loaded.length === 0}
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
