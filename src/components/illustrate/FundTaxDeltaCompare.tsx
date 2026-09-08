"use client";

import { useEffect, useMemo, useState } from "react";
import { TaxDeltaCompareCard } from "@/components/illustrate/TaxDeltaCompareCard";
import { postIllustrateCompare } from "@/lib/illustrate/compare-client";
import { toDataApiCompareBody } from "@/lib/illustrate/compare-request";
import { seedNavLookup } from "@/lib/illustrate/seed-nav";
import {
  COMPARE_SUMMARY_HOLDING_DOLLARS,
  type ComparePeriodIn,
  type CompareResponse,
  type CompareSideIn,
} from "@/lib/illustrate/compare-types";
import { toTaxDeltaCardModel } from "@/lib/illustrate/compare-map";
import type { TaxRates } from "@/lib/illustrate/types";

const DEFAULT_PERIODS: ComparePeriodIn[] = [
  { year: 2021 },
  { year: 2022 },
  { year: 2023 },
  { year: 2024 },
  { year: 2025 },
];

export type FundTaxDeltaCompareProps = {
  left: CompareSideIn;
  right: CompareSideIn;
  /** Request holding. Summary footer is always normalized to $10k by the API. */
  holdingDollars?: number;
  taxRates?: Partial<TaxRates> | Record<string, never>;
  periods?: ComparePeriodIn[];
  className?: string;
};

type CompareQuery = {
  left: CompareSideIn;
  right: CompareSideIn;
  holdingDollars: number;
  taxRates: Partial<TaxRates> | Record<string, never> | null;
  periods: ComparePeriodIn[];
};

export function FundTaxDeltaCompare({
  left,
  right,
  holdingDollars = COMPARE_SUMMARY_HOLDING_DOLLARS,
  taxRates,
  periods = DEFAULT_PERIODS,
  className,
}: FundTaxDeltaCompareProps) {
  const query = useMemo<CompareQuery>(
    () => ({
      left,
      right,
      holdingDollars,
      taxRates: taxRates ?? null,
      periods,
    }),
    [left, right, holdingDollars, taxRates, periods],
  );
  const requestKey = JSON.stringify(query);
  const [retry, setRetry] = useState(0);
  const fetchKey = `${requestKey}:${retry}`;
  const [settledKey, setSettledKey] = useState<string | null>(null);
  const [result, setResult] = useState<CompareResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const loading = settledKey !== fetchKey;

  useEffect(() => {
    const controller = new AbortController();
    const next = JSON.parse(requestKey) as CompareQuery;

    void postIllustrateCompare(
      toDataApiCompareBody(
        {
          mode: "fund_vs_fund",
          holding_dollars: next.holdingDollars,
          combine_state_with_federal: true,
          latest_as_of_only: true,
          left: next.left,
          right: next.right,
          periods: next.periods,
          tax_rates: next.taxRates ?? {},
        },
        seedNavLookup,
      ),
      { signal: controller.signal },
    )
      .then((payload) => {
        setResult(payload);
        setError(null);
        setSettledKey(fetchKey);
      })
      .catch((caught: unknown) => {
        if (caught instanceof DOMException && caught.name === "AbortError") return;
        setResult(null);
        setError(caught instanceof Error ? caught.message : "Compare failed");
        setSettledKey(fetchKey);
      });

    return () => controller.abort();
  }, [requestKey, fetchKey]);

  if (loading) {
    return (
      <div
        className={`min-h-[420px] w-full max-w-[420px] animate-pulse rounded-2xl border border-line bg-surface shadow-[0_8px_24px_rgba(26,29,26,0.08)] ${className ?? ""}`}
        aria-busy
        aria-label="Loading fund tax-delta compare"
      />
    );
  }

  if (error) {
    return (
      <div
        className={`flex min-h-[420px] w-full max-w-[420px] flex-col items-start justify-center rounded-2xl border border-tax-more/20 bg-tax-more-soft px-5 py-6 ${className ?? ""}`}
      >
        <p className="font-serif text-lg text-tax-more">Compare unavailable</p>
        <p className="mt-2 text-sm text-ink">{error}</p>
        <button
          type="button"
          onClick={() => setRetry((value) => value + 1)}
          className="mt-4 h-9 rounded-md bg-accent px-3 text-sm text-white hover:bg-accent-hover"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!result) {
    return (
      <div
        className={`flex min-h-[420px] w-full max-w-[420px] flex-col items-start justify-center rounded-2xl border border-dashed border-line-strong bg-surface px-5 py-6 ${className ?? ""}`}
      >
        <p className="font-serif text-lg text-ink">Compare unavailable</p>
        <p className="mt-2 text-sm text-muted">
          POST /illustrate/compare returned no payload for these two funds.
        </p>
      </div>
    );
  }

  const model = toTaxDeltaCardModel(result, {
    left: left.label,
    right: right.label,
  });

  return <TaxDeltaCompareCard model={model} className={className} />;
}
