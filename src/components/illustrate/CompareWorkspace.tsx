"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { FundEstimateView } from "@/data/types";
import {
  GrowthAndTaxDragModule,
} from "@/components/illustrate/GrowthAndTaxDragModule";
import { TickerField } from "@/components/illustrate/portfolio-compare/TickerField";
import { NeedFundPricePrompt } from "@/components/illustrate/NeedFundPricePrompt";
import { TaxRateFields } from "@/components/illustrate/TaxRateFields";
import { UpcomingTable } from "@/components/illustrate/portfolio-compare/UpcomingTable";
import { NoticeToast, useNoticeToast } from "@/components/NoticeToast";
import { SavedAssetActions } from "@/components/saved-assets/SavedAssetActions";
import { fetchFundsSearch } from "@/lib/data-api/funds-client";
import { postIllustrateCompare } from "@/lib/illustrate/compare-client";
import {
  trailingCalendarPeriods,
  yoyTaxDragCompareRequest,
} from "@/lib/illustrate/compare-request";
import {
  COMPARE_DEFAULT_COMBINE_STATE,
  COMPARE_DEFAULT_HOLDING_DOLLARS,
  COMPARE_DEFAULT_TAX_RATES,
  COMPARE_FETCH_DEBOUNCE_MS,
  COMPARE_SLOT_COUNT,
  compareInputsMatch,
  compareSlotPlaceholder,
  filledCompareTickers,
  keepFreshCompareRows,
  mergeCompareFundViews,
  mergeCompareLoadedRows,
  padCompareSlots,
  parseCompareHoldingDollars,
  pickFundViewFromSearch,
  setCompareSlot,
  upcomingRowsFromCompareTickers,
  type CompareGrowthFund,
  type CompareLoadedTicker,
} from "@/lib/illustrate/compare-workspace";
import {
  compareWorkspaceIsSavable,
  compareWorkspaceToPortfolioBooks,
  portfolioBooksToCompareWorkspace,
} from "@/lib/illustrate/portfolio-save-open";
import { toPortfolioAssetPayload } from "@/lib/saved-assets/payloads";
import { resolveFundView } from "@/lib/illustrate/fund-history";
import { isMissingNavError } from "@/lib/illustrate/illustrate-error";
import { toUpcomingSummary } from "@/lib/illustrate/tax-drag-chart";
import type { TaxRates } from "@/lib/illustrate/types";
import type { PortfolioFundOption } from "@/lib/illustrate/portfolio-compare-types";

export function CompareWorkspace({
  funds = [],
  initialTickers = [],
  headingAs: Heading = "h1",
}: {
  funds?: FundEstimateView[];
  initialTickers?: Array<string | undefined | null>;
  headingAs?: "h1" | "h2";
}) {
  const [slots, setSlots] = useState(() => padCompareSlots(initialTickers));
  const { notice, onNotice, dismissNotice } = useNoticeToast();
  const [holdingDollars, setHoldingDollars] = useState(COMPARE_DEFAULT_HOLDING_DOLLARS);
  const [holdingDraft, setHoldingDraft] = useState(() =>
    formatHoldingInput(COMPARE_DEFAULT_HOLDING_DOLLARS),
  );
  const [taxRates, setTaxRates] = useState<TaxRates>(COMPARE_DEFAULT_TAX_RATES);
  const [combineState, setCombineState] = useState(COMPARE_DEFAULT_COMBINE_STATE);
  const [knownFunds, setKnownFunds] = useState<FundEstimateView[]>(funds);
  const [confirmHints, setConfirmHints] = useState<
    Record<string, CompareGrowthFund>
  >({});
  const catalog = useMemo<PortfolioFundOption[]>(
    () =>
      knownFunds.map((fund) => ({
        ticker: fund.ticker,
        fundName: fund.fundName,
        family: fund.family,
        nav: fund.nav > 0 ? fund.nav : null,
      })),
    [knownFunds],
  );
  const filledTickers = filledCompareTickers(slots);
  const filledKey = filledTickers.join(",");
  // Ticker + confirm-time hint only. Later hydrate must not change Growth keys.
  const growthFunds = useMemo(
    () =>
      filledTickers.map((ticker) => {
        const hint = confirmHints[ticker];
        return {
          ticker,
          label: ticker,
          fundIdentifier: hint?.fundIdentifier ?? ticker,
          fundFamily: hint?.fundFamily,
          fundName: hint?.fundName,
          navPerShare: hint?.navPerShare,
        };
      }),
    [confirmHints, filledTickers],
  );
  const fundsRef = useRef(knownFunds);
  fundsRef.current = knownFunds;
  const [loaded, setLoaded] = useState<{
    holdingDollars: number;
    taxRates: TaxRates;
    combine: boolean;
    rows: CompareLoadedTicker[];
  }>({
    holdingDollars: COMPARE_DEFAULT_HOLDING_DOLLARS,
    taxRates: COMPARE_DEFAULT_TAX_RATES,
    combine: COMPARE_DEFAULT_COMBINE_STATE,
    rows: [],
  });
  const [navOverrides, setNavOverrides] = useState<Record<string, number>>({});
  const [navNeededTickers, setNavNeededTickers] = useState<string[]>([]);

  useEffect(() => {
    const tickers = filledKey ? filledKey.split(",") : [];
    if (tickers.length === 0) {
      setLoaded((current) => ({
        holdingDollars,
        taxRates,
        combine: combineState,
        rows: keepFreshCompareRows(current.rows, []),
      }));
      setNavNeededTickers([]);
      return;
    }

    // Keep already-confirmed tickers on screen while a new slot loads.
    setLoaded((current) => ({
      holdingDollars,
      taxRates,
      combine: combineState,
      rows: compareInputsMatch(current, holdingDollars, taxRates, combineState)
        ? keepFreshCompareRows(current.rows, tickers)
        : [],
    }));

    const controller = new AbortController();
    const periods = trailingCalendarPeriods();
    const timer = window.setTimeout(() => {
      void Promise.all(
        tickers.map(async (ticker) => {
          const fund = resolveFundView(fundsRef.current, ticker) ?? null;
          let row: CompareLoadedTicker;
          try {
            const tax = await postIllustrateCompare(
              yoyTaxDragCompareRequest({
                ticker,
                label: ticker,
                fundIdentifier: fund?.ticker ?? ticker,
                fundFamily: fund?.family,
                fundName: fund?.fundName,
                holdingDollars,
                navPerShare:
                  navOverrides[ticker] ??
                  (fund && fund.nav > 0 ? fund.nav : undefined),
                periods,
                taxRates,
                combineStateWithFederal: combineState,
              }),
              { signal: controller.signal },
            );
            row = { ticker, fund, tax, needsNav: false };
          } catch (caught) {
            if (caught instanceof DOMException && caught.name === "AbortError") {
              return;
            }
            row = {
              ticker,
              fund,
              tax: null,
              needsNav: isMissingNavError(caught),
            };
          }
          if (controller.signal.aborted) return;
          setLoaded((current) => ({
            holdingDollars,
            taxRates,
            combine: combineState,
            rows: mergeCompareLoadedRows(current.rows, row, tickers),
          }));
          setNavNeededTickers((current) => {
            if (row.needsNav) {
              return current.includes(ticker) ? current : [...current, ticker];
            }
            return current.filter((item) => item !== ticker);
          });
        }),
      ).catch((caught: unknown) => {
        if (caught instanceof DOMException && caught.name === "AbortError") return;
      });
    }, COMPARE_FETCH_DEBOUNCE_MS);

    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [filledKey, holdingDollars, navOverrides, taxRates, combineState]);

  useEffect(() => {
    const tickers = filledKey ? filledKey.split(",") : [];
    if (tickers.length === 0) return;
    let cancelled = false;
    void Promise.all(
      tickers.map(async (ticker) => {
        if (resolveFundView(fundsRef.current, ticker)) return;
        const page = await fetchFundsSearch<FundEstimateView>(ticker, 5, {
          navOnly: false,
        });
        if (cancelled) return;
        const fund = pickFundViewFromSearch(page.items, ticker);
        if (!fund) return;
        setKnownFunds((current) => mergeCompareFundViews(current, fund, tickers));
      }),
    );
    return () => {
      cancelled = true;
    };
  }, [filledKey]);

  const historyMatchesInputs = compareInputsMatch(
    loaded,
    holdingDollars,
    taxRates,
    combineState,
  );
  const activeLoaded = useMemo(
    () => (filledKey && historyMatchesInputs ? loaded.rows : []),
    [filledKey, historyMatchesInputs, loaded.rows],
  );
  const upcomingRows = useMemo(
    () =>
      upcomingRowsFromCompareTickers(
        filledTickers.map((ticker, index) => {
          const loadedRow = activeLoaded.find((item) => item.ticker === ticker);
          const fund =
            resolveFundView(knownFunds, ticker) ?? loadedRow?.fund ?? null;
          return {
            ticker,
            fund,
            holdingDollars,
            navPerShare:
              navOverrides[ticker] ??
              (fund && fund.nav > 0 ? fund.nav : null),
            upcoming: loadedRow?.tax
              ? toUpcomingSummary(
                  loadedRow.tax.summary.upcoming_taxable_distribution,
                  "left",
                )
              : null,
            index,
          };
        }),
      ),
    [activeLoaded, filledTickers, knownFunds, holdingDollars, navOverrides],
  );
  const prefetchTax = useMemo(
    () =>
      historyMatchesInputs
        ? loaded.rows.map((row) => ({
            ticker: row.ticker,
            tax: row.tax,
            taxSide: "auto" as const,
          }))
        : undefined,
    [historyMatchesInputs, loaded.rows],
  );

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
            Start with one ticker — growth, tax drag, and upcoming all
            populate for that fund. Each additional filled slot (up to{" "}
            {COMPARE_SLOT_COUNT}) joins every module. Empty slots are ignored.
            Dollars invested and tax rates are shared — Tax $ and tax-drag
            recompute from the same holding and rates. Upcoming is never filled
            from paid history.
          </p>
        </div>
        <div className="flex shrink-0 flex-col items-stretch gap-3 sm:items-end">
          <SavedAssetActions
            type="portfolio"
            canSave={() => compareWorkspaceIsSavable(slots)}
            getPayload={() =>
              toPortfolioAssetPayload(
                compareWorkspaceToPortfolioBooks(
                  { tickers: slots, holdingDollars },
                  catalog,
                ),
              )
            }
            onOpen={(asset) => {
              const next = portfolioBooksToCompareWorkspace(
                asset.payload,
                holdingDollars,
              );
              if (next.tickers.length === 0) return;
              setSlots(padCompareSlots(next.tickers));
              if (next.holdingDollars > 0) {
                setHoldingDollars(next.holdingDollars);
                setHoldingDraft(formatHoldingInput(next.holdingDollars));
              }
            }}
            onNotice={onNotice}
          />
          <label className="block">
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
        </div>
      </header>

      <div className="grid w-full grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {slots.map((ticker, index) => {
          const selected = ticker ? resolveFundView(knownFunds, ticker) : null;
          return (
            <div key={`compare-slot-${index}`} className="min-w-0">
              <TickerField
                ticker={ticker}
                fundName={selected?.fundName || ""}
                funds={catalog}
                inputId={`compare-slot-${index}`}
                placeholder={compareSlotPlaceholder(index)}
                hideSubtitle
                allowEmpty
                onNotice={onNotice}
                onSelect={(fund) => {
                  const nextTicker = fund.ticker.trim().toUpperCase();
                  if (nextTicker) {
                    setConfirmHints((current) => ({
                      ...current,
                      [nextTicker]: {
                        ticker: nextTicker,
                        label: nextTicker,
                        fundIdentifier: nextTicker,
                        fundFamily: fund.family,
                        fundName: fund.fundName || undefined,
                        navPerShare:
                          fund.nav != null && fund.nav > 0 ? fund.nav : undefined,
                      },
                    }));
                  }
                  setSlots((current) => setCompareSlot(current, index, fund.ticker));
                }}
              />
            </div>
          );
        })}
      </div>

      <div className="mt-4 rounded-xl border border-line bg-paper/50 px-3 py-3 sm:px-4">
        <TaxRateFields
          compact
          rates={taxRates}
          combine={combineState}
          onRatesChange={setTaxRates}
          onCombineChange={setCombineState}
        />
      </div>

      <section
        id="growth-and-tax"
        aria-label="Growth of dollars and tax drag"
        className="mt-10 w-full scroll-mt-20"
      >
        <GrowthAndTaxDragModule
          funds={growthFunds}
          seedFunds={growthFunds}
          lockToSeed
          allowAddFund={false}
          editablePrincipal={false}
          startDollars={holdingDollars}
          taxRates={taxRates}
          combineStateWithFederal={combineState}
          prefetchTax={prefetchTax}
        />
      </section>

      <div className="mt-10 w-full">
        {navNeededTickers.length > 0 ? (
          <NeedFundPricePrompt
            className="mb-4"
            holdings={navNeededTickers.map((ticker) => ({
              key: ticker,
              ticker,
              nav: navOverrides[ticker] ?? resolveFundView(knownFunds, ticker)?.nav ?? null,
            }))}
            onNavChange={(key, nav) => {
              if (nav == null) return;
              setNavOverrides((current) => ({ ...current, [key]: nav }));
              setNavNeededTickers((current) =>
                current.filter((ticker) => ticker !== key),
              );
            }}
          />
        ) : null}
        <UpcomingTable
          rows={upcomingRows}
          headingId="compare-upcoming"
          taxRates={taxRates}
          combineStateWithFederal={combineState}
        />
      </div>
      <NoticeToast message={notice} onDismiss={dismissNotice} />
    </section>
  );
}

function formatHoldingInput(value: number): string {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);
}
