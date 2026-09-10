import { TickerHistoryLink } from "@/components/illustrate/TickerHistoryLink";
import { formatOptionalDate } from "@/lib/format";
import {
  ANNOUNCED_COLUMN,
  DIST_AMOUNT_COLUMN,
  DOLLAR_IMPACT_COLUMN,
  EX_COLUMN,
  PCT_OF_NAV_COLUMN,
  RECORD_COLUMN,
  isUpcomingEmptyAmount,
  UPCOMING_MODULE_DETAIL,
  UPCOMING_MODULE_HEADING,
  UPCOMING_SOFT_DASH,
  upcomingDistributionPerShareAmount,
  upcomingDollarImpactAmount,
  upcomingEmptyDetail,
  upcomingEmptyHeadline,
  upcomingPctOfNavAmount,
} from "@/lib/illustrate/portfolio-compare-copy";
import type { UpcomingRow } from "@/lib/illustrate/portfolio-compare-map";
import { UI_DEFAULT_TAX_RATES, type TaxRates } from "@/lib/illustrate/types";

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
    <div className="min-w-[7rem] max-w-[14rem]">
      <div className="font-mono text-[13px] font-medium text-ink">
        <TickerHistoryLink ticker={row.ticker} />
      </div>
      {row.fundName && row.fundName !== row.ticker ? (
        <p className="mt-0.5 truncate text-[11px] leading-snug text-muted">
          {row.fundName}
        </p>
      ) : null}
    </div>
  );
}

function MetricCell({
  value,
  undisclosed,
}: {
  value: string;
  undisclosed: boolean;
}) {
  return (
    <span
      className={`block font-mono tabular-nums ${
        undisclosed
          ? "text-[11px] leading-snug text-muted"
          : "text-[13px] font-medium text-ink"
      }`}
    >
      {value}
    </span>
  );
}

function DateCell({ value }: { value: string | null }) {
  const label = formatOptionalDate(value);
  return (
    <span
      className={`block font-mono tabular-nums ${
        label === UPCOMING_SOFT_DASH
          ? "text-[11px] leading-snug text-muted"
          : "text-[12px] text-ink"
      }`}
    >
      {label}
    </span>
  );
}

export function UpcomingTable({
  rows,
  headingId,
  sideLabel,
  className = "",
  taxRates = UI_DEFAULT_TAX_RATES,
  combineStateWithFederal = true,
}: {
  rows: UpcomingRow[];
  headingId: string;
  sideLabel?: string;
  className?: string;
  taxRates?: TaxRates;
  combineStateWithFederal?: boolean;
}) {
  const anyAvailable = rows.some((row) => row.available);
  const legend = sideLabel
    ? `${UPCOMING_MODULE_DETAIL} · ${sideLabel}`
    : UPCOMING_MODULE_DETAIL;
  const rates = { taxRates, combine: combineStateWithFederal };

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
              {upcomingEmptyHeadline(rows)}
            </p>
            <p className="mt-1 text-[12px] leading-relaxed text-muted">
              {upcomingEmptyDetail(rows)}
            </p>
          </div>
        ) : null}
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="text-[10px] font-semibold uppercase tracking-[0.12em] text-faint">
              <tr className="border-b border-line">
                <th className="py-1.5 pr-2 text-left">Ticker</th>
                <th className="px-2 py-1.5 text-right">{DIST_AMOUNT_COLUMN}</th>
                <th className="px-2 py-1.5 text-right">{PCT_OF_NAV_COLUMN}</th>
                <th className="px-2 py-1.5 text-right">{DOLLAR_IMPACT_COLUMN}</th>
                <th className="px-2 py-1.5 text-left">{ANNOUNCED_COLUMN}</th>
                <th className="px-2 py-1.5 text-left">{RECORD_COLUMN}</th>
                <th className="py-1.5 pl-2 text-left">{EX_COLUMN}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const perShare = upcomingDistributionPerShareAmount(row);
                const pct = upcomingPctOfNavAmount(row);
                const impact = upcomingDollarImpactAmount(row, rates);
                return (
                  <tr key={row.key} className="border-b border-line last:border-0">
                    <td className="py-2 pr-3 align-top">
                      <TickerCell row={row} />
                    </td>
                    <td className="px-2 py-2 align-top text-right">
                      <MetricCell
                        value={perShare}
                        undisclosed={isUpcomingEmptyAmount(perShare)}
                      />
                    </td>
                    <td className="px-2 py-2 align-top text-right">
                      <MetricCell
                        value={pct}
                        undisclosed={isUpcomingEmptyAmount(pct)}
                      />
                    </td>
                    <td className="px-2 py-2 align-top text-right">
                      <MetricCell
                        value={impact}
                        undisclosed={isUpcomingEmptyAmount(impact)}
                      />
                    </td>
                    <td className="px-2 py-2 align-top">
                      <DateCell value={row.announcedDate} />
                    </td>
                    <td className="px-2 py-2 align-top">
                      <DateCell value={row.recordDate} />
                    </td>
                    <td className="py-2 pl-2 align-top">
                      <DateCell value={row.exDate} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
      <p className="mt-2 text-[10px] text-faint">
        one row per ticker · manager unpaid $/share · % of NAV = $/share ÷ weekly
        NAV · $ tax impact = Dist $ × inputted rates · Announced / Record /
        Ex-date include year · payable is not a primary column · never invent
        {sideLabel ? ` · ${sideLabel}` : ""}
      </p>
    </section>
  );
}
