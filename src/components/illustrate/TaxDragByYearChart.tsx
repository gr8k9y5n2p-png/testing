import {
  SHARED_CHART_PAD,
  SHARED_CHART_WIDTH,
  yearLayout,
  type ChartPad,
} from "@/lib/charts/shared-axis";
import {
  formatTaxDragValue,
  unionTaxDragYears,
  type TaxDragFundSeries,
  type TaxDragLinePoint,
  type TaxDragMetric,
  type TaxDragYearPoint,
  type UpcomingSummary,
} from "@/lib/illustrate/tax-drag-chart";

export type TaxDragByYearChartProps = {
  periods?: TaxDragYearPoint[];
  /** Multi-fund side-by-side bars. Colors should match growth lines. */
  series?: TaxDragFundSeries[];
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
  /** `down` draws negative bars from a 0% baseline at the top. */
  orientation?: "up" | "down";
  showBarLabels?: boolean;
  /** `flush` is the stacked homepage panel (no card chrome / max-width). */
  layout?: "card" | "flush";
  width?: number;
  height?: number;
  pad?: ChartPad;
  years?: number[];
};

const CARD_W = 360;
const CARD_H = 168;
const CARD_PAD = { top: 16, right: 12, bottom: 28, left: 44 };

export function TaxDragByYearChart({
  periods = [],
  series,
  metric = "tax_dollars",
  title = "Tax drag by year",
  lineSeries = null,
  showLine = false,
  upcomingSummary = null,
  loading = false,
  emptyLabel = "No calendar-year tax-drag rows",
  className = "",
  sample = false,
  orientation = "up",
  showBarLabels = false,
  layout = "card",
  width,
  height,
  pad,
  years: yearsProp,
}: TaxDragByYearChartProps) {
  const flush = layout === "flush";
  const chartW = width ?? (flush ? SHARED_CHART_WIDTH : CARD_W);
  const chartH = height ?? (flush ? 188 : CARD_H);
  const chartPad = pad ?? (flush ? SHARED_CHART_PAD : CARD_PAD);

  if (loading) {
    return (
      <div
        className={
          flush
            ? `min-h-[200px] w-full animate-pulse rounded-md bg-paper ${className}`
            : `min-h-[240px] w-full max-w-[420px] animate-pulse rounded-2xl border border-line bg-surface shadow-[0_8px_24px_rgba(26,29,26,0.08)] ${className}`
        }
        aria-busy
        aria-label="Loading tax drag by year"
      />
    );
  }

  const fundSeries: TaxDragFundSeries[] =
    series && series.length > 0
      ? series
      : [
          {
            id: "fund",
            label: title,
            color: "var(--tax-more)",
            points: [...periods].sort((a, b) => a.year - b.year),
          },
        ];

  const years =
    yearsProp && yearsProp.length > 0
      ? yearsProp
      : unionTaxDragYears(fundSeries);
  const overlay = lineSeries ?? (showLine && !series ? fundSeries[0]?.points : null);
  const measured = [
    ...fundSeries.flatMap((row) => row.points.map((point) => point.value)),
    ...(overlay ?? []).map((point) => point.value),
  ].filter((value): value is number => value != null && Number.isFinite(value));

  if (years.length === 0 || measured.length === 0) {
    return (
      <div
        className={
          flush
            ? `flex min-h-[160px] flex-col justify-center px-1 py-4 ${className}`
            : `flex min-h-[240px] w-full max-w-[420px] flex-col items-start justify-center rounded-2xl border border-dashed border-line-strong bg-surface px-5 py-6 ${className}`
        }
      >
        <p className="font-serif text-lg text-ink">{emptyLabel}</p>
        <p className="mt-2 text-sm text-muted">
          Missing years are skipped — Aftertax does not invent tax-drag rows.
        </p>
      </div>
    );
  }

  const down = orientation === "down";
  const peak = down
    ? Math.min(...measured, 0)
    : Math.max(...measured, 0);
  const scale = niceScale(down ? Math.abs(peak) : peak, metric);
  const innerH = chartH - chartPad.top - chartPad.bottom;
  const axis = yearLayout(years, fundSeries.length, chartW, chartPad);
  const barW = axis.barW;

  const xAt = (index: number) => axis.center(index);
  const yAt = (value: number) => {
    if (scale === 0) return down ? chartPad.top : chartPad.top + innerH;
    if (down) {
      return chartPad.top + (Math.abs(value) / scale) * innerH;
    }
    return chartPad.top + innerH - (value / scale) * innerH;
  };

  const ticks = down ? [0, -scale / 2, -scale] : [0, scale / 2, scale];
  const linePath = overlay ? polylinePath(overlay, years, xAt, yAt) : "";
  const zeroY = down ? chartPad.top : chartPad.top + innerH;

  const aria = years
    .map((year) => {
      const bits = fundSeries.map((row) => {
        const point = row.points.find((item) => item.year === year);
        return point?.value == null
          ? `${row.label}: no data`
          : `${row.label}: ${formatTaxDragValue(point.value, metric)}`;
      });
      return `${year}: ${bits.join(", ")}`;
    })
    .join(". ");

  const plot = (
    <div role="img" aria-label={`${title}. ${aria}`}>
      <svg viewBox={`0 0 ${chartW} ${chartH}`} className="h-auto w-full" aria-hidden>
        {ticks.map((tick) => {
          const y = yAt(tick);
          return (
            <g key={tick}>
              <line
                x1={chartPad.left}
                x2={chartW - chartPad.right}
                y1={y}
                y2={y}
                className="stroke-line"
                strokeWidth={1}
              />
              <text
                x={chartPad.left - 6}
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

        {years.map((year, index) => {
          const center = xAt(index);
          return (
            <g key={year}>
              {fundSeries.map((row, seriesIndex) => {
                const point = row.points.find((item) => item.year === year);
                const amount = point?.value ?? null;
                const gap = amount == null;
                const x = axis.barX(index, seriesIndex);
                if (gap) {
                  return seriesIndex === 0 ? (
                    <line
                      key={`${row.id}-gap`}
                      x1={center}
                      x2={center}
                      y1={chartPad.top + 8}
                      y2={chartPad.top + innerH}
                      className="stroke-line-strong"
                      strokeWidth={1}
                      strokeDasharray="3 3"
                    />
                  ) : null;
                }
                const endY = yAt(amount);
                const barY = down ? Math.min(zeroY, endY) : endY;
                const barH = Math.max(2, Math.abs(endY - zeroY));
                const labelY = down ? endY + 11 : endY - 5;
                return (
                  <g key={`${row.id}-${year}`}>
                    <rect
                      x={x}
                      y={barY}
                      width={barW}
                      height={barH}
                      rx={2}
                      fill={row.color}
                      fillOpacity={0.88}
                    />
                    {showBarLabels ? (
                      <text
                        x={x + barW / 2}
                        y={labelY}
                        textAnchor="middle"
                        fill={row.color}
                        fontSize={8}
                        fontFamily="ui-monospace, monospace"
                      >
                        {formatTaxDragValue(amount, metric)}
                      </text>
                    ) : null}
                  </g>
                );
              })}
              <text
                x={center}
                y={chartH - 8}
                textAnchor="middle"
                className="fill-muted"
                fontSize={10}
                fontFamily="ui-monospace, monospace"
              >
                {year}
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
              const index = years.findIndex((year) => year === point.year);
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
  );

  if (flush) {
    return (
      <section className={`w-full ${className}`}>
        <header className="mb-2">
          <h3 className="text-[11px] font-semibold uppercase tracking-[0.16em] text-faint">
            {title}
          </h3>
        </header>
        {plot}
        {fundSeries.length > 0 ? (
          <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-muted">
            {fundSeries.map((row) => (
              <li key={row.id} className="flex items-center gap-1.5">
                <span
                  className="inline-block size-2 rounded-[2px]"
                  style={{ background: row.color }}
                />
                <span>
                  {row.label}
                  {row.description ? (
                    <span className="text-faint"> · {row.description}</span>
                  ) : null}
                </span>
              </li>
            ))}
          </ul>
        ) : null}
      </section>
    );
  }

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
      <div className="mt-3">{plot}</div>
      <p className="mt-2 text-[10px] leading-relaxed text-faint">
        Calendar years · {metric === "tax_dollars" ? "tax $" : "effective tax %"} ·
        gaps stay empty
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
  years: number[],
  xAt: (index: number) => number,
  yAt: (value: number) => number,
): string {
  const chunks: string[] = [];
  let drawing = false;
  for (const point of series) {
    const index = years.findIndex((year) => year === point.year);
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
