import {
  SHARED_CHART_PAD,
  SHARED_CHART_WIDTH,
  yearLayout,
  type ChartPad,
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
        <p className="font-serif text-lg text-ink">No growth series</p>
        <p className="mt-2 text-sm text-muted">
          GET /performance returned no overlapping monthly points.
        </p>
      </div>
    );
  }

  const lo = Math.min(unit === "percent" ? 0 : startDollars, ...values);
  const hi = Math.max(unit === "percent" ? 0 : startDollars, ...values);
  const scale = unit === "percent" ? nicePctScale(lo, hi) : niceMoneyScale(lo, hi);
  const innerH = height - pad.top - pad.bottom;
  const layout = yearLayout(years, 1, width, pad);
  const xAt = (year: number) => {
    const index = years.indexOf(year);
    const i = index < 0 ? 0 : index;
    return layout.center(i);
  };
  const yAt = (value: number) =>
    pad.top + innerH - ((value - scale.min) / (scale.max - scale.min || 1)) * innerH;

  const ticks =
    unit === "percent" ? pctTicks(scale.min, scale.max) : moneyTicks(scale.min, scale.max);
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

          {fundSeries.map((row, index) => {
            const last = row.points.find((point) => point.year === lastYear) ??
              row.points[row.points.length - 1];
            if (!last || unit === "percent") return null;
            const offset = index === 0 ? -12 : 12;
            return (
              <text
                key={`end-${row.id}`}
                x={xAt(last.year) + 8}
                y={yAt(last.value) + offset}
                className="fill-ink"
                fontSize={10}
                fontFamily="ui-monospace, monospace"
                fontWeight={500}
              >
                {formatUsd(last.value, 0)}
              </text>
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

function niceMoneyScale(min: number, max: number) {
  const pad = Math.max((max - min) * 0.08, 400);
  const lo = Math.max(0, min - pad * 0.25);
  const hi = max + pad;
  const span = hi - lo;
  const step = span <= 12_000 ? 2_500 : span <= 25_000 ? 5_000 : span <= 60_000 ? 10_000 : 20_000;
  return {
    min: Math.floor(lo / step) * step,
    max: Math.ceil(hi / step) * step,
  };
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

function moneyTicks(min: number, max: number): number[] {
  const span = max - min;
  const step = span <= 12_000 ? 2_500 : span <= 25_000 ? 5_000 : span <= 60_000 ? 10_000 : 20_000;
  const ticks: number[] = [];
  for (let value = min; value <= max + 0.01; value += step) {
    ticks.push(value);
  }
  return ticks.length >= 2 ? ticks : [min, max];
}

function formatCompactUsd(value: number): string {
  if (value >= 1000) return `$${(value / 1000).toFixed(value % 1000 === 0 ? 0 : 1)}k`;
  return formatUsd(value, 0);
}
