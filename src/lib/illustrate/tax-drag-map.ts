import type {
  CompareDeltas,
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
 * Explicit `matched: true`. Omitted is not a match.
 */
export function illustrationIsMatched(
  illustration: { matched?: boolean | string | null } | null | undefined,
): boolean {
  return illustration?.matched === true || illustration?.matched === "true";
}

/** Data miss signal. Unmatched sides are `matched: false` (totals may be null). */
export function illustrationIsUnmatched(
  illustration: { matched?: boolean | string | null } | null | undefined,
): boolean {
  return illustration?.matched === false || illustration?.matched === "false";
}

function numericOrNull(value: unknown): number | null {
  if (value == null || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function totalsMetric(
  illustration: CompareIllustration | null | undefined,
  metric: TaxDragMetric,
): number | null {
  if (!illustration || illustrationIsUnmatched(illustration)) return null;
  const totals = illustration.totals;
  if (metric === "tax_dollars") {
    // Request-holding dollars. Never summary.total_tax_difference
    // (that footer field is always normalized to $10,000).
    return numericOrNull(
      totals?.estimated_tax ??
        totals?.estimated_tax_dollars ??
        illustration.estimated_tax ??
        illustration.estimated_tax_dollars,
    );
  }
  return numericOrNull(
    totals?.effective_tax_on_holding ?? illustration.effective_tax_on_holding,
  );
}

function deltaMetric(
  deltas: CompareDeltas | null | undefined,
  metric: TaxDragMetric,
  side?: "left" | "right",
): number | null {
  if (!deltas) return null;
  const nested = side ? deltas[side] : undefined;
  if (metric === "tax_dollars") {
    const perSide =
      side === "left"
        ? (nested?.estimated_tax ??
            nested?.estimated_tax_dollars ??
            deltas.left_estimated_tax ??
            deltas.left_estimated_tax_dollars)
        : side === "right"
          ? (nested?.estimated_tax ??
              nested?.estimated_tax_dollars ??
              deltas.right_estimated_tax ??
              deltas.right_estimated_tax_dollars)
          : null;
    return numericOrNull(perSide ?? deltas.estimated_tax ?? deltas.estimated_tax_dollars);
  }
  const perSide =
    side === "left"
      ? (nested?.effective_tax_on_holding ?? deltas.left_effective_tax_on_holding)
      : side === "right"
        ? (nested?.effective_tax_on_holding ?? deltas.right_effective_tax_on_holding)
        : null;
  return numericOrNull(perSide ?? deltas.effective_tax_on_holding);
}

/**
 * Chart value for one side of a compare period.
 *
 * - `matched: false` → N/A (ignore totals and deltas)
 * - `matched: true` + `"0.00"` / 0 → real zero
 * - `matched: true` + null totals → fall back to period `deltas.*`
 *   (live compare can put tax only on deltas)
 */
export function taxDragValueFromIllustration(
  illustration: CompareIllustration | null | undefined,
  metric: TaxDragMetric = "tax_dollars",
  deltas?: CompareDeltas | null,
  side?: "left" | "right",
): number | null {
  if (!illustration || illustrationIsUnmatched(illustration)) return null;
  const fromTotals = totalsMetric(illustration, metric);
  if (fromTotals != null) return fromTotals;
  if (!illustrationIsMatched(illustration)) return null;
  return deltaMetric(deltas, metric, side);
}

/** Same rules, reading `period.left` / `period.right` (never a root `period.matched`). */
export function taxDragValueFromPeriodSide(
  period: {
    left?: CompareIllustration | null;
    right?: CompareIllustration | null;
    deltas?: CompareDeltas | null;
  },
  side: "left" | "right",
  metric: TaxDragMetric = "tax_dollars",
): number | null {
  return taxDragValueFromIllustration(period[side], metric, period.deltas, side);
}

function pickMetric(
  illustration: CompareIllustration | null | undefined,
  metric: TaxDragMetric,
  deltas?: CompareDeltas | null,
  side?: "left" | "right",
): number | null {
  return taxDragValueFromIllustration(illustration, metric, deltas, side);
}

function yearFromLabel(label: string | undefined, fallback?: number): number | null {
  const match = label?.trim().match(/\b(19|20)\d{2}\b/);
  if (match) return Number(match[0]);
  return fallback ?? null;
}

/**
 * Map `POST /illustrate/compare` periods onto calendar-year points.
 *
 * `mode: "yoy"` pairs consecutive vintages (period.year is the newer year;
 * `right` is that vintage, `left` is the prior). Gaps stay `null` when
 * `matched` is false. Matched sides with null totals still chart when
 * `period.deltas` exposes tax (live AGTHX/FBGRX shape). Years not present
 * in `periods` are not invented.
 *
 * `fund_vs_fund`: pass `side` (`left` / `right`) for that fund’s individual
 * series. `auto` is left-only; use `toCompareTaxDragSeries` for both funds.
 *
 * `$` reads `left`/`right` `totals.estimated_tax` at the request
 * `holding_dollars`, then period `deltas.estimated_tax` (and per-side
 * delta fields) when totals are null. Do not chart
 * `summary.total_tax_difference` or `summary.distribution_dollars_difference`.
 */
export function toTaxDragPeriods(
  response: CompareResponse,
  metric: TaxDragMetric = "tax_dollars",
  side: "left" | "right" | "auto" = "auto",
): TaxDragYearPoint[] {
  const byYear = new Map<number, TaxDragYearPoint>();

  const write = (year: number, value: number | null) => {
    if (!Number.isFinite(year) || year <= 0) return;
    const prior = byYear.get(year);
    if (prior && prior.value != null && value == null) return;
    byYear.set(year, { year, value });
  };

  for (const period of response.periods) {
    const leftTotals = totalsMetric(period.left, metric);
    const rightTotals = totalsMetric(period.right, metric);
    const leftValue = pickMetric(period.left, metric, period.deltas, "left");
    const rightValue = pickMetric(period.right, metric, period.deltas, "right");

    if (response.mode === "yoy") {
      const newerYear = period.year;
      const olderYear = yearFromLabel(period.left?.label, newerYear - 1);
      const vintageLabel = yearFromLabel(period.left?.label) != null;
      const sharedDeltaOnly =
        leftTotals == null &&
        rightTotals == null &&
        (leftValue == null || rightValue == null || leftValue === rightValue);
      // Live yoy calendar rows label sides with the ticker and put tax on
      // period.deltas — plot once on period.year. Vintage pairs keep both years.
      if (!vintageLabel || sharedDeltaOnly) {
        write(newerYear, rightValue ?? leftValue);
        continue;
      }
      write(olderYear ?? newerYear - 1, leftValue);
      write(newerYear, rightValue);
      continue;
    }
    if (side === "right") {
      write(period.year, rightValue);
    } else {
      write(period.year, leftValue);
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

function illustrationHasTaxDrag(
  illustration: CompareIllustration | null | undefined,
  deltas?: CompareDeltas | null,
  side?: "left" | "right",
): boolean {
  return (
    taxDragValueFromIllustration(illustration, "effective_tax", deltas, side) != null ||
    taxDragValueFromIllustration(illustration, "tax_dollars", deltas, side) != null
  );
}

/** Both sides have a chartable tax value (including published 0 and delta fallback). */
export function comparePeriodIsCovered(period: {
  left?: CompareIllustration | null;
  right?: CompareIllustration | null;
  deltas?: CompareDeltas | null;
}): boolean {
  return (
    illustrationHasTaxDrag(period.left, period.deltas, "left") &&
    illustrationHasTaxDrag(period.right, period.deltas, "right")
  );
}
