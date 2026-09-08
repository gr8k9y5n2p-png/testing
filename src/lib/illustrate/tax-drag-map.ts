import type {
  CompareIllustration,
  CompareResponse,
} from "./compare-types";

/** Visible gap label. Never substitute 0% / a zero bar. */
export const TAX_DRAG_NA_LABEL = "N/A";

/** Bar / line metric for `TaxDragByYearChart`. */
export type TaxDragMetric = "tax_dollars" | "effective_tax";

/**
 * One calendar year. `value` is tax $ or a decimal effective-tax rate
 * (`0.008` = 0.8%) depending on `metric`. `null` is a gap — never invent.
 */
export type TaxDragYearPoint = {
  year: number;
  value: number | null;
};

export type TaxDragLinePoint = {
  year: number;
  value: number | null;
};

export type TaxDragFundSeries = {
  id: string;
  label: string;
  color: string;
  description?: string;
  points: TaxDragYearPoint[];
};

const DEFAULT_LEFT_COLOR = "#1b7a72";
const DEFAULT_RIGHT_COLOR = "#3a4348";

/**
 * Data sends `matched` as the miss signal. Totals stay `"0.00"` / `"0.000000"`
 * on unmatched years — do not treat those zeros as tax drag.
 */
export function illustrationIsMatched(
  illustration: { matched?: boolean | string | null } | null | undefined,
): boolean {
  return illustration?.matched === true || illustration?.matched === "true";
}

function numericOrZero(value: unknown): number {
  if (value == null || value === "") return 0;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function pickMetric(
  illustration: CompareIllustration | null | undefined,
  metric: TaxDragMetric,
): number | null {
  if (!illustrationIsMatched(illustration)) return null;
  const totals = illustration?.totals;
  if (metric === "tax_dollars") {
    // Request-holding dollars. Never summary.total_tax_difference
    // (that footer field is always normalized to $10,000).
    return numericOrZero(totals?.estimated_tax ?? totals?.estimated_tax_dollars);
  }
  // Rate — fraction of holding. Does not scale with $. matched + 0.000000 = 0.
  return numericOrZero(totals?.effective_tax_on_holding);
}

function yearFromLabel(label: string | undefined, fallback: number): number {
  const match = label?.trim().match(/\b(19|20)\d{2}\b/);
  if (!match) return fallback;
  return Number(match[0]);
}

/**
 * Map `POST /illustrate/compare` periods onto calendar-year points.
 *
 * `mode: "yoy"` pairs consecutive vintages (period.year is the newer year;
 * `right` is that vintage, `left` is the prior). Gaps stay `null` when
 * `matched` is not true — years not present in `periods` are not invented.
 *
 * `fund_vs_fund`: pass `side` (`left` / `right`) for that fund’s individual
 * series. `auto` is left-only; use `toCompareTaxDragSeries` for both funds.
 *
 * `$` reads `left`/`right` `totals.estimated_tax` at the request
 * `holding_dollars`. Do not chart `summary.total_tax_difference` or
 * `summary.distribution_dollars_difference`.
 */
export function toTaxDragPeriods(
  response: CompareResponse,
  metric: TaxDragMetric = "tax_dollars",
  side: "left" | "right" | "auto" = "auto",
): TaxDragYearPoint[] {
  const byYear = new Map<number, TaxDragYearPoint>();

  const write = (year: number, illustration: CompareIllustration | null | undefined) => {
    if (!Number.isFinite(year) || year <= 0) return;
    const value = pickMetric(illustration, metric);
    const prior = byYear.get(year);
    if (prior && prior.value != null && value == null) return;
    byYear.set(year, { year, value });
  };

  for (const period of response.periods) {
    if (response.mode === "yoy") {
      const newerYear = period.year;
      const olderYear = yearFromLabel(period.left?.label, newerYear - 1);
      write(olderYear, period.left);
      write(newerYear, period.right);
      continue;
    }
    if (side === "right") {
      write(period.year, period.right);
    } else {
      write(period.year, period.left);
    }
  }

  return [...byYear.values()].sort((a, b) => a.year - b.year);
}

function sideLabel(
  response: CompareResponse,
  side: "left" | "right",
  fallback: string,
): string {
  const first = response.periods[0];
  const label = (response[side]?.label || first?.[side]?.label || fallback).trim();
  return label || fallback;
}

/**
 * One series per fund for fund-vs-fund compare. YoY (single selector)
 * returns that fund’s calendar-year series only.
 */
export function toCompareTaxDragSeries(
  response: CompareResponse,
  metric: TaxDragMetric = "effective_tax",
  colors?: { left?: string; right?: string },
): TaxDragFundSeries[] {
  if (response.mode === "yoy") {
    return [
      {
        id: sideLabel(response, "left", "Fund"),
        label: sideLabel(response, "left", "Fund"),
        color: colors?.left ?? DEFAULT_LEFT_COLOR,
        points: toTaxDragPeriods(response, metric),
      },
    ];
  }
  return [
    {
      id: "left",
      label: sideLabel(response, "left", "Fund A"),
      color: colors?.left ?? DEFAULT_LEFT_COLOR,
      points: toTaxDragPeriods(response, metric, "left"),
    },
    {
      id: "right",
      label: sideLabel(response, "right", "Fund B"),
      color: colors?.right ?? DEFAULT_RIGHT_COLOR,
      points: toTaxDragPeriods(response, metric, "right"),
    },
  ];
}

/** Fill a shared year axis. Missing years stay `null` (N/A) — never 0. */
export function alignTaxDragYears(
  points: TaxDragYearPoint[],
  years: number[],
): TaxDragYearPoint[] {
  return years.map((year) => {
    const match = points.find((point) => point.year === year);
    return { year, value: match?.value ?? null };
  });
}

export function taxDragLineFromPeriods(
  periods: TaxDragYearPoint[],
): TaxDragLinePoint[] {
  return periods.map((point) => ({ year: point.year, value: point.value }));
}

/** Flip rates to negative so bars drop from a 0% baseline. */
export function toNegativeTaxDrag(
  periods: TaxDragYearPoint[],
): TaxDragYearPoint[] {
  return periods.map((point) => ({
    year: point.year,
    value: point.value == null ? null : -Math.abs(point.value),
  }));
}

export function unionTaxDragYears(series: TaxDragFundSeries[]): number[] {
  const years = new Set<number>();
  for (const row of series) {
    for (const point of row.points) years.add(point.year);
  }
  return [...years].sort((a, b) => a - b);
}

/** Both sides matched — a delta is chartable. Otherwise the year is N/A. */
export function comparePeriodIsCovered(period: {
  left?: { matched?: boolean | string | null } | null;
  right?: { matched?: boolean | string | null } | null;
}): boolean {
  return illustrationIsMatched(period.left) && illustrationIsMatched(period.right);
}
