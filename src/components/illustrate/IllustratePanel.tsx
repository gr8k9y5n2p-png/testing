"use client";

import { useEffect, useMemo, useState } from "react";
import type { FundEstimateView } from "@/data/types";
import { useCoverage } from "@/components/coverage/CoverageProvider";
import { isMissingNavError, isMockIllustrate, postIllustrate } from "@/lib/illustrate/client";
import {
  illustrationRequestNav,
  navFromFundMetadata,
  perShareNavError,
} from "@/lib/illustrate/compare-request";
import { formatWeeklyNavLabel } from "@/lib/illustrate/nav-math";
import { seedNavLookup } from "@/lib/illustrate/seed-nav";
import { distributionIdsForFund } from "@/lib/illustrate/ids";
import {
  postIllustratePortfolio,
  type PortfolioIllustrateResponse,
} from "@/lib/illustrate/portfolio";
import {
  AMOUNT_UNITS,
  DEFAULT_HOLDING_DOLLARS,
  UI_DEFAULT_TAX_RATES,
  emptyIllustrateResponse,
  type AmountUnit,
  type IllustrateRequest,
  type IllustrateResponse,
  type TaxRates,
} from "@/lib/illustrate/types";
import { DistributionDateStrip } from "@/components/DistributionDateStrip";
import { IllustrationResults } from "@/components/illustrate/IllustrationResults";
import { PortfolioCoverageCard } from "@/components/illustrate/PortfolioCoverageCard";
import { TaxRateFields } from "@/components/illustrate/TaxRateFields";

export function IllustratePanel({
  selected,
}: {
  selected: FundEstimateView | null;
}) {
  const coverage = useCoverage();
  const live = selected ? coverage.isLive(selected.family) : true;
  const meta = selected ? coverage.familyMeta(selected.family) : undefined;

  return (
    <section
      id="illustrate"
      aria-labelledby="illustrate-heading"
      className="scroll-mt-6 rounded-lg border border-line bg-surface p-4 shadow-[0_1px_2px_rgba(26,29,26,0.04)] sm:p-6"
    >
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">
            Tax impact
          </p>
          <h2
            id="illustrate-heading"
            className="mt-1 font-serif text-xl tracking-tight text-ink"
          >
            Dollar illustration
          </h2>
          <p className="mt-1 max-w-2xl text-sm text-muted">
            Instant estimated distribution and tax in dollars. Adjust holding
            size and rates; Aftertax posts them to illustrate and returns the
            dollar result.
          </p>
        </div>
        {selected && !live ? (
          <p className="max-w-xs rounded-md border border-line bg-notice px-3 py-2 text-xs text-ink">
            Coverage gap: {selected.family}
            {meta?.aum_rank ? ` · AUM rank ${meta.aum_rank}` : ""} is not in live
            ingest yet. Result can understate tax impact.
          </p>
        ) : null}
        {selected && live && meta ? (
          <p className="max-w-xs rounded-md border border-above/20 bg-above-soft px-3 py-2 text-xs text-above">
            Live coverage: {meta.display_name}
            {meta.aum_rank ? ` · AUM rank ${meta.aum_rank}` : ""}
            {meta.priority ? ` · priority ${meta.priority}` : ""}
          </p>
        ) : null}
      </div>

      {selected ? (
        <div className="mb-5 rounded-md border border-line bg-paper px-4 py-3">
          <p className="text-sm font-medium text-ink">
            {selected.ticker} · {selected.fundName}
          </p>
          <DistributionDateStrip
            fund={selected}
            showPayable
            showStage
            className="mt-1.5"
          />
          <p className="mt-1.5 font-mono text-[11px] text-faint">
            Weekly NAV {formatWeeklyNavLabel(selected)}
          </p>
        </div>
      ) : null}

      {selected ? (
        <IllustrationWorkspace key={selected.id} fund={selected} />
      ) : (
        <div className="flex min-h-[12rem] items-center justify-center rounded-md border border-dashed border-line-strong px-6 text-center text-sm text-muted">
          Search a fund above to see taxable impact in dollars.
        </div>
      )}
    </section>
  );
}

function IllustrationWorkspace({ fund }: { fund: FundEstimateView }) {
  const [holding, setHolding] = useState(DEFAULT_HOLDING_DOLLARS);
  const [holdingInput, setHoldingInput] = useState(
    DEFAULT_HOLDING_DOLLARS.toLocaleString("en-US"),
  );
  const [rates, setRates] = useState<TaxRates>(UI_DEFAULT_TAX_RATES);
  const [combine, setCombine] = useState(true);
  const mock = isMockIllustrate();
  const navLookup = mock ? seedNavLookup : undefined;
  const metadataNav = navFromFundMetadata(fund.ticker, fund.nav, navLookup);
  const [unit, setUnit] = useState<AmountUnit>(AMOUNT_UNITS.percent_of_nav);
  const [navInput, setNavInput] = useState(
    metadataNav != null ? String(metadataNav) : fund.nav > 0 ? String(fund.nav) : "",
  );
  const [result, setResult] = useState<IllustrateResponse | null>(null);
  const [portfolio, setPortfolio] = useState<PortfolioIllustrateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const distributionIds = useMemo(
    () => distributionIdsForFund(fund.id, unit),
    [fund.id, unit],
  );

  const needsNav = unit === AMOUNT_UNITS.per_share;
  const requestNav = illustrationRequestNav(
    navInput,
    fund.ticker,
    fund.nav,
    navLookup,
  );
  const navError = perShareNavError(unit, requestNav);
  const useIds = mock && !fund.id.startsWith("api:");
  const canFetch = !navError && (useIds ? distributionIds.length > 0 : Boolean(fund.ticker));

  useEffect(() => {
    if (!canFetch) return;

    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      const request: IllustrateRequest = {
        holding_dollars: holding,
        ...(useIds
          ? { distribution_ids: distributionIds }
          : {
              selector: {
                fund_family: fund.family,
                fund_identifier: fund.ticker,
                ticker: fund.ticker,
              },
            }),
        ...(requestNav != null ? { nav_per_share: requestNav } : {}),
        tax_rates: rates,
        combine_state_with_federal: combine,
      };
      setLoading(true);
      postIllustrate(request, { signal: controller.signal })
        .then((payload) => {
          setResult(payload);
          setError(null);
          setLoading(false);
        })
        .catch((caught: unknown) => {
          if (caught instanceof DOMException && caught.name === "AbortError") return;
          if (isMissingNavError(caught)) {
            setUnit(AMOUNT_UNITS.per_share);
            setResult(null);
            setError(null);
            setLoading(false);
            return;
          }
          // Live miss: soft empty Upcoming (undisclosed). Never invent seed
          // math, paid history, or a MOCK banner.
          setResult(emptyIllustrateResponse(rates));
          setError(null);
          setLoading(false);
        });

      void postIllustratePortfolio(
        {
          holdings: [
            {
              holding_dollars: holding,
              ticker: fund.ticker,
              fund_family: fund.family,
              fund_identifier: fund.ticker,
              ...(mock ? { fund_name: fund.fundName } : {}),
              ...(requestNav != null ? { nav_per_share: requestNav } : {}),
            },
          ],
          tax_rates: rates,
          combine_state_with_federal: combine,
        },
        { signal: controller.signal },
      )
        .then(setPortfolio)
        .catch(() => setPortfolio(null));
    }, 250);

    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [canFetch, useIds, distributionIds, holding, rates, combine, requestNav, fund.family, fund.ticker, fund.fundName]);

  function commitHolding(raw: string) {
    const parsed = Number(raw.replace(/,/g, ""));
    if (parsed > 0) {
      setHolding(parsed);
      setHoldingInput(parsed.toLocaleString("en-US"));
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-12">
      <div className="space-y-4 lg:col-span-5">
        <label className="block">
          <span className="mb-1.5 block text-[11px] font-semibold uppercase tracking-[0.12em] text-faint">
            Holding
          </span>
          <div className="relative">
            <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-faint">
              $
            </span>
            <input
              inputMode="decimal"
              value={holdingInput}
              onChange={(event) => setHoldingInput(event.target.value)}
              onBlur={(event) => commitHolding(event.target.value)}
              className="h-12 w-full rounded-md border border-line bg-paper pl-7 pr-3 font-mono text-base text-ink"
            />
          </div>
        </label>
        <div className="flex flex-wrap gap-2">
          <UnitToggle
            active={unit === AMOUNT_UNITS.percent_of_nav}
            onClick={() => setUnit(AMOUNT_UNITS.percent_of_nav)}
            label="% of NAV"
          />
          <UnitToggle
            active={unit === AMOUNT_UNITS.per_share}
            onClick={() => setUnit(AMOUNT_UNITS.per_share)}
            label="$ / share"
          />
        </div>
        {needsNav ? (
          <label className="block">
            <span className="mb-1.5 block text-[11px] font-semibold uppercase tracking-[0.12em] text-faint">
              NAV per share
            </span>
            <input
              type="number"
              min={0.01}
              step={0.01}
              value={navInput}
              onChange={(event) => setNavInput(event.target.value)}
              className="h-10 w-full rounded-md border border-line bg-paper px-3 font-mono text-sm"
            />
            <span className="mt-1 block text-[11px] text-faint">
              Required for per_share amounts. Share count = holding ÷ NAV.
            </span>
          </label>
        ) : (
          <p className="text-xs text-faint">
            {metadataNav != null
              ? `% of NAV uses weekly NAV (${formatWeeklyNavLabel(fund)}) so Dist $ = est $/share × (holding ÷ NAV).`
              : "% of NAV sends holding dollars. Missing weekly NAV stays undisclosed — never invented. Switch to $ / share to enter a price."}
          </p>
        )}
        <TaxRateFields
          rates={rates}
          combine={combine}
          onRatesChange={setRates}
          onCombineChange={setCombine}
        />
      </div>
      <div className="lg:col-span-7">
        {navError ? (
          <p className="rounded-md border border-below/20 bg-below-soft px-4 py-3 text-sm text-below">
            {navError}
          </p>
        ) : loading && !result ? (
          <div className="h-64 animate-pulse rounded-md bg-paper" />
        ) : error ? (
          <p className="rounded-md border border-below/20 bg-below-soft px-4 py-3 text-sm text-below">
            {error}
          </p>
        ) : result ? (
          <div className="space-y-4">
            {portfolio ? <PortfolioCoverageCard result={portfolio} /> : null}
            <IllustrationResults
              result={result}
              fund={fund}
              holdingDollars={holding}
            />
          </div>
        ) : null}
      </div>
    </div>
  );
}

function UnitToggle({
  active,
  onClick,
  label,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`h-9 rounded-md px-3 text-sm ${
        active
          ? "bg-accent text-white"
          : "border border-line text-muted hover:text-ink"
      }`}
    >
      {label}
    </button>
  );
}
