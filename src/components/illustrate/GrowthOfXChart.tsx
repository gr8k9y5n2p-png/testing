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
  height = 228,
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

  const ticks = [scale.max, (scale.min + scale.max) / 2, scale.min];
  const heading =
    title ??
    (unit === "percent"
      ? "Cumulative return"
      : `Cumulative investment performance (Growth of ${formatUsd(startDollars, 0)})`);

  const aria = series
    .map((row) => {
      const last = row.points[row.points.length - 1];
      return last
        ? `${row.label} ends at ${formatUsd(last.value, 0)}`
        : row.label;
    })
    .join(". ");

  return (
    <section className={`relative w-full ${className}`}>
      <header className="mb-2">
        <h3 className="text-[11px] font-semibold uppercase tracking-[0.16em] text-faint">
          {heading}
        </h3>
      </header>

      <ul className="pointer-events-none absolute left-14 top-8 z-10 flex flex-col gap-1 text-[11px] text-ink">
        {series.map((row) => (
          <li key={row.id} className="flex items-center gap-1.5">
            <span
              className="inline-block h-px w-4"
              style={{
                background: row.dashed ? "transparent" : row.color,
                boxShadow: row.dashed ? `0 0 0 0.6px ${row.color}` : undefined,
                borderTop: row.dashed ? `1px dashed ${row.color}` : undefined,
              }}
            />
            {row.label}
          </li>
        ))}
      </ul>

      {showAnnualized && annualized && annualized.length > 0 ? (
        <aside className="absolute bottom-10 right-4 z-10 rounded-md border border-line bg-surface/95 px-2.5 py-2 text-[10px] shadow-[0_4px_12px_rgba(26,29,26,0.06)]">
          <p className="mb-1 font-semibold uppercase tracking-[0.12em] text-faint">
            {years.length}-year annualized
          </p>
          <table>
            <tbody>
              {annualized.map((row) => (
                <tr key={row.id}>
                  <td className="pr-3 text-muted">{row.label}</td>
                  <td className="text-right font-mono text-ink">
                    {row.value == null ? "—" : `${(row.value * 100).toFixed(1)}%`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-1 text-[9px] uppercase tracking-[0.08em] text-faint">
            Hypothetical illustration only
          </p>
        </aside>
      ) : null}

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
                {row.points.map((point) => (
                  <circle
                    key={`${row.id}-${point.year}`}
                    cx={xAt(point.year)}
                    cy={yAt(point.value)}
                    r={2.4}
                    fill={row.color}
                  />
                ))}
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
  const lo = min >= 0 ? 0 : min - pad;
  const hi = max + pad;
  const step = hi <= 0.5 ? 0.1 : hi <= 1.5 ? 0.25 : 0.5;
  return {
    min: min >= 0 ? 0 : Math.floor(lo / step) * step,
    max: Math.ceil(hi / step) * step,
  };
}

function formatAxisPct(value: number): string {
  return `${(value * 100).toFixed(0)}%`;
}

function niceMoneyScale(min: number, max: number) {
  const pad = Math.max((max - min) * 0.08, 500);
  const lo = Math.max(0, min - pad);
  const hi = max + pad;
  const step = hi <= 20_000 ? 5_000 : hi <= 50_000 ? 10_000 : 20_000;
  return {
    min: Math.floor(lo / step) * step,
    max: Math.ceil(hi / step) * step,
  };
}

function formatCompactUsd(value: number): string {
  if (value >= 1000) return `$${(value / 1000).toFixed(value % 1000 === 0 ? 0 : 1)}k`;
  return formatUsd(value, 0);
}
