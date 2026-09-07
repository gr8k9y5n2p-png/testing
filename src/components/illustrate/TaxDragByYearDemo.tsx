"use client";

import { useEffect, useState } from "react";
import { TaxDragByYearChart } from "@/components/illustrate/TaxDragByYearChart";
import { postIllustrateCompare } from "@/lib/illustrate/compare-client";
import type {
  ComparePeriodIn,
  CompareResponse,
  CompareSelectors,
} from "@/lib/illustrate/compare-types";
import {
  taxDragLineFromPeriods,
  toTaxDragPeriods,
  toUpcomingSummary,
  type TaxDragMetric,
} from "@/lib/illustrate/tax-drag-chart";

const DEFAULT_YOY_PERIODS: ComparePeriodIn[] = [
  { year: 2021 },
  { year: 2022 },
  { year: 2023 },
  { year: 2024 },
  { year: 2025 },
];

const DEFAULT_SELECTORS: CompareSelectors = {
  fund_family: "American Funds",
  fund_identifier: "AMCPX",
  ticker: "AMCPX",
  fund_name: "AMCAP Fund",
};

export type TaxDragByYearDemoProps = {
  selectors?: CompareSelectors;
  holdingDollars?: number;
  periods?: ComparePeriodIn[];
  metric?: TaxDragMetric;
  showLine?: boolean;
  className?: string;
  title?: string;
};

type YoyQuery = {
  selectors: CompareSelectors;
  holdingDollars: number;
  periods: ComparePeriodIn[];
};

/**
 * Dollar Illustration drop-in: posts `mode: "yoy"` and renders TaxDragByYearChart.
 * Falls back to the local mock when the Data API is unreachable.
 */
export function TaxDragByYearDemo({
  selectors = DEFAULT_SELECTORS,
  holdingDollars = 10_000,
  periods = DEFAULT_YOY_PERIODS,
  metric = "tax_dollars",
  showLine = true,
  className,
  title,
}: TaxDragByYearDemoProps) {
  const requestKey = JSON.stringify({ selectors, holdingDollars, periods });
  const [retry, setRetry] = useState(0);
  const fetchKey = `${requestKey}:${retry}`;
  const [settledKey, setSettledKey] = useState<string | null>(null);
  const [result, setResult] = useState<CompareResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const loading = settledKey !== fetchKey;

  useEffect(() => {
    const controller = new AbortController();
    const next = JSON.parse(requestKey) as YoyQuery;

    void postIllustrateCompare(
      {
        mode: "yoy",
        holding_dollars: next.holdingDollars,
        selectors: next.selectors,
        left: { label: next.selectors.fund_name, selectors: next.selectors },
        periods: next.periods,
        tax_rates: {},
        combine_state_with_federal: true,
        latest_as_of_only: true,
      },
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
        setError(caught instanceof Error ? caught.message : "YoY compare failed");
        setSettledKey(fetchKey);
      });

    return () => controller.abort();
  }, [requestKey, fetchKey]);

  if (error) {
    return (
      <div
        className={`flex min-h-[240px] w-full max-w-[420px] flex-col items-start justify-center rounded-2xl border border-tax-more/20 bg-tax-more-soft px-5 py-6 ${className ?? ""}`}
      >
        <p className="font-serif text-lg text-tax-more">YoY tax drag unavailable</p>
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

  const nextPeriods = result ? toTaxDragPeriods(result, metric) : [];
  const upcoming = result
    ? toUpcomingSummary(result.summary.upcoming_taxable_distribution, "either")
    : null;

  return (
    <TaxDragByYearChart
      periods={nextPeriods}
      metric={metric}
      title={title}
      lineSeries={showLine ? taxDragLineFromPeriods(nextPeriods) : null}
      upcomingSummary={upcoming}
      loading={loading}
      sample={result?.source === "mock"}
      className={className}
    />
  );
}
