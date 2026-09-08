import type { ReactNode } from "react";
import { TickerHistoryLink } from "@/components/illustrate/TickerHistoryLink";
import { formatOptionalDate, formatUsd } from "@/lib/format";
import {
  UPCOMING_MODULE_DETAIL,
  UPCOMING_MODULE_HEADING,
  UPCOMING_UNAVAILABLE_DETAIL,
  UPCOMING_UNAVAILABLE_HEADLINE,
} from "@/lib/illustrate/portfolio-compare-copy";
import {
  heatBackground,
  type UpcomingRow,
} from "@/lib/illustrate/portfolio-compare-map";
import { TAX_DRAG_NA_LABEL } from "@/lib/illustrate/tax-drag-chart";

function dateCell(value: string | null): string {
  return formatOptionalDate(value);
}

function taxCell(row: UpcomingRow): ReactNode {
  if (!row.available || !row.covered || row.estimatedTax == null) {
    return <span className="text-faint">{TAX_DRAG_NA_LABEL}</span>;
  }
  if (Math.abs(row.estimatedTax) < 0.5) {
    return <span className="text-tax-less">{formatUsd(0, 0)}</span>;
  }
  return formatUsd(row.estimatedTax, 0);
}

function distCell(row: UpcomingRow, showHeat: boolean): ReactNode {
  if (!row.available || row.distributionDollars == null) {
    return (
      <span className="text-[11px] font-sans font-medium normal-case tracking-normal text-muted">
        {UPCOMING_UNAVAILABLE_HEADLINE}
      </span>
    );
  }
  return (
    <span
      className={`inline-block min-w-[4.25rem] rounded-md px-1.5 py-0.5 text-center font-mono text-[12px] tabular-nums ${
        showHeat ? heatBackground(row.heat) : "text-ink"
      }`}
    >
      {formatUsd(row.distributionDollars, 0)}
    </span>
  );
}

function SectionHeader({
  headingId,
  title,
  legend,
}: {
  headingId: string;
  title: string;
  legend: string;
}) {
  return (
    <header className="mb-3 flex flex-wrap items-end justify-between gap-2">
      <h2 id={headingId} className="font-serif text-lg tracking-tight text-ink">
        {title}
      </h2>
      <p className="text-[10px] text-muted">{legend}</p>
    </header>
  );
}

export function UpcomingTable({
  rows,
  headingId,
  sideLabel,
  className = "",
}: {
  rows: UpcomingRow[];
  headingId: string;
  sideLabel: "Current" | "Proposed";
  className?: string;
}) {
  const anyAvailable = rows.some((row) => row.available);

  return (
    <section
      aria-labelledby={headingId}
      className={`flex flex-col rounded-2xl border border-line bg-surface p-3 shadow-[0_8px_24px_rgba(26,29,26,0.06)] sm:p-4 ${className}`}
    >
      <SectionHeader
        headingId={headingId}
        title={UPCOMING_MODULE_HEADING}
        legend={`${UPCOMING_MODULE_DETAIL} · ${sideLabel}`}
      />

      <div className="rounded-xl border border-line bg-surface px-3 py-2">
        {!anyAvailable ? (
          <div className="px-1 py-5">
            <p className="font-serif text-base tracking-tight text-ink">
              {UPCOMING_UNAVAILABLE_HEADLINE}
            </p>
            <p className="mt-1 text-[12px] leading-relaxed text-muted">
              {UPCOMING_UNAVAILABLE_DETAIL}
            </p>
          </div>
        ) : null}
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="text-[10px] font-semibold uppercase tracking-[0.12em] text-faint">
              <tr className="border-b border-line">
                <th className="py-1.5 pr-2 text-left">Ticker</th>
                <th className="px-2 py-1.5 text-right">Est. dist $</th>
                <th className="px-2 py-1.5 text-right">Est. tax</th>
                <th className="px-2 py-1.5 text-right">Record</th>
                <th className="py-1.5 pl-2 text-right">Ex-div</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.key} className="border-b border-line last:border-0">
                  <td className="py-2 pr-2 font-mono text-[13px] font-medium text-ink">
                    <TickerHistoryLink ticker={row.ticker} />
                  </td>
                  <td className="px-2 py-2 text-right">{distCell(row, true)}</td>
                  <td className="px-2 py-2 text-right font-mono text-[12px] tabular-nums">
                    {taxCell(row)}
                  </td>
                  <td className="px-2 py-2 text-right font-mono text-[11px] tabular-nums text-muted">
                    {dateCell(row.recordDate)}
                  </td>
                  <td className="py-2 pl-2 text-right font-mono text-[11px] tabular-nums text-muted">
                    {dateCell(row.exDate)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <p className="mt-2 text-[10px] text-faint">
        every fund · empty upcoming is undisclosed, not $0 · dates include year · {sideLabel}
      </p>
    </section>
  );
}
