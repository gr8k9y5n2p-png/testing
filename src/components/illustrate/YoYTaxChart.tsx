import { formatUsd } from "@/lib/format";
import {
  computeYoyLine,
  sortYoYPoints,
  type YoYTaxChartPoint,
} from "@/lib/illustrate/yoy-tax-chart";

export type YoYTaxChartProps = {
  bars: YoYTaxChartPoint[];
  /** Optional descending YoY tax line. Pass `true` to derive from `bars`. */
  line?: YoYTaxChartPoint[] | true;
  headingId?: string;
  title?: string;
  className?: string;
  valueFormat?: (value: number) => string;
};

function defaultFormat(value: number): string {
  return formatUsd(Math.round(value), 0);
}

export function YoYTaxChart({
  bars,
  line,
  headingId,
  title = "Tax by calendar year",
  className = "",
  valueFormat = defaultFormat,
}: YoYTaxChartProps) {
  const series = sortYoYPoints(bars);
  const yoyLine = line === true ? computeYoyLine(series) : line ? sortYoYPoints(line) : [];
  const showLine = yoyLine.some((point) => point.value != null);
  const maxBar = series.reduce((peak, point) => Math.max(peak, point.value ?? 0), 0);
  const lineValues = yoyLine.map((point) => point.value).filter((value): value is number => value != null);
  const maxLine = lineValues.reduce((peak, value) => Math.max(peak, Math.abs(value)), 0);

  const linePoints = series
    .map((bar, index) => {
      const yoy = yoyLine.find((point) => point.year === bar.year);
      if (yoy?.value == null || maxLine <= 0) return null;
      const x = series.length <= 1 ? 50 : (index / (series.length - 1)) * 100;
      const y = 50 - (yoy.value / maxLine) * 42;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .filter((point): point is string => point != null);

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
          {title}
        </h2>
        {showLine ? (
          <p className="text-[10px] text-muted">bars = tax · line = YoY Δ</p>
        ) : (
          <p className="text-[10px] text-muted">calendar year</p>
        )}
      </header>

      {series.length === 0 ? (
        <p className="py-6 text-center text-sm text-muted">No historical years to chart.</p>
      ) : (
        <div className="relative">
          {showLine && linePoints.length > 1 ? (
            <svg
              aria-hidden
              viewBox="0 0 100 100"
              preserveAspectRatio="none"
              className="pointer-events-none absolute inset-x-0 top-5 h-28 w-full"
            >
              <polyline
                fill="none"
                stroke="currentColor"
                strokeWidth="1.4"
                vectorEffect="non-scaling-stroke"
                className="text-ink/45"
                points={linePoints.join(" ")}
              />
            </svg>
          ) : null}
          <div
            className="relative flex h-40 items-end gap-1.5 sm:gap-2"
            role="img"
            aria-label={series
              .map((point) =>
                point.value == null
                  ? `${point.year}: not announced`
                  : `${point.year}: ${valueFormat(point.value)}`,
              )
              .join(". ")}
          >
            {series.map((point) => {
              const heightPct =
                point.value == null || maxBar <= 0
                  ? 4
                  : Math.max(8, (point.value / maxBar) * 100);
              return (
                <div
                  key={point.year}
                  className="flex min-w-0 flex-1 flex-col items-center gap-1"
                >
                  <span className="font-mono text-[10px] tabular-nums text-muted">
                    {point.value == null ? "—" : valueFormat(point.value)}
                  </span>
                  <div className="flex h-28 w-full items-end justify-center">
                    <div
                      className={`w-[68%] max-w-9 rounded-t-sm ${
                        point.value == null ? "bg-line" : "bg-ink/80"
                      }`}
                      style={{ height: `${heightPct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
          <ul className="mt-2 flex gap-1.5 sm:gap-2">
            {series.map((point) => (
              <li
                key={point.year}
                className="min-w-0 flex-1 text-center font-mono text-[10px] text-muted"
              >
                {point.year}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
