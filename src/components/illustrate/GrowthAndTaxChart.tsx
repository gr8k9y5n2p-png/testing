"use client";

import { useId } from "react";
import { END_LABEL_MIN_GAP, staggerEndLabels } from "@/lib/charts/end-labels";
import {
  AXIS_LABEL_GAP_PX,
  growthTaxBarCenter,
  growthTaxBarWidth,
  growthTaxBarX,
  growthTaxChartPad,
  startAmountLabel,
  startAmountLabelX,
  underBarTickerFontSize,
  underBarTickerLabel,
} from "@/lib/charts/growth-tax-layout";
import { formatCompactUsd, niceMoneyScale } from "@/lib/charts/money-axis";
import {
  SHARED_CHART_WIDTH,
  yearLayout,
  type ChartPad,
  type YearLayout,
} from "@/lib/charts/shared-axis";
import { formatUsd } from "@/lib/format";
import { isRemovableGrowthSeries } from "@/lib/illustrate/growth-selection";
import type { GrowthLineSeries } from "@/lib/illustrate/growth-tax-series";
import {
  GROWTH_TAX_ESTIMATE_TYPES,
  GROWTH_TAX_TYPE_COLORS,
  GROWTH_TAX_TYPE_LABELS,
  formatGrowthTaxCell,
  lightenHex,
  type GrowthTaxByTypeModel,
} from "@/lib/illustrate/growth-tax-by-type";

export type GrowthAndTaxChartProps = {
  years: number[];
  growthSeries: GrowthLineSeries[];
  taxModel: GrowthTaxByTypeModel;
  startDollars: number;
  loading?: boolean;
  className?: string;
  pad?: ChartPad;
  axis?: YearLayout;
  emptyLabel?: string;
  emptyHint?: string;
  onRemoveSeries?: (id: string) => void;
  annualized?: { id: string; value: number | null }[];
};

const GROWTH_H = 220;
const TAX_H = 188;
const ZERO_GAP = 10;

export function GrowthAndTaxChart({
  years,
  growthSeries,
  taxModel,
  startDollars,
  loading = false,
  className = "",
  pad: padProp,
  axis: axisProp,
  emptyLabel = "No fund series",
  emptyHint = "",
  onRemoveSeries,
  annualized = [],
}: GrowthAndTaxChartProps) {
  const hatchId = useId().replace(/:/g, "");

  if (loading) {
    return (
      <div
        className={`min-h-[360px] w-full animate-pulse rounded-md bg-paper ${className}`}
        aria-busy
        aria-label="Loading growth and tax"
      />
    );
  }

  const growthValues = growthSeries.flatMap((row) => row.points.map((point) => point.value));
  if (years.length === 0) {
    return (
      <div className={`flex min-h-[200px] flex-col justify-center py-4 ${className}`}>
        <p className="font-serif text-lg text-ink">{emptyLabel}</p>
        {emptyHint ? <p className="mt-2 text-sm text-muted">{emptyHint}</p> : null}
      </div>
    );
  }

  const width = SHARED_CHART_WIDTH;
  const pad = padProp ?? growthTaxChartPad(startDollars);
  const axis = axisProp ?? yearLayout(years, Math.max(taxModel.tickers.length, 1), width, pad);
  const startLabel = startAmountLabel(startDollars);
  const startLabelX = startAmountLabelX(pad.left);
  const growthInner = GROWTH_H - pad.top - ZERO_GAP;
  const taxInner = TAX_H - pad.bottom - ZERO_GAP;
  const zeroY = pad.top + growthInner;
  const height = zeroY + ZERO_GAP + taxInner + pad.bottom;

  const lo = growthValues.length
    ? Math.min(startDollars, ...growthValues)
    : startDollars;
  const hi = growthValues.length
    ? Math.max(startDollars, ...growthValues)
    : startDollars * 1.2;
  const growthScale = niceMoneyScale(lo, hi, startDollars);
  const taxPeak = Math.max(
    0,
    ...taxModel.series.flatMap((row) =>
      row.years.map((year) => (year.total == null ? 0 : Math.abs(year.total))),
    ),
  );
  const taxScale = niceMoneyScale(
    0,
    Math.max(taxPeak, taxModel.unit === "per_share" ? 1 : 50),
    0,
  );

  const xCenter = (index: number) => axis.center(index);
  const growthY = (value: number) => {
    const span = growthScale.max - growthScale.min || 1;
    return pad.top + growthInner - ((value - growthScale.min) / span) * growthInner;
  };
  const taxY = (value: number) => {
    const span = taxScale.max || 1;
    return zeroY + ZERO_GAP + (Math.abs(value) / span) * taxInner;
  };

  const lastYear = years[years.length - 1];
  const fundSeries = growthSeries.filter((row) => !row.dashed);
  const endLabels = placeGrowthEndLabels({
    fundSeries,
    lastYear,
    xAt: (year) => {
      const index = years.indexOf(year);
      return xCenter(index < 0 ? 0 : index);
    },
    yAt: growthY,
    minY: pad.top + 8,
    maxY: zeroY - 4,
  });

  const aria = years
    .map((year, index) => {
      const bits = taxModel.series.map((row) => {
        const cell = row.years[index];
        const total = cell?.total;
        const mark = cell?.status === "announced" ? " announced unpaid" : "";
        return `${row.ticker}: ${total == null ? "undisclosed" : formatUsd(total, 0)}${mark}`;
      });
      return `${year}: ${bits.join(", ")}`;
    })
    .join(". ");

  return (
    <section className={`w-full ${className}`}>
      <header className="mb-2 flex flex-wrap items-end justify-between gap-3">
        <h3 className="text-[11px] font-semibold uppercase tracking-[0.16em] text-faint">
          Growth ({formatUsd(startDollars, 0)})
        </h3>
        <ul className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[12px] text-ink">
          {fundSeries.map((row) => {
            const ann = annualized.find((item) => item.id === row.id);
            return (
            <li key={row.id} className="flex items-center gap-1.5">
              <span
                className="inline-block h-px w-4"
                style={{ background: row.color }}
              />
              <span className="font-medium">{row.label}</span>
              {onRemoveSeries && isRemovableGrowthSeries(row.id, row.dashed) ? (
                <button
                  type="button"
                  onClick={() => onRemoveSeries(row.id)}
                  className="rounded px-0.5 text-faint hover:bg-surface hover:text-ink"
                  aria-label={`Remove ${row.label}`}
                >
                  ×
                </button>
              ) : null}
              {ann?.value != null ? (
                <span
                  className="inline-flex items-center rounded-full bg-paper px-2 py-0.5 text-[10px] font-medium"
                  style={{ color: row.color }}
                >
                  {(ann.value * 100).toFixed(1)}% ann.
                </span>
              ) : null}
            </li>
            );
          })}
        </ul>
      </header>

      <div role="img" aria-label={`Growth and tax. ${aria}`} className="min-h-[280px]">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="h-auto w-full"
          preserveAspectRatio="xMidYMid meet"
          aria-hidden
        >
          <defs>
            <clipPath id={`gt-plot-${hatchId}`}>
              <rect
                x={pad.left}
                y={pad.top}
                width={Math.max(1, width - pad.left - pad.right)}
                height={Math.max(1, height - pad.top - pad.bottom)}
              />
            </clipPath>
            <pattern
              id={`gt-hatch-${hatchId}`}
              width="5"
              height="5"
              patternUnits="userSpaceOnUse"
              patternTransform="rotate(45)"
            >
              <rect width="5" height="5" fill="white" fillOpacity="0.2" />
              <line x1="0" y1="0" x2="0" y2="5" stroke="white" strokeWidth="1.35" />
            </pattern>
          </defs>

          {years.map((_, index) =>
            index === 0 ? null : (
              <line
                key={`gutter-${years[index]}`}
                x1={axis.slotLeft(index)}
                x2={axis.slotLeft(index)}
                y1={pad.top}
                y2={zeroY + ZERO_GAP + taxInner}
                className="stroke-line"
                strokeWidth={1}
                strokeDasharray="2 5"
              />
            ),
          )}

          {growthScale.ticks.map((tick) => {
            const y = growthY(tick);
            const isStart = Math.abs(tick - startDollars) < 1e-6;
            return (
              <g key={`g-${tick}`}>
                <line
                  x1={pad.left}
                  x2={width - pad.right}
                  y1={y}
                  y2={y}
                  className="stroke-line"
                  strokeWidth={1}
                />
                {isStart ? null : (
                  <text
                    x={pad.left - AXIS_LABEL_GAP_PX}
                    y={y + 3}
                    textAnchor="end"
                    className="fill-faint"
                    fontSize={9}
                    fontFamily="ui-monospace, monospace"
                  >
                    {formatCompactUsd(tick)}
                  </text>
                )}
              </g>
            );
          })}

          <text
            data-start-label
            data-start-x={startLabelX.toFixed(1)}
            x={startLabelX}
            y={growthY(startDollars) + 3}
            textAnchor="end"
            className="fill-faint"
            fontSize={9}
            fontFamily="ui-monospace, monospace"
          >
            {startLabel}
          </text>

          {taxScale.ticks
            .filter((tick) => tick > 0)
            .map((tick) => {
              const y = taxY(tick);
              return (
                <g key={`t-${tick}`}>
                  <line
                    x1={pad.left}
                    x2={width - pad.right}
                    y1={y}
                    y2={y}
                    className="stroke-line"
                    strokeWidth={1}
                  />
                  <text
                    x={pad.left - AXIS_LABEL_GAP_PX}
                    y={y + 3}
                    textAnchor="end"
                    className="fill-faint"
                    fontSize={9}
                    fontFamily="ui-monospace, monospace"
                  >
                    {taxModel.unit === "per_share"
                      ? formatGrowthTaxCell(-tick, "paid", "type", "per_share")
                      : formatCompactUsd(-tick)}
                  </text>
                </g>
              );
            })}

          <line
            x1={pad.left}
            x2={width - pad.right}
            y1={zeroY}
            y2={zeroY}
            className="stroke-ink"
            strokeWidth={1.15}
          />
          <text
            x={pad.left - AXIS_LABEL_GAP_PX}
            y={zeroY + 3}
            textAnchor="end"
            className="fill-faint"
            fontSize={9}
            fontFamily="ui-monospace, monospace"
          >
            $0
          </text>

          <g clipPath={`url(#gt-plot-${hatchId})`}>
          {fundSeries.map((row) => {
            const d = polyline(row.points, years, xCenter, growthY);
            if (!d) return null;
            const last = row.points[row.points.length - 1];
            const lastIndex = last ? years.indexOf(last.year) : -1;
            return (
              <g key={row.id}>
                <path
                  d={d}
                  fill="none"
                  stroke={row.color}
                  strokeWidth={1.75}
                  strokeLinejoin="round"
                  strokeLinecap="round"
                />
                {last && lastIndex >= 0 ? (
                  <circle
                    cx={xCenter(lastIndex)}
                    cy={growthY(last.value)}
                    r={3.2}
                    fill={row.color}
                  />
                ) : null}
              </g>
            );
          })}
          </g>

          {endLabels.map((label) => {
            const leader = Math.abs(label.labelY - label.y) > 6;
            return (
              <g key={`end-${label.id}`}>
                {leader ? (
                  <path
                    d={`M${label.x.toFixed(1)},${label.y.toFixed(1)} L${(label.x + 5).toFixed(1)},${label.labelY.toFixed(1)}`}
                    fill="none"
                    stroke={label.color}
                    strokeWidth={0.75}
                    opacity={0.55}
                  />
                ) : null}
                <text
                  x={label.x + 8}
                  y={label.labelY + 3}
                  fill={label.color}
                  fontSize={10}
                  fontFamily="ui-monospace, monospace"
                  fontWeight={500}
                >
                  {label.text}
                </text>
              </g>
            );
          })}

          {years.map((year, yearIndex) =>
            taxModel.series.map((row, seriesIndex) => {
              const cell = row.years[yearIndex];
              if (!cell || cell.total == null || cell.total === 0) return null;
              const x = growthTaxBarX(axis.barX(yearIndex, seriesIndex), axis.barW);
              const barW = growthTaxBarWidth(axis.barW);
              let cursor = zeroY + ZERO_GAP;
              const segments = GROWTH_TAX_ESTIMATE_TYPES.flatMap((type) => {
                const value = cell.amounts[type];
                if (value == null || value <= 0) return [];
                return [{ type, value }];
              });
              return (
                <g key={`${row.ticker}-${year}`}>
                  {segments.map((segment) => {
                    const h = Math.max(
                      1.5,
                      (segment.value / (taxScale.max || 1)) * taxInner,
                    );
                    const y = cursor;
                    cursor += h;
                    const fill =
                      cell.status === "announced"
                        ? lightenHex(GROWTH_TAX_TYPE_COLORS[segment.type])
                        : GROWTH_TAX_TYPE_COLORS[segment.type];
                    return (
                      <g key={`${row.ticker}-${year}-${segment.type}`}>
                        <rect
                          x={x}
                          y={y}
                          width={barW}
                          height={h}
                          fill={fill}
                          fillOpacity={cell.status === "announced" ? 0.92 : 0.94}
                        />
                        {cell.status === "announced" ? (
                          <rect
                            x={x}
                            y={y}
                            width={barW}
                            height={h}
                            fill={`url(#gt-hatch-${hatchId})`}
                          />
                        ) : null}
                      </g>
                    );
                  })}
                </g>
              );
            }),
          )}

          {years.map((year, yearIndex) =>
            taxModel.series.map((row, seriesIndex) => {
              const x = growthTaxBarCenter(axis.barX(yearIndex, seriesIndex), axis.barW);
              const fontSize = underBarTickerFontSize(axis.count);
              const label = underBarTickerLabel(row.ticker, axis.barW, fontSize);
              return (
                <text
                  key={`bar-ticker-${year}-${row.ticker}`}
                  data-bar-ticker={row.ticker}
                  data-bar-year={year}
                  data-bar-x={x.toFixed(1)}
                  x={x}
                  y={height - 36}
                  textAnchor="middle"
                  className="fill-ink"
                  fontSize={fontSize}
                  fontFamily="ui-monospace, monospace"
                >
                  <title>{row.ticker}</title>
                  {label}
                </text>
              );
            }),
          )}

          {years.map((year, index) => (
            <text
              key={year}
              data-year-label={year}
              x={xCenter(index)}
              y={height - 12}
              textAnchor="middle"
              className="fill-ink"
              fontSize={11}
              fontFamily="ui-monospace, monospace"
            >
              {year}
            </text>
          ))}
        </svg>
      </div>
    </section>
  );
}

export function GrowthTaxTypeLegend({ className = "" }: { className?: string }) {
  return (
    <ul
      className={`flex flex-wrap items-center justify-center gap-x-4 gap-y-1.5 text-[11px] text-muted ${className}`}
    >
      {GROWTH_TAX_ESTIMATE_TYPES.map((type) => (
        <li key={type} className="flex items-center gap-1.5">
          <span
            className="inline-block size-2 rounded-[2px]"
            style={{ background: GROWTH_TAX_TYPE_COLORS[type] }}
          />
          {GROWTH_TAX_TYPE_LABELS[type]}
        </li>
      ))}
      <li className="flex items-center gap-1.5">
        <span
          aria-hidden
          className="inline-block size-2.5 rounded-[2px]"
          style={{
            background: lightenHex("#1b7a72"),
            backgroundImage:
              "repeating-linear-gradient(135deg, rgba(255,255,255,0.55) 0 1px, transparent 1px 3px)",
          }}
        />
        Announced (unpaid)
      </li>
    </ul>
  );
}

function polyline(
  points: { year: number; value: number }[],
  years: number[],
  xAt: (index: number) => number,
  yAt: (value: number) => number,
): string {
  return points
    .flatMap((point, index) => {
      const yearIndex = years.indexOf(point.year);
      if (yearIndex < 0) return [];
      const command = index === 0 ? "M" : "L";
      return [`${command}${xAt(yearIndex).toFixed(1)},${yAt(point.value).toFixed(1)}`];
    })
    .join(" ");
}

function placeGrowthEndLabels({
  fundSeries,
  lastYear,
  xAt,
  yAt,
  minY,
  maxY,
}: {
  fundSeries: GrowthLineSeries[];
  lastYear: number | undefined;
  xAt: (year: number) => number;
  yAt: (value: number) => number;
  minY: number;
  maxY: number;
}) {
  const raw = fundSeries.flatMap((row) => {
    const last =
      (lastYear != null
        ? row.points.find((point) => point.year === lastYear)
        : undefined) ?? row.points[row.points.length - 1];
    if (!last) return [];
    return [
      {
        id: row.id,
        color: row.color,
        text: last.value >= 100_000 ? formatCompactUsd(last.value) : formatUsd(last.value, 0),
        x: xAt(last.year),
        y: yAt(last.value),
      },
    ];
  });
  const placed = staggerEndLabels(
    raw.map((label) => ({ id: label.id, y: label.y })),
    { minGap: END_LABEL_MIN_GAP, minY, maxY },
  );
  if (!placed) return [];
  const byId = new Map(raw.map((label) => [label.id, label]));
  return placed.flatMap((row) => {
    const source = byId.get(row.id);
    if (!source) return [];
    return [{ ...source, labelY: row.labelY }];
  });
}
