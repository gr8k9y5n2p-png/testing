import { TickerHistoryLink } from "@/components/illustrate/TickerHistoryLink";
import { formatUsd } from "@/lib/format";
import {
  formatAsOfStage,
  heatBackground,
  type UpcomingRow,
} from "@/lib/illustrate/portfolio-compare-map";

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
  return (
    <section
      aria-labelledby={headingId}
      className={`flex flex-col rounded-2xl border border-line bg-surface p-3 shadow-[0_8px_24px_rgba(26,29,26,0.06)] sm:p-4 ${className}`}
    >
      <header className="mb-3 flex flex-wrap items-end justify-between gap-2">
        <h2
          id={headingId}
          className="font-serif text-lg tracking-tight text-ink"
        >
          Upcoming distributions
        </h2>
        <p className="text-[10px] text-muted">sorted by est. dist ↓</p>
      </header>

      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="text-[10px] font-semibold uppercase tracking-[0.12em] text-faint">
            <tr className="border-b border-line">
              <th className="py-1.5 pr-2 text-left">Ticker</th>
              <th className="px-2 py-1.5 text-right">Est. dist $</th>
              <th className="px-2 py-1.5 text-right">Est. tax</th>
              <th className="py-1.5 pl-2 text-right">Stage</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={4} className="py-6 text-center text-sm text-muted">
                  No upcoming estimates for these holdings.
                </td>
              </tr>
            ) : (
              rows.map((row) => (
                <tr key={row.key} className="border-b border-line last:border-0">
                  <td className="py-2 pr-2 font-mono text-[13px] font-medium text-ink">
                    <TickerHistoryLink ticker={row.ticker} />
                  </td>
                  <td className="px-2 py-2 text-right">
                    <span
                      className={`inline-block min-w-[4.25rem] rounded-md px-1.5 py-0.5 text-center font-mono text-[12px] tabular-nums ${heatBackground(row.heat)}`}
                    >
                      {formatUsd(row.distributionDollars, 0)}
                    </span>
                  </td>
                  <td className="px-2 py-2 text-right font-mono text-[12px] tabular-nums">
                    {row.estimatedTax == null ? (
                      "—"
                    ) : Math.abs(row.estimatedTax) < 0.5 ? (
                      <span className="text-tax-less">{formatUsd(0, 0)}</span>
                    ) : (
                      formatUsd(row.estimatedTax, 0)
                    )}
                  </td>
                  <td className="py-2 pl-2 text-right text-[11px] text-muted">
                    {formatAsOfStage(row.asOf, row.stage)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-[10px] text-faint">
        heat = relative within {sideLabel}
      </p>
    </section>
  );
}
