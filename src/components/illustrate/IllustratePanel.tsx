"use client";

import { useEffect, useMemo, useState } from "react";
import type { FundEstimateView } from "@/data/types";
import { isLiveCoveredFamily } from "@/lib/coverage";
import { isMockIllustrate, postIllustrate } from "@/lib/illustrate/client";
import { distributionIdsForFund } from "@/lib/illustrate/ids";
import {
  AMOUNT_UNITS,
  DEFAULT_HOLDING_DOLLARS,
  UI_DEFAULT_TAX_RATES,
  type AmountUnit,
  type IllustrateRequest,
  type IllustrateResponse,
  type TaxRates,
} from "@/lib/illustrate/types";
import { FundPicker } from "@/components/illustrate/FundPicker";
import { IllustrationResults } from "@/components/illustrate/IllustrationResults";
import { TaxRateFields } from "@/components/illustrate/TaxRateFields";

export function IllustratePanel({
  funds,
  selected,
  onSelect,
}: {
  funds: FundEstimateView[];
  selected: FundEstimateView | null;
  onSelect: (fund: FundEstimateView) => void;
}) {
  return (
    <section
      id="illustrate"
      aria-labelledby="illustrate-heading"
      className="mb-10 rounded-lg border border-line bg-surface p-4 shadow-[0_1px_2px_rgba(28,51,72,0.04)] sm:p-6"
    >
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-teal">
            Tax impact
          </p>
          <h2
            id="illustrate-heading"
            className="mt-1 font-serif text-xl tracking-tight text-navy"
          >
            Dollar illustration
          </h2>
          <p className="mt-1 max-w-2xl text-sm text-muted">
            Pick a fund and a holding size. Aftertax posts rates to the illustrate
            API and shows estimated distribution and tax in dollars.
          </p>
        </div>
        {selected && !isLiveCoveredFamily(selected.family) ? (
          <p className="max-w-xs rounded-md border border-gold/30 bg-gold-soft px-3 py-2 text-xs text-navy">
            Coverage gap: {selected.family} is not in live ingest yet. Result uses
            sample data and can understate tax impact.
          </p>
        ) : null}
      </div>

      <div className="space-y-4">
        <FundPicker funds={funds} selected={selected} onSelect={onSelect} />
        {selected ? (
          <IllustrationWorkspace key={selected.id} fund={selected} />
        ) : (
          <div className="flex min-h-[16rem] items-center justify-center rounded-md border border-dashed border-line-strong px-6 text-center text-sm text-muted">
            Search a fund to see estimated distribution and tax in dollars.
          </div>
        )}
      </div>
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
  const [unit, setUnit] = useState<AmountUnit>(AMOUNT_UNITS.percent_of_nav);
  const [navInput, setNavInput] = useState(String(fund.nav));
  const [result, setResult] = useState<IllustrateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const distributionIds = useMemo(
    () => distributionIdsForFund(fund.id, unit),
    [fund.id, unit],
  );

  const needsNav = unit === AMOUNT_UNITS.per_share;
  const nav = Number(navInput);
  const navError =
    needsNav && !(nav > 0)
      ? "Enter NAV per share to illustrate $ / share amounts."
      : null;
  const canFetch = distributionIds.length > 0 && !navError;

  useEffect(() => {
    if (!canFetch) return;

    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      const mock = isMockIllustrate();
      const request: IllustrateRequest = {
        holding_dollars: holding,
        ...(mock
          ? { distribution_ids: distributionIds }
          : {
              selector: {
                fund_family: fund.family,
                fund_identifier: fund.ticker,
              },
            }),
        nav_per_share: needsNav ? nav : null,
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
          setResult(null);
          setError(caught instanceof Error ? caught.message : "Illustration failed");
          setLoading(false);
        });
    }, 250);

    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [canFetch, distributionIds, holding, rates, combine, needsNav, nav, fund.family, fund.ticker]);

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
            % of NAV uses holding dollars only. Switch to $ / share to send
            nav_per_share.
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
          <IllustrationResults result={result} />
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
          ? "bg-navy text-white"
          : "border border-line text-muted hover:text-ink"
      }`}
    >
      {label}
    </button>
  );
}
