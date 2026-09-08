import { TickerHistoryLink } from "@/components/illustrate/TickerHistoryLink";
import { formatUsd } from "@/lib/format";
import {
  YEAR_TAX_DETAIL,
  YEAR_TAX_EMPTY,
  YEAR_TAX_HEADING,
} from "@/lib/illustrate/portfolio-compare-copy";
import { TAX_DRAG_NA_LABEL } from "@/lib/illustrate/tax-drag-chart";
import {
  hasCalendarYearTax,
  type YearTaxRow,
  type YearTaxTableModel,
} from "@/lib/illustrate/portfolio-year-tax";

function taxCell(value: number | null): string {
  if (value == null) return TAX_DRAG_NA_LABEL;
  return formatUsd(Math.round(value), 0);
}

function SideRows({
  label,
  rows,
  years,
}: {
  label: string;
  rows: YearTaxRow[];
  years: number[];
}) {
  if (rows.length === 0) return null;
  return (
    <>
      <tr className="border-b border-line bg-paper">
        <th
          colSpan={years.length + 1}
          className="py-1.5 pr-2 text-left text-[10px] font-semibold uppercase tracking-[0.12em] text-faint"
        >
          {label}
        </th>
      </tr>
      {rows.map((row) => (
        <tr key={row.key} className="border-b border-line last:border-0">
          <td className="py-2 pr-2 font-mono text-[13px] font-medium text-ink">
            <TickerHistoryLink ticker={row.ticker} />
          </td>
          {row.cells.map((cell, index) => (
            <td
              key={`${row.key}-${years[index]}`}
              className={`px-2 py-2 text-right font-mono text-[12px] tabular-nums ${
                cell == null ? "text-faint" : "text-ink"
              }`}
            >
              {taxCell(cell)}
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}

export function CalendarYearTaxTable({
  model,
  headingId = "calendar-year-tax",
  className = "",
}: {
  model: YearTaxTableModel;
  headingId?: string;
  className?: string;
}) {
  const populated = hasCalendarYearTax(model);

  return (
    <section
      aria-labelledby={headingId}
      className={`flex flex-col rounded-2xl border border-line bg-surface p-3 shadow-[0_8px_24px_rgba(26,29,26,0.06)] sm:p-4 ${className}`}
    >
      <header className="mb-3 flex flex-wrap items-end justify-between gap-2">
        <h2 id={headingId} className="font-serif text-lg tracking-tight text-ink">
          {YEAR_TAX_HEADING}
        </h2>
        <p className="text-[10px] text-muted">{YEAR_TAX_DETAIL}</p>
      </header>

      {!populated ? (
        <p className="px-1 py-5 text-sm text-muted">{YEAR_TAX_EMPTY}</p>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-line bg-paper px-3 py-2">
          <table className="min-w-full text-sm">
            <thead className="text-[10px] font-semibold uppercase tracking-[0.12em] text-faint">
              <tr className="border-b border-line">
                <th className="py-1.5 pr-2 text-left">Ticker</th>
                {model.years.map((year) => (
                  <th key={year} className="px-2 py-1.5 text-right">
                    {year}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <SideRows label="Current" rows={model.current} years={model.years} />
              <SideRows label="Proposed" rows={model.proposed} years={model.years} />
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
