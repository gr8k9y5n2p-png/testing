import { niceMoneyScale } from "@/lib/charts/money-axis";
import {
  SHARED_CHART_PAD,
  SHARED_CHART_WIDTH,
  yearLayout,
  type ChartPad,
  type YearLayout,
} from "@/lib/charts/shared-axis";
import { isRemovableGrowthSeries } from "@/lib/illustrate/growth-selection";
import {
  TAX_DRAG_NA_LABEL,
  formatTaxDragPoint,
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
  emptyHint?: string;
  className?: string;
  /** @deprecated Friends beta never advertises SAMPLE. Prefer `live`. */
  sample?: boolean;
  /** True when the series came from the Data API. Mock / fixture stays blank. */
  live?: boolean;
  /** `down` draws negative bars from a 0% baseline at the top. */
  orientation?: "up" | "down";
  showBarLabels?: boolean;
  /** `flush` is the stacked homepage panel (no card chrome / max-width). */
  layout?: "card" | "flush";
  width?: number;
  height?: number;
  pad?: ChartPad;
  years?: number[];
  /** Shared x-scale with the growth chart. */
  axis?: YearLayout;
  /** Locked-sketch % / $ control on the tax-drag panel. */
  onUnitChange?: (metric: TaxDragMetric) => void;
  /** Remove a user-added fund. Benchmark series stay non-removable. */
  onRemoveSeries?: (id: string) => void;
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
  emptyHint = `Missing years stay ${TAX_DRAG_NA_LABEL} — Aftertax does not invent tax-drag rows.`,
  className = "",
  live = false,
  orientation = "up",
  showBarLabels = false,
  layout = "card",
  width,
  height,
  pad,
  years: yearsProp,
  axis: axisProp,
  onUnitChange,
  onRemoveSeries,
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

  // Years on a shared axis (or any period slots) still plot — unmatched
  // years are N/A gaps, not an empty “no overlapping years” card.
  if (years.length === 0) {
    return (
      <div
        className={
          flush
            ? `flex min-h-[160px] flex-col justify-center px-1 py-4 ${className}`
            : `flex min-h-[240px] w-full max-w-[420px] flex-col items-start justify-center rounded-2xl border border-dashed border-line-strong bg-surface px-5 py-6 ${className}`
        }
      >
        <p className="font-serif text-lg text-ink">{emptyLabel}</p>
        {emptyHint ? (
          <p className="mt-2 text-sm text-muted">{emptyHint}</p>
        ) : null}
      </div>
    );
  }

  const down = orientation === "down";
  const peak = down
    ? Math.min(...measured, 0)
    : Math.max(...measured, 0);
  const scale = niceScale(down ? Math.abs(peak) : peak, metric);
  const innerH = chartH - chartPad.top - chartPad.bottom;
  const axis =
    axisProp ?? yearLayout(years, fundSeries.length, chartW, chartPad);
  const barW = axis.barW;
  const labelBars = showBarLabels && axis.barW >= 12;

  const xAt = (index: number) => axis.center(index);
  const yAt = (value: number) => {
    if (scale === 0) return down ? chartPad.top : chartPad.top + innerH;
    if (down) {
      return chartPad.top + (Math.abs(value) / scale) * innerH;
    }
    return chartPad.top + innerH - (value / scale) * innerH;
  };

  const ticks = down
    ? taxTicks(-scale, metric)
    : [0, scale / 2, scale].filter((value, index, all) => all.indexOf(value) === index);
  const linePath = overlay ? polylinePath(overlay, years, xAt, yAt) : "";
  const zeroY = down ? chartPad.top : chartPad.top + innerH;

  const aria = years
    .map((year) => {
      const bits = fundSeries.map((row) => {
        const point = row.points.find((item) => item.year === year);
        return `${row.label}: ${formatTaxDragPoint(point?.value, metric)}`;
      });
      return `${year}: ${bits.join(", ")}`;
    })
    .join(". ");

  const plot = (
    <div role="img" aria-label={`${title}. ${aria}`}>
      <svg viewBox={`0 0 ${chartW} ${chartH}`} className="h-auto w-full" aria-hidden>
          {years.map((_, index) =>
            index === 0 ? null : (
              <line
                key={`year-gutter-${years[index]}`}
                x1={axis.slotLeft(index)}
                x2={axis.slotLeft(index)}
                y1={chartPad.top}
                y2={chartPad.top + innerH}
                className="stroke-line"
                strokeWidth={1}
                strokeDasharray="2 5"
              />
            ),
          )}

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
                  const naX = fundSeries.length > 1 ? x + barW / 2 : center;
                  const naY = down ? chartPad.top + 12 : chartPad.top + innerH - 6;
                  return (
                    <text
                      key={`${row.id}-na-${year}`}
                      x={naX}
                      y={naY}
                      textAnchor="middle"
                      className="fill-faint"
                      fontSize={barW < 10 ? 7 : 8}
                      fontFamily="ui-monospace, monospace"
                    >
                      {TAX_DRAG_NA_LABEL}
                    </text>
                  );
                }
                const endY = yAt(amount);
                const barY = down ? Math.min(zeroY, endY) : endY;
                const magnitude = Math.abs(endY - zeroY);
                // Genuine 0 still occupies the slot (hairline at baseline).
                const barH = amount === 0 ? 2 : Math.max(2, magnitude);
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
                    {labelBars ? (
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
        <header className="mb-2 flex flex-wrap items-end justify-between gap-3">
          <h3 className="text-[11px] font-semibold uppercase tracking-[0.16em] text-faint">
            {title}
          </h3>
          {fundSeries.length > 0 || upcomingSummary ? (
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
              <UpcomingChip summary={upcomingSummary} />
              <ul className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[12px] text-muted">
                {fundSeries.map((row) => (
                  <li key={row.id} className="flex items-center gap-1.5">
                    <span
                      className="inline-block size-2 rounded-[2px]"
                      style={{ background: row.color }}
                    />
                    <span className="text-ink">{row.label}</span>
                    {onRemoveSeries && isRemovableGrowthSeries(row.id) ? (
                      <button
                        type="button"
                        onClick={() => onRemoveSeries(row.id)}
                        className="rounded px-0.5 text-faint hover:bg-surface hover:text-ink"
                        aria-label={`Remove ${row.label}`}
                      >
                        ×
                      </button>
                    ) : null}
                  </li>
                ))}
                <li className="text-faint">
                  {metric === "effective_tax" ? "% of portfolio value" : "tax $"}
                  {" · "}
                  {TAX_DRAG_NA_LABEL} = unmatched
                </li>
              </ul>
              {onUnitChange ? (
                <div
                  className="inline-flex rounded-md border border-line bg-paper p-0.5 text-[11px] font-semibold"
                  role="group"
                  aria-label="Tax drag units"
                >
                  <button
                    type="button"
                    title="Effective tax on holding"
                    onClick={() => onUnitChange("effective_tax")}
                    className={`h-7 rounded px-2 ${
                      metric === "effective_tax" ? "bg-ink text-white" : "text-muted"
                    }`}
                  >
                    %
                  </button>
                  <button
                    type="button"
                    title="Estimated tax dollars"
                    onClick={() => onUnitChange("tax_dollars")}
                    className={`h-7 rounded px-2 ${
                      metric === "tax_dollars" ? "bg-ink text-white" : "text-muted"
                    }`}
                  >
                    $
                  </button>
                </div>
              ) : null}
            </div>
          ) : null}
        </header>
        {plot}
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
            Aftertax{live ? " · Live" : ""}
          </p>
          <h3 className="mt-2 font-serif text-lg tracking-tight text-ink">{title}</h3>
        </div>
        <UpcomingChip summary={upcomingSummary} />
      </header>
      <div className="mt-3">{plot}</div>
      <p className="mt-2 text-[10px] leading-relaxed text-faint">
        Calendar years · {metric === "tax_dollars" ? "tax $" : "effective tax %"} ·{" "}
        {TAX_DRAG_NA_LABEL} = unmatched year · 0 = no tax drag
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

function taxTicks(min: number, metric: TaxDragMetric): number[] {
  if (metric === "tax_dollars") {
    const { ticks } = niceMoneyScale(0, Math.abs(min), 0);
    return ticks.map((tick) => (tick === 0 ? 0 : -tick));
  }
  const floor = Math.min(min, 0);
  const step = Math.abs(floor) <= 0.02 ? 0.005 : Math.abs(floor) <= 0.04 ? 0.01 : Math.abs(floor) / 3;
  const ticks: number[] = [];
  for (let value = 0; value >= floor - 0.0001; value -= step) {
    ticks.push(Math.round(value * 1000) / 1000);
  }
  return ticks.length >= 2 ? ticks : [0, floor];
}

function niceScale(peak: number, metric: TaxDragMetric): number {
  if (peak <= 0) return metric === "effective_tax" ? 0.01 : 50;
  if (metric === "effective_tax") {
    const pct = peak * 100;
    const step = pct <= 1.5 ? 0.5 : 1;
    return (Math.ceil(pct / step) * step) / 100;
  }
  return niceMoneyScale(0, peak, 0).max;
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
