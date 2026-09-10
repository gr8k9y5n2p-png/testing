"use client";

import { useEffect, useState } from "react";
import type { FundEstimate, FundEstimateView } from "@/data/types";
import { publicationStageLabel } from "@/data/distribution-bucket";
import {
  ILLUSTRATION_PAID_HISTORY_DETAIL,
  ILLUSTRATION_PAID_HISTORY_KICKER,
  PAID_HISTORY_EMPTY,
  SEARCH_PAID_HISTORY_HEADING,
} from "@/lib/copy";
import { formatOptionalDate, formatUsd } from "@/lib/format";
import { formatSoftPct } from "@/lib/illustrate/nav-math";
import {
  illustrationPaidHistoryYear,
  illustrationPaidTypeRows,
} from "@/lib/illustrate/illustration-paid-history";

const ESTIMATE_LABELS: Record<string, string> = {
  ordinary_income: "Ordinary income",
  long_term_capital_gains: "Long-term capital gains",
  short_term_capital_gains: "Short-term capital gains",
  qualified_dividend: "Qualified dividends",
  total_capital_gains: "Total capital gains",
  special_dividend: "Special dividend",
  return_of_capital: "Return of capital",
};

/** Full ticker hydrate so prior-year finals come from GET /distributions. */
async function fetchTickerDistributions(
  ticker: string,
): Promise<FundEstimateView | null> {
  const params = new URLSearchParams();
  params.set("q", ticker);
  params.set("limit", "5");
  const response = await fetch(`/api/funds?${params.toString()}`);
  if (!response.ok) return null;
  const body = (await response.json()) as {
    items?: FundEstimateView[];
    data?: FundEstimateView[];
  };
  const items = Array.isArray(body.items)
    ? body.items
    : Array.isArray(body.data)
      ? body.data
      : [];
  return (
    items.find((row) => row.ticker.trim().toUpperCase() === ticker) ?? null
  );
}

export function IllustrationPaidHistory({ fund }: { fund: FundEstimate }) {
  const [hydrated, setHydrated] = useState<FundEstimateView | null>(null);

  useEffect(() => {
    const ticker = fund.ticker.trim().toUpperCase();
    setHydrated(null);
    if (!ticker || ticker === "—") {
      return;
    }
    let cancelled = false;
    void fetchTickerDistributions(ticker).then((match) => {
      if (!cancelled) setHydrated(match);
    });
    return () => {
      cancelled = true;
    };
  }, [fund.ticker]);

  const source = hydrated ?? fund;
  const year = illustrationPaidHistoryYear();
  const rows = illustrationPaidTypeRows(source);

  return (
    <section
      className="w-full overflow-hidden rounded-xl border border-line bg-paper"
      aria-labelledby="illustration-paid-history-heading"
    >
      <header className="flex flex-wrap items-end justify-between gap-2 border-b border-line px-4 py-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-faint">
            {ILLUSTRATION_PAID_HISTORY_KICKER}
          </p>
          <h3
            id="illustration-paid-history-heading"
            className="mt-1 font-serif text-xl tracking-tight text-ink"
          >
            {SEARCH_PAID_HISTORY_HEADING}
          </h3>
          <p className="mt-1 max-w-3xl text-sm text-muted">
            {year} · {ILLUSTRATION_PAID_HISTORY_DETAIL}
          </p>
        </div>
      </header>
      {rows.length === 0 ? (
        <p className="px-4 py-6 text-sm text-muted">{PAID_HISTORY_EMPTY}</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-surface text-[11px] font-semibold uppercase tracking-[0.1em] text-faint">
              <tr>
                <th className="px-4 py-2 text-left">Component</th>
                <th className="px-4 py-2 text-right">$ / Share</th>
                <th className="px-4 py-2 text-right">% of NAV</th>
                <th className="px-4 py-2 text-left">Announced</th>
                <th className="px-4 py-2 text-left">Record</th>
                <th className="px-4 py-2 text-left">Ex-Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {rows.map((row) => (
                <tr key={row.key}>
                  <td className="px-4 py-2.5">
                    <span className="block text-ink">
                      {row.estimateType
                        ? (ESTIMATE_LABELS[row.estimateType] ?? row.estimateType)
                        : "—"}
                    </span>
                    <span className="font-mono text-[11px] text-faint">
                      {publicationStageLabel(row.stage) || "—"}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-right font-mono">
                    {row.perShare == null ? "—" : `${formatUsd(row.perShare, 4)} / sh`}
                  </td>
                  <td className="px-4 py-2.5 text-right font-mono">
                    {formatSoftPct(row.pctOfNav)}
                  </td>
                  <td className="px-4 py-2.5 font-mono text-muted">
                    {formatOptionalDate(row.asOfDate)}
                  </td>
                  <td className="px-4 py-2.5 font-mono text-muted">
                    {formatOptionalDate(row.recordDate)}
                  </td>
                  <td className="px-4 py-2.5 font-mono text-muted">
                    {formatOptionalDate(row.exDate)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
