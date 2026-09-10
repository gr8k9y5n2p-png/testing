"use client";

import { useEffect, useState } from "react";
import type { FundEstimate, FundEstimateView } from "@/data/types";
import {
  DATA_API_UNAVAILABLE,
  ILLUSTRATION_PAID_HISTORY_DETAIL,
  ILLUSTRATION_PAID_HISTORY_KICKER,
  PAID_HISTORY_EMPTY,
  SEARCH_PAID_HISTORY_HEADING,
} from "@/lib/copy";
import { fetchFundsSearch } from "@/lib/data-api/funds-client";
import { formatUsd } from "@/lib/format";
import { formatSoftPct } from "@/lib/illustrate/nav-math";
import { GROWTH_TAX_TYPE_LABELS } from "@/lib/illustrate/growth-tax-by-type";
import {
  illustrationPaidHistoryMatrix,
  illustrationPaidHistoryYears,
  type IllustrationPaidMatrixCell,
} from "@/lib/illustrate/illustration-paid-history";

const ESTIMATE_LABELS: Record<string, string> = {
  ...GROWTH_TAX_TYPE_LABELS,
  ordinary_income: "Ordinary",
  long_term_capital_gains: "LTCG",
  short_term_capital_gains: "STCG",
  qualified_dividend: "QDI",
  total_capital_gains: "Total capital gains",
  special_dividend: "Special",
  return_of_capital: "ROC",
};

function formatMatrixCell(cell: IllustrationPaidMatrixCell): string {
  if (cell.perShare != null) {
    return `${formatUsd(cell.perShare, 4)} / sh`;
  }
  if (cell.pctOfNav != null) {
    return formatSoftPct(cell.pctOfNav);
  }
  return "—";
}

export function IllustrationPaidHistory({ fund }: { fund: FundEstimate }) {
  const [hydrated, setHydrated] = useState<FundEstimateView | null>(null);
  const [unavailable, setUnavailable] = useState(false);

  useEffect(() => {
    const ticker = fund.ticker.trim().toUpperCase();
    setHydrated(null);
    setUnavailable(false);
    if (!ticker || ticker === "—") {
      return;
    }
    let cancelled = false;
    void fetchFundsSearch<FundEstimateView>(ticker, 5, { navOnly: false }).then((result) => {
      if (cancelled) return;
      if (result.unavailable) {
        setUnavailable(true);
        return;
      }
      const match = result.items.find(
        (row) => row.ticker.trim().toUpperCase() === ticker,
      );
      setHydrated(match ?? null);
    });
    return () => {
      cancelled = true;
    };
  }, [fund.ticker]);

  const source = hydrated ?? fund;
  const years = illustrationPaidHistoryYears();
  const matrix = illustrationPaidHistoryMatrix(source);
  const empty = matrix.rows.length === 0;

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
            {years[0]}–{years[years.length - 1]} · {ILLUSTRATION_PAID_HISTORY_DETAIL}
          </p>
        </div>
      </header>
      {empty ? (
        <p className="px-4 py-6 text-sm text-muted">
          {unavailable ? DATA_API_UNAVAILABLE : PAID_HISTORY_EMPTY}
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-surface text-[11px] font-semibold uppercase tracking-[0.1em] text-faint">
              <tr>
                <th className="px-4 py-2 text-left">Component</th>
                {matrix.years.map((year) => (
                  <th key={year} className="px-4 py-2 text-right">
                    {year}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {matrix.rows.map((row) => (
                <tr key={row.estimateType || "distribution"}>
                  <td className="px-4 py-2.5 text-ink">
                    {row.estimateType
                      ? (ESTIMATE_LABELS[row.estimateType] ?? row.estimateType)
                      : "—"}
                  </td>
                  {matrix.years.map((year) => (
                    <td
                      key={year}
                      className="px-4 py-2.5 text-right font-mono tabular-nums"
                    >
                      {formatMatrixCell(row.cells[year] ?? { perShare: null, pctOfNav: null, amountUnit: null })}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
