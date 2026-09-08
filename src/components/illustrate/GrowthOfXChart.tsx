import {
  END_LABEL_MIN_GAP,
  staggerEndLabels,
} from "@/lib/charts/end-labels";
import { formatCompactUsd, niceMoneyScale } from "@/lib/charts/money-axis";
import {
  SHARED_CHART_PAD,
  SHARED_CHART_WIDTH,
  yearLayout,
  type ChartPad,
  type YearLayout,
} from "@/lib/charts/shared-axis";
import { formatUsd } from "@/lib/format";

export type ChartUnit = "dollars" | "percent";

export type GrowthLineSeries = {
  id: string;
  label: string;
  color: string;
  dashed?: boolean;
  points: { year: number; value: number }[];
};

export type AnnualizedRow = {
  id: string;
  label: string;
  color?: string;
  value: number | null;
};

export function GrowthOfXChart({
  years,
  series,
  startDollars,
  title,
  unit = "dollars",
  annualized,
  showAnnualized = true,
  loading = false,
  className = "",
  width = SHARED_CHART_WIDTH,
  height = 236,
  pad = SHARED_CHART_PAD,
  axis: axisProp,
  emptyLabel = "No growth series",
  emptyHint = "GET /performance returned no overlapping monthly points.",
}: {
  years: number[];
  series: GrowthLineSeries[];
  startDollars: number;
  title?: string;
  unit?: ChartUnit;
  annualized?: AnnualizedRow[];
  showAnnualized?: boolean;
  loading?: boolean;
  className?: string;
  width?: number;
  height?: number;
  pad?: ChartPad;
  axis?: YearLayout;
  emptyLabel?: string;
  emptyHint?: string;
}) {
  if (loading) {
    return (
      <div
        className={`min-h-[220px] w-full animate-pulse rounded-md bg-paper ${className}`}
        aria-busy
        aria-label="Loading cumulative growth"
      />
    );
  }

  const values = series.flatMap((row) => row.points.map((point) => point.value));
  if (years.length === 0 || values.length === 0) {
    return (
      <div className={`flex min-h-[160px] flex-col justify-center py-4 ${className}`}>
        <p className="font-serif text-lg text-ink">{emptyLabel}</p>
        {emptyHint ? (
          <p className="mt-2 text-sm text-muted">{emptyHint}</p>
        ) : null}
      </div>
    );
  }

  const lo = Math.min(unit === "percent" ? 0 : startDollars, ...values);
  const hi = Math.max(unit === "percent" ? 0 : startDollars, ...values);
  const moneyScale = unit === "dollars" ? niceMoneyScale(lo, hi, startDollars) : null;
  const pctScale = unit === "percent" ? nicePctScale(lo, hi) : null;
  const scale = moneyScale ?? pctScale ?? { min: lo, max: hi };
  const innerH = height - pad.top - pad.bottom;
  const layout = axisProp ?? yearLayout(years, 1, width, pad);
  const xAt = (year: number) => {
    const index = years.indexOf(year);
    const i = index < 0 ? 0 : index;
    return layout.center(i);
  };
  const yAt = (value: number) =>
    pad.top + innerH - ((value - scale.min) / (scale.max - scale.min || 1)) * innerH;

  const ticks = moneyScale?.ticks ?? pctTicks(scale.min, scale.max);
  const heading =
    title ??
    (unit === "percent"
      ? "Cumulative return"
      : `Cumulative growth of ${formatUsd(startDollars, 0)}`);

  const aria = series
    .map((row) => {
      const last = row.points[row.points.length - 1];
      return last
        ? `${row.label} ends at ${formatUsd(last.value, 0)}`
        : row.label;
    })
    .join(". ");

  const fundSeries = series.filter((row) => !row.dashed);
  const lastYear = years[years.length - 1];
  const endLabels = placeGrowthEndLabels({
    fundSeries,
    lastYear,
    unit,
    xAt,
    yAt,
    minY: pad.top + 8,
    maxY: pad.top + innerH - 4,
  });

  return (
    <section className={`w-full ${className}`}>
      <header className="mb-2 flex flex-wrap items-end justify-between gap-3">
        <h3 className="text-[11px] font-semibold uppercase tracking-[0.16em] text-faint">
          {heading}
        </h3>
        <ul className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[12px] text-ink">
          {series.map((row) => {
            const ann = annualized?.find((item) => item.id === row.id);
            return (
              <li key={row.id} className="flex items-center gap-1.5">
                <span
                  className="inline-block h-px w-4"
                  style={{
                    background: row.dashed ? "transparent" : row.color,
                    borderTop: row.dashed ? `1.5px dashed ${row.color}` : undefined,
                  }}
                />
                <span className="font-medium">{row.label}</span>
                {showAnnualized && !row.dashed && ann?.value != null ? (
                  <span
                    className="inline-flex items-center gap-1 rounded-full bg-paper px-2 py-0.5 text-[10px] font-medium"
                    style={{ color: row.color }}
                  >
                    <span
                      className="inline-block size-1.5 rounded-full"
                      style={{ background: row.color }}
                    />
                    {(ann.value * 100).toFixed(1)}% ann.
                  </span>
                ) : null}
              </li>
            );
          })}
        </ul>
      </header>

      <div role="img" aria-label={`${heading}. ${aria}`}>
        <svg viewBox={`0 0 ${width} ${height}`} className="h-auto w-full" aria-hidden>
          {years.map((_, index) =>
            index === 0 ? null : (
              <line
                key={`year-gutter-${years[index]}`}
                x1={layout.slotLeft(index)}
                x2={layout.slotLeft(index)}
                y1={pad.top}
                y2={pad.top + innerH}
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
                  x1={pad.left}
                  x2={width - pad.right}
                  y1={y}
                  y2={y}
                  className="stroke-line"
                  strokeWidth={1}
                />
                <text
                  x={pad.left - 6}
                  y={y + 3}
                  textAnchor="end"
                  className="fill-faint"
                  fontSize={9}
                  fontFamily="ui-monospace, monospace"
                >
                  {unit === "percent" ? formatAxisPct(tick) : formatCompactUsd(tick)}
                </text>
              </g>
            );
          })}

          {series.map((row) => {
            const d = polyline(row.points, xAt, yAt);
            if (!d) return null;
            const last = row.points[row.points.length - 1];
            return (
              <g key={row.id}>
                <path
                  d={d}
                  fill="none"
                  stroke={row.color}
                  strokeWidth={1.75}
                  strokeDasharray={row.dashed ? "5 4" : undefined}
                  strokeLinejoin="round"
                  strokeLinecap="round"
                />
                {last && !row.dashed ? (
                  <circle
                    cx={xAt(last.year)}
                    cy={yAt(last.value)}
                    r={3.2}
                    fill={row.color}
                  />
                ) : null}
              </g>
            );
          })}

          {endLabels.map((label) => {
            const leader = Math.abs(label.labelY - label.y) > 6;
            return (
              <g key={`end-${label.id}`} data-end-label={label.id}>
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
                  data-end-label-y={label.labelY.toFixed(1)}
                >
                  {label.text}
                </text>
              </g>
            );
          })}

          {years.map((year) => (
            <text
              key={year}
              x={xAt(year)}
              y={height - 8}
              textAnchor="middle"
              className="fill-muted"
              fontSize={10}
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

type PlacedGrowthEndLabel = {
  id: string;
  color: string;
  text: string;
  x: number;
  y: number;
  labelY: number;
};

function formatEndValue(value: number): string {
  return value >= 100_000 ? formatCompactUsd(value) : formatUsd(value, 0);
}

function placeGrowthEndLabels({
  fundSeries,
  lastYear,
  unit,
  xAt,
  yAt,
  minY,
  maxY,
}: {
  fundSeries: GrowthLineSeries[];
  lastYear: number | undefined;
  unit: ChartUnit;
  xAt: (year: number) => number;
  yAt: (value: number) => number;
  minY: number;
  maxY: number;
}): PlacedGrowthEndLabel[] {
  if (unit === "percent") return [];
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
        text: formatEndValue(last.value),
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

function polyline(
  points: { year: number; value: number }[],
  xAt: (year: number) => number,
  yAt: (value: number) => number,
): string {
  return points
    .map((point, index) => {
      const command = index === 0 ? "M" : "L";
      return `${command}${xAt(point.year).toFixed(1)},${yAt(point.value).toFixed(1)}`;
    })
    .join(" ");
}

function nicePctScale(min: number, max: number) {
  const pad = Math.max((max - min) * 0.08, 0.05);
  const hi = max + pad;
  const step = hi <= 0.5 ? 0.1 : hi <= 1.5 ? 0.25 : 0.5;
  return {
    min: min >= 0 ? 0 : Math.floor((min - pad) / step) * step,
    max: Math.ceil(hi / step) * step,
  };
}

function formatAxisPct(value: number): string {
  return `${(value * 100).toFixed(0)}%`;
}

function pctTicks(min: number, max: number): number[] {
  const span = max - min;
  const step = span <= 0.5 ? 0.1 : span <= 1.5 ? 0.25 : 0.5;
  const ticks: number[] = [];
  for (let value = min; value <= max + 0.001; value += step) {
    ticks.push(Math.round(value * 1000) / 1000);
  }
  return ticks.length >= 2 ? ticks : [min, max];
}

