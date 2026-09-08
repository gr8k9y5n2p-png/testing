import { TickerHistoryLink } from "@/components/illustrate/TickerHistoryLink";
import { formatUsd } from "@/lib/format";
import {
  UPCOMING_MODULE_DETAIL,
  UPCOMING_UNAVAILABLE_DETAIL,
  UPCOMING_UNAVAILABLE_HEADLINE,
} from "@/lib/illustrate/portfolio-compare-copy";
import type { TaxImpactBar } from "@/lib/illustrate/portfolio-compare-map";

export function TaxImpactChart({
  bars,
  headingId,
  totalTax,
  hasUpcoming = true,
  className = "",
}: {
  bars: TaxImpactBar[];
  headingId: string;
  /** Sum of this book's holdings[].upcoming.estimated_tax. */
  totalTax: number;
  /** False when there are no unpaid announced rows — do not render $0. */
  hasUpcoming?: boolean;
  className?: string;
}) {
  const unavailable = !hasUpcoming;

  return (
    <section
      aria-labelledby={headingId}
      className={`flex flex-col rounded-2xl border border-line bg-surface p-3 shadow-[0_8px_24px_rgba(26,29,26,0.06)] sm:p-4 ${className}`}
    >
      <header className="mb-3 flex flex-wrap items-end justify-between gap-2">
        <h2 id={headingId} className="font-serif text-lg tracking-tight text-ink">
          Total tax impact
        </h2>
        <p className="text-[10px] text-muted">{UPCOMING_MODULE_DETAIL}</p>
      </header>

      <div className="rounded-xl border border-line bg-surface px-3 py-2">
        <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-ink">
          Upcoming tax to holder
        </p>
        {unavailable ? (
          <>
            <p className="mt-1 font-serif text-[22px] leading-tight tracking-tight text-ink">
              {UPCOMING_UNAVAILABLE_HEADLINE}
            </p>
            <p className="mt-1 text-[11px] text-muted">{UPCOMING_UNAVAILABLE_DETAIL}</p>
          </>
        ) : (
          <p className="mt-1 font-serif text-[28px] leading-tight tracking-tight text-ink tabular-nums">
            {formatUsd(Math.round(totalTax), 0)}
          </p>
        )}
      </div>

      {unavailable ? (
        <div
          className="mt-3 min-h-28 rounded-lg border border-dashed border-line bg-paper"
          aria-hidden
        />
      ) : bars.length === 0 ? (
        <p className="py-6 text-center text-sm text-muted">No holdings to chart.</p>
      ) : (
        <div className="mt-3 flex items-end gap-1.5 sm:gap-2">
          {bars.map((bar) => {
            const heightPct = bar.taxDollars <= 0 ? 2 : Math.max(8, bar.share * 100);
            return (
              <div
                key={bar.ticker}
                className="flex min-w-0 flex-1 flex-col items-center gap-1"
              >
                <div
                  className="flex w-full flex-col items-center gap-1"
                  role="img"
                  aria-label={`${bar.ticker}: ${formatUsd(bar.taxDollars, 0)} estimated tax on upcoming`}
                >
                  <span className="font-mono text-[10px] tabular-nums text-muted">
                    {formatUsd(bar.taxDollars, 0)}
                  </span>
                  <div className="flex h-28 w-full items-end justify-center border-b border-line">
                    <div
                      title={`${bar.ticker}: ${formatUsd(bar.taxDollars, 0)}`}
                      className="w-[68%] max-w-9 rounded-t-sm"
                      style={{
                        height: `${heightPct}%`,
                        backgroundColor: bar.color,
                      }}
                    />
                  </div>
                </div>
                <TickerHistoryLink
                  ticker={bar.ticker}
                  className="w-full truncate text-center font-mono text-[10px] leading-none"
                />
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
