import { formatUsd } from "@/lib/format";
import type { TaxImpactBar } from "@/lib/illustrate/portfolio-compare-map";

export function TaxImpactChart({
  bars,
  headingId,
  totalTax,
  className = "",
}: {
  bars: TaxImpactBar[];
  headingId: string;
  /** Sum of this book's holdings[].upcoming.estimated_tax. */
  totalTax: number;
  className?: string;
}) {
  return (
    <section
      aria-labelledby={headingId}
      className={`flex flex-col rounded-2xl border border-line bg-surface p-3 shadow-[0_8px_24px_rgba(26,29,26,0.06)] sm:p-4 ${className}`}
    >
      <div className="mb-4">
        <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-faint">
          Total tax impact
        </p>
        <p className="mt-1 font-serif text-[28px] leading-tight tracking-tight text-ink tabular-nums">
          {formatUsd(Math.round(totalTax), 0)}
        </p>
      </div>
      <header className="mb-3 flex flex-wrap items-end justify-between gap-2">
        <h2
          id={headingId}
          className="font-serif text-lg tracking-tight text-ink"
        >
          Est. tax on upcoming
        </h2>
        <p className="text-[10px] text-muted">$ per fund · allocated</p>
      </header>

      {bars.length === 0 ? (
        <p className="py-6 text-center text-sm text-muted">
          No holdings to chart.
        </p>
      ) : (
        <div
          className="flex items-end gap-1.5 sm:gap-2"
          role="img"
          aria-label={bars
            .map(
              (bar) =>
                `${bar.ticker}: ${formatUsd(bar.taxDollars, 0)} estimated tax on upcoming`,
            )
            .join(". ")}
        >
          {bars.map((bar) => {
            const heightPct =
              bar.taxDollars <= 0 ? 2 : Math.max(8, bar.share * 100);
            return (
              <div
                key={bar.ticker}
                className="flex min-w-0 flex-1 flex-col items-center gap-1"
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
                <span
                  className="w-full truncate text-center font-mono text-[10px] leading-none text-ink"
                  title={bar.ticker}
                >
                  {bar.ticker}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
