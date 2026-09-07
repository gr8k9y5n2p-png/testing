import { formatUsd } from "@/lib/format";
import type { TaxImpactBar } from "@/lib/illustrate/portfolio-compare-map";

export function TaxImpactChart({
  bars,
  headingId,
  className = "",
}: {
  bars: TaxImpactBar[];
  headingId: string;
  className?: string;
}) {
  const peak = bars.reduce((max, bar) => Math.max(max, bar.taxDollars), 0);

  return (
    <section
      aria-labelledby={headingId}
      className={`rounded-2xl border border-line bg-surface p-3 shadow-[0_8px_24px_rgba(26,29,26,0.06)] sm:p-4 ${className}`}
    >
      <header className="mb-3 flex flex-wrap items-end justify-between gap-2">
        <div>
          <h2
            id={headingId}
            className="font-serif text-lg tracking-tight text-ink"
          >
            Tax impact
          </h2>
          <p className="mt-0.5 text-[10px] text-muted">
            est. tax on upcoming · vs peers in this book
          </p>
        </div>
        {peak > 0 ? (
          <p className="font-mono text-[10px] text-faint">
            max {formatUsd(peak, 0)}
          </p>
        ) : null}
      </header>

      {bars.length === 0 ? (
        <p className="py-6 text-center text-sm text-muted">
          No holdings to chart.
        </p>
      ) : (
        <>
          <div
            className="flex h-40 items-end gap-1.5 sm:gap-2"
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
                  <div className="flex h-28 w-full items-end justify-center">
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
              );
            })}
          </div>

          <ul className="mt-3 flex flex-wrap gap-x-3 gap-y-1.5">
            {bars.map((bar) => (
              <li
                key={bar.ticker}
                className="flex items-center gap-1.5 font-mono text-[10px] text-ink"
              >
                <span
                  aria-hidden
                  className="size-2 shrink-0 rounded-[2px]"
                  style={{ backgroundColor: bar.color }}
                />
                {bar.ticker}
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
