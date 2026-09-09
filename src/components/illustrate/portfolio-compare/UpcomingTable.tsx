import { TickerHistoryLink } from "@/components/illustrate/TickerHistoryLink";
import { formatOptionalDate } from "@/lib/format";
import {
  UPCOMING_MODULE_DETAIL,
  UPCOMING_MODULE_HEADING,
  UPCOMING_UNAVAILABLE_DETAIL,
  UPCOMING_UNAVAILABLE_HEADLINE,
} from "@/lib/illustrate/portfolio-compare-copy";
import {
  upcomingDistributionLine,
  upcomingEstimatedTaxLine,
  type UpcomingRow,
} from "@/lib/illustrate/portfolio-compare-map";

function dateCell(value: string | null): string {
  return formatOptionalDate(value);
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

function TickerCell({ row }: { row: UpcomingRow }) {
  return (
    <div className="min-w-[11rem]">
      <div className="font-mono text-[13px] font-medium text-ink">
        <TickerHistoryLink ticker={row.ticker} />
      </div>
      <p className="mt-1 text-[11px] leading-snug text-muted">
        {upcomingDistributionLine(row)}
      </p>
      <p className="text-[11px] leading-snug text-muted">
        {upcomingEstimatedTaxLine(row)}
      </p>
    </div>
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
  sideLabel?: string;
  className?: string;
}) {
  const anyAvailable = rows.some((row) => row.available);
  const legend = sideLabel
    ? `${UPCOMING_MODULE_DETAIL} · ${sideLabel}`
    : UPCOMING_MODULE_DETAIL;

  return (
    <section
      aria-labelledby={headingId}
      className={`flex flex-col rounded-2xl border border-line bg-surface p-3 shadow-[0_8px_24px_rgba(26,29,26,0.06)] sm:p-4 ${className}`}
    >
      <SectionHeader
        headingId={headingId}
        title={UPCOMING_MODULE_HEADING}
        legend={legend}
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
                <th className="px-2 py-1.5 text-right">Record</th>
                <th className="py-1.5 pl-2 text-right">Ex-div</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.key} className="border-b border-line last:border-0">
                  <td className="py-2 pr-3 align-top">
                    <TickerCell row={row} />
                  </td>
                  <td className="px-2 py-2 align-top text-right font-mono text-[11px] tabular-nums text-muted">
                    {dateCell(row.recordDate)}
                  </td>
                  <td className="py-2 pl-2 align-top text-right font-mono text-[11px] tabular-nums text-muted">
                    {dateCell(row.exDate)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <p className="mt-2 text-[10px] text-faint">
        every fund · empty upcoming is undisclosed, not $0 · dates include year
        {sideLabel ? ` · ${sideLabel}` : ""}
      </p>
    </section>
  );
}
