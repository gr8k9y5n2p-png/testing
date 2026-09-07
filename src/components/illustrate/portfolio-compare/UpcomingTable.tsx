import { formatUsd } from "@/lib/format";
import {
  formatAsOfStage,
  heatBackground,
  type UpcomingRow,
} from "@/lib/illustrate/portfolio-compare-map";

export function UpcomingTable({
  rows,
  sample,
}: {
  rows: UpcomingRow[];
  sample: boolean;
}) {
  return (
    <section
      aria-labelledby="upcoming-heading"
      className="rounded-2xl border border-line bg-surface p-4 shadow-[0_8px_24px_rgba(26,29,26,0.06)] sm:p-5"
    >
      <header className="mb-4 flex flex-wrap items-end justify-between gap-2">
        <h2
          id="upcoming-heading"
          className="font-serif text-xl tracking-tight text-ink"
        >
          Upcoming distributions
        </h2>
        <p className="text-[11px] text-muted">
          on allocated dollars · sorted by est. dist ↓
        </p>
      </header>

      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="text-[10px] font-semibold uppercase tracking-[0.12em] text-faint">
            <tr className="border-b border-line">
              <th className="py-2 pr-3 text-left">Ticker / Fund</th>
              <th className="px-3 py-2 text-left">Side</th>
              <th className="px-3 py-2 text-right">Est. upcoming dist</th>
              <th className="px-3 py-2 text-right">Est. tax on upcoming</th>
              <th className="py-2 pl-3 text-right">As-of / Stage</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-8 text-center text-sm text-muted">
                  No upcoming distribution estimates for these holdings.
                </td>
              </tr>
            ) : (
              rows.map((row) => (
                <tr key={row.key} className="border-b border-line last:border-0">
                  <td className="py-2.5 pr-3">
                    <span className="block font-mono text-sm font-medium text-ink">
                      {row.ticker}
                    </span>
                    <span className="block text-[11px] text-muted">{row.fundName}</span>
                  </td>
                  <td className="px-3 py-2.5">
                    <span
                      className={`inline-flex rounded-full px-2 py-0.5 text-[11px] font-medium ${
                        row.side === "proposed"
                          ? "bg-accent-soft text-accent"
                          : "bg-notice text-muted"
                      }`}
                    >
                      {row.sideLabel}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 text-right">
                    <span
                      className={`inline-block min-w-[5.5rem] rounded-md px-2 py-1 font-mono text-[13px] tabular-nums ${heatBackground(row.heat)}`}
                    >
                      {formatUsd(row.distributionDollars, 0)}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 text-right font-mono text-[13px] tabular-nums">
                    {row.estimatedTax == null ? (
                      "—"
                    ) : Math.abs(row.estimatedTax) < 0.5 ? (
                      <span className="text-tax-less">{formatUsd(0, 0)}</span>
                    ) : (
                      formatUsd(row.estimatedTax, 0)
                    )}
                  </td>
                  <td className="py-2.5 pl-3 text-right text-[12px] text-muted">
                    {formatAsOfStage(row.asOf, row.stage)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <p className="mt-3 text-[10px] text-faint">
        {sample ? "demo · " : ""}from Data upcoming components · heat = relative est. dist $
      </p>
    </section>
  );
}
