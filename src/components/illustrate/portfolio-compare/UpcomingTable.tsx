import { DistributionDateStrip } from "@/components/DistributionDateStrip";
import { TickerHistoryLink } from "@/components/illustrate/TickerHistoryLink";
import { ENTER_NAV_COPY } from "@/lib/illustrate/illustrate-error";
import {
  DIST_AMOUNT_COLUMN,
  DOLLAR_IMPACT_COLUMN,
  PCT_OF_NAV_COLUMN,
  UPCOMING_AMOUNT_UNAVAILABLE,
  UPCOMING_MODULE_DETAIL,
  UPCOMING_MODULE_HEADING,
  UPCOMING_UNAVAILABLE_DETAIL,
  UPCOMING_UNAVAILABLE_HEADLINE,
  upcomingDistributionAmount,
  upcomingDollarImpactAmount,
  upcomingPctOfNavAmount,
  upcomingPerShareAmount,
} from "@/lib/illustrate/portfolio-compare-copy";
import type { UpcomingRow } from "@/lib/illustrate/portfolio-compare-map";

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
    <div className="min-w-[8rem] max-w-[16rem]">
      <div className="font-mono text-[13px] font-medium text-ink">
        <TickerHistoryLink ticker={row.ticker} />
      </div>
      {row.fundName && row.fundName !== row.ticker ? (
        <p className="mt-0.5 truncate text-[11px] leading-snug text-muted">
          {row.fundName}
        </p>
      ) : null}
      <DistributionDateStrip
        fund={{
          asOfDate: row.announcedDate ?? "",
          recordDate: row.recordDate,
          exDate: row.exDate,
          payableDate: row.payableDate,
          publicationStage: row.stage,
          bucket: "upcoming",
        }}
        showPayable={Boolean(row.payableDate)}
        className="mt-1"
      />
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
                <th className="px-2 py-1.5 text-right">{DIST_AMOUNT_COLUMN}</th>
                <th className="px-2 py-1.5 text-right">{PCT_OF_NAV_COLUMN}</th>
                <th className="py-1.5 pl-2 text-right">{DOLLAR_IMPACT_COLUMN}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const dist = upcomingDistributionAmount(row);
                const perShare = upcomingPerShareAmount(row);
                const pct = upcomingPctOfNavAmount(row);
                const impact = upcomingDollarImpactAmount(row);
                const needNav =
                  row.available &&
                  row.distributionDollars != null &&
                  perShare == null;
                return (
                  <tr key={row.key} className="border-b border-line last:border-0">
                    <td className="py-2 pr-3 align-top">
                      <TickerCell row={row} />
                    </td>
                    <td className="px-2 py-2 align-top text-right">
                      <MetricCell
                        value={dist}
                        undisclosed={dist === UPCOMING_AMOUNT_UNAVAILABLE}
                      />
                      {perShare ? (
                        <span className="mt-0.5 block font-mono text-[11px] tabular-nums text-muted">
                          {perShare}
                        </span>
                      ) : needNav ? (
                        <span className="mt-0.5 block text-[10px] leading-snug text-muted">
                          {ENTER_NAV_COPY}
                        </span>
                      ) : null}
                    </td>
                    <td className="px-2 py-2 align-top text-right">
                      <MetricCell
                        value={pct}
                        undisclosed={pct === UPCOMING_AMOUNT_UNAVAILABLE}
                      />
                    </td>
                    <td className="py-2 pl-2 align-top text-right">
                      <MetricCell
                        value={impact}
                        undisclosed={impact === "N/A"}
                      />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
      <p className="mt-2 text-[10px] text-faint">
        every fund · Dist $ + $ / share · issuer % of NAV · $ impact ·
        empty upcoming is undisclosed, not $0 · Announced / Record / Ex /
        Payable include year
        {sideLabel ? ` · ${sideLabel}` : ""}
      </p>
    </section>
  );
}
