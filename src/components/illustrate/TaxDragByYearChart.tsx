import {
  formatTaxDragValue,
  type TaxDragLinePoint,
  type TaxDragMetric,
  type TaxDragYearPoint,
  type UpcomingSummary,
} from "@/lib/illustrate/tax-drag-chart";

export type TaxDragByYearChartProps = {
  periods: TaxDragYearPoint[];
  metric?: TaxDragMetric;
  title?: string;
  /** Same-unit overlay; gaps break the polyline (no interpolation). */
  lineSeries?: TaxDragLinePoint[] | null;
  /** When true, overlay `periods` as the descending YoY tax line. */
  showLine?: boolean;
  upcomingSummary?: UpcomingSummary | null;
  loading?: boolean;
  emptyLabel?: string;
  className?: string;
  sample?: boolean;
};

const CHART_W = 360;
const CHART_H = 168;
const PAD = { top: 16, right: 12, bottom: 28, left: 44 };

export function TaxDragByYearChart({
  periods,
  metric = "tax_dollars",
  title = "Tax drag by year",
  lineSeries = null,
  showLine = false,
  upcomingSummary = null,
  loading = false,
  emptyLabel = "No calendar-year tax-drag rows",
  className = "",
  sample = false,
}: TaxDragByYearChartProps) {
  if (loading) {
    return (
      <div
        className={`min-h-[240px] w-full max-w-[420px] animate-pulse rounded-2xl border border-line bg-surface shadow-[0_8px_24px_rgba(26,29,26,0.08)] ${className}`}
        aria-busy
        aria-label="Loading tax drag by year"
      />
    );
  }

  const years = [...periods].sort((a, b) => a.year - b.year);
  const overlay = lineSeries ?? (showLine ? years : null);
  const measured = [
    ...years.map((point) => point.value),
    ...(overlay ?? []).map((point) => point.value),
  ].filter((value): value is number => value != null && Number.isFinite(value));

  if (years.length === 0 || measured.length === 0) {
    return (
      <div
        className={`flex min-h-[240px] w-full max-w-[420px] flex-col items-start justify-center rounded-2xl border border-dashed border-line-strong bg-surface px-5 py-6 ${className}`}
      >
        <p className="font-serif text-lg text-ink">{emptyLabel}</p>
        <p className="mt-2 text-sm text-muted">
          Missing years are skipped — Aftertax does not invent tax-drag rows.
        </p>
      </div>
    );
  }

  const peak = Math.max(...measured, 0);
  const scale = niceScale(peak, metric);
  const innerW = CHART_W - PAD.left - PAD.right;
  const innerH = CHART_H - PAD.top - PAD.bottom;
  const slot = years.length > 0 ? innerW / years.length : innerW;
  const barW = Math.min(28, Math.max(10, slot * 0.48));

  const xAt = (index: number) => PAD.left + slot * index + slot / 2;
  const yAt = (value: number) =>
    PAD.top + innerH - (scale === 0 ? 0 : (value / scale) * innerH);

  const ticks = [0, scale / 2, scale];
  const linePath = overlay ? polylinePath(overlay, years, xAt, yAt) : "";

  const aria = years
    .map((point) =>
      point.value == null
        ? `${point.year}: no data`
        : `${point.year}: ${formatTaxDragValue(point.value, metric)}`,
    )
    .join(". ");

  return (
    <article
      className={`flex w-full max-w-[420px] flex-col rounded-2xl border border-line bg-surface px-5 py-5 shadow-[0_8px_24px_rgba(26,29,26,0.08)] ${className}`}
    >
      <header className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-faint">
            <span aria-hidden className="inline-block size-1.5 rounded-full bg-tax-less" />
            Aftertax{sample ? " · Sample" : ""}
          </p>
          <h3 className="mt-2 font-serif text-lg tracking-tight text-ink">{title}</h3>
        </div>
        <UpcomingChip summary={upcomingSummary} />
      </header>

      <div
        className="mt-3"
        role="img"
        aria-label={`${title}. ${aria}`}
      >
        <svg
          viewBox={`0 0 ${CHART_W} ${CHART_H}`}
          className="h-auto w-full"
          aria-hidden
        >
          {ticks.map((tick) => {
            const y = yAt(tick);
            return (
              <g key={tick}>
                <line
                  x1={PAD.left}
                  x2={CHART_W - PAD.right}
                  y1={y}
                  y2={y}
                  className="stroke-line"
                  strokeWidth={1}
                />
                <text
                  x={PAD.left - 6}
                  y={y + 3}
                  textAnchor="end"
                  className="fill-faint"
                  fontSize={9}
                  fontFamily="ui-monospace, monospace"
                >
                  {formatTaxDragValue(tick, metric)}
                </text>
              </g>
            );
          })}

          {years.map((point, index) => {
            const x = xAt(index);
            const amount = point.value;
            const gap = amount == null;
            const height = gap ? 0 : Math.max(2, innerH - (yAt(amount) - PAD.top));
            const y = gap ? PAD.top + innerH : yAt(amount);
            return (
              <g key={point.year}>
                {gap ? (
                  <line
                    x1={x}
                    x2={x}
                    y1={PAD.top + 8}
                    y2={PAD.top + innerH}
                    className="stroke-line-strong"
                    strokeWidth={1}
                    strokeDasharray="3 3"
                  />
                ) : (
                  <rect
                    x={x - barW / 2}
                    y={y}
                    width={barW}
                    height={height}
                    rx={3}
                    className="fill-tax-more-soft"
                  />
                )}
                <text
                  x={x}
                  y={CHART_H - 8}
                  textAnchor="middle"
                  className="fill-muted"
                  fontSize={10}
                  fontFamily="ui-monospace, monospace"
                >
                  {point.year}
                </text>
              </g>
            );
          })}

          {linePath ? (
            <path
              d={linePath}
              fill="none"
              className="stroke-ink"
              strokeWidth={1.75}
              strokeLinejoin="round"
              strokeLinecap="round"
            />
          ) : null}

          {overlay
            ? overlay.map((point) => {
                if (point.value == null) return null;
                const index = years.findIndex((row) => row.year === point.year);
                if (index < 0) return null;
                return (
                  <circle
                    key={`line-${point.year}`}
                    cx={xAt(index)}
                    cy={yAt(point.value)}
                    r={3}
                    className="fill-ink"
                  />
                );
              })
            : null}
        </svg>
      </div>

      <p className="mt-2 text-[10px] leading-relaxed text-faint">
        Calendar years · {metric === "tax_dollars" ? "tax $" : "effective tax %"} ·
        gaps stay empty · line is observed YoY tax
        {sample ? " · demo" : ""}
      </p>
    </article>
  );
}

/** Alias kept for Website Engineering drop-in. */
export const TaxYoYChart = TaxDragByYearChart;

function UpcomingChip({ summary }: { summary: UpcomingSummary | null | undefined }) {
  if (!summary) return null;
  const announced = summary.announced;
  const text =
    summary.label ??
    (announced
      ? summary.dollars != null
        ? `Upcoming · ${formatTaxDragValue(summary.dollars, "tax_dollars")}`
        : "Upcoming"
      : "Not announced");

  return (
    <span
      className={`mt-1 inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-medium ${
        announced
          ? "bg-tax-more-soft text-tax-more"
          : "bg-paper text-muted ring-1 ring-line"
      }`}
    >
      {text}
    </span>
  );
}

function niceScale(peak: number, metric: TaxDragMetric): number {
  if (peak <= 0) return metric === "effective_tax" ? 0.01 : 50;
  if (metric === "effective_tax") {
    const pct = peak * 100;
    const step = pct <= 1 ? 0.5 : 1;
    return (Math.ceil(pct / step) * step) / 100;
  }
  const step = peak <= 100 ? 25 : 50;
  return Math.ceil(peak / step) * step;
}

function polylinePath(
  series: TaxDragLinePoint[],
  years: TaxDragYearPoint[],
  xAt: (index: number) => number,
  yAt: (value: number) => number,
): string {
  const chunks: string[] = [];
  let drawing = false;
  for (const point of series) {
    const index = years.findIndex((row) => row.year === point.year);
    if (index < 0 || point.value == null) {
      drawing = false;
      continue;
    }
    const command = drawing ? "L" : "M";
    chunks.push(`${command}${xAt(index).toFixed(1)},${yAt(point.value).toFixed(1)}`);
    drawing = true;
  }
  return chunks.join(" ");
}
