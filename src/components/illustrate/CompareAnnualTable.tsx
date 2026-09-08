import { TickerHistoryLink } from "@/components/illustrate/TickerHistoryLink";
import { formatUsd } from "@/lib/format";
import type { CompareAnnualTableModel } from "@/lib/illustrate/compare-workspace";
import { TAX_DRAG_NA_LABEL } from "@/lib/illustrate/tax-drag-chart";

function moneyCell(value: number | null): string {
  if (value == null) return TAX_DRAG_NA_LABEL;
  return formatUsd(Math.round(value), 0);
}

export function CompareAnnualTable({
  model,
  headingId = "compare-annual-history",
  className = "",
}: {
  model: CompareAnnualTableModel;
  headingId?: string;
  className?: string;
}) {
  const empty = model.groups.length === 0;

  return (
    <section
      aria-labelledby={headingId}
      className={`flex w-full flex-col rounded-2xl border border-line bg-surface p-3 shadow-[0_8px_24px_rgba(26,29,26,0.06)] sm:p-4 ${className}`}
    >
      <header className="mb-3 flex flex-wrap items-end justify-between gap-2">
        <h2 id={headingId} className="font-serif text-lg tracking-tight text-ink">
          Calendar-year tax & distributions
        </h2>
        <p className="text-[10px] text-muted">
          historical tax $ and dist $ · not Upcoming
        </p>
      </header>

      {empty ? (
        <p className="px-1 py-5 text-sm text-muted">
          Add tickers above to load calendar-year history from the Data API.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-line bg-paper px-3 py-2">
          <table className="min-w-full text-sm">
            <thead className="text-[10px] font-semibold uppercase tracking-[0.12em] text-faint">
              <tr className="border-b border-line">
                <th className="py-1.5 pr-2 text-left">Ticker</th>
                <th className="px-2 py-1.5 text-left">Series</th>
                {model.years.map((year) => (
                  <th key={year} className="px-2 py-1.5 text-right">
                    {year}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {model.groups.map((group) =>
                group.rows.map((row, index) => (
                  <tr key={row.key} className="border-b border-line last:border-0">
                    <td className="py-2 pr-2 font-mono text-[13px] font-medium text-ink">
                      {index === 0 ? <TickerHistoryLink ticker={row.ticker} /> : null}
                    </td>
                    <td className="px-2 py-2 text-[11px] text-muted">{row.label}</td>
                    {row.cells.map((cell, cellIndex) => (
                      <td
                        key={`${row.key}-${model.years[cellIndex]}`}
                        className={`px-2 py-2 text-right font-mono text-[12px] tabular-nums ${
                          cell == null ? "text-faint" : "text-ink"
                        }`}
                      >
                        {moneyCell(cell)}
                      </td>
                    ))}
                  </tr>
                )),
              )}
            </tbody>
          </table>
        </div>
      )}
      <p className="mt-2 text-[10px] text-faint">
        {TAX_DRAG_NA_LABEL} = unmatched / uncovered · never $0 · dates from Data only
      </p>
    </section>
  );
}
