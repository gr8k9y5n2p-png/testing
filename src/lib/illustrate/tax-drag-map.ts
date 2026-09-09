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
 * Explicit `matched: true`. Omitted is not a match for **delta fallback**.
 * Totals still chart unless `illustrationIsUnmatched` (explicit false).
 * Periods have no root `matched` — read `left` / `right` only.
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

function holdingDollars(
  illustration: CompareIllustration | null | undefined,
  fallback?: number | null,
): number | null {
  return numericOrNull(illustration?.holding_dollars) ?? numericOrNull(fallback);
}

/**
 * Side-level `left.estimated_tax` / `right.estimated_tax` are null by design.
 * Chart tax from `*.totals.estimated_tax` (or `totals.estimated_tax_dollars`).
 */
function dollarsFromIllustration(
  illustration: CompareIllustration | null | undefined,
): number | null {
  const totals = illustration?.totals;
  return numericOrNull(totals?.estimated_tax ?? totals?.estimated_tax_dollars);
}

function rateFromIllustration(
  illustration: CompareIllustration | null | undefined,
): number | null {
  return numericOrNull(illustration?.totals?.effective_tax_on_holding);
}

function totalsMetric(
  illustration: CompareIllustration | null | undefined,
  metric: TaxDragMetric,
  holdingFallback?: number | null,
): number | null {
  if (!illustration || illustrationIsUnmatched(illustration)) return null;
  const dollars = dollarsFromIllustration(illustration);
  const rate = rateFromIllustration(illustration);
  const holding = holdingDollars(illustration, holdingFallback);
  if (metric === "tax_dollars") {
    if (dollars != null) return dollars;
    if (rate != null && holding != null && holding !== 0) return rate * holding;
    return null;
  }
  if (rate != null) return rate;
  if (dollars != null && holding != null && holding !== 0) return dollars / holding;
  return null;
}

function perSideDeltaMetric(
  deltas: CompareDeltas | null | undefined,
  metric: TaxDragMetric,
  side: "left" | "right",
): number | null {
  if (!deltas) return null;
  const nested = deltas[side];
  if (metric === "tax_dollars") {
    return numericOrNull(
      nested?.estimated_tax ??
        nested?.estimated_tax_dollars ??
        (side === "left"
          ? (deltas.left_estimated_tax ?? deltas.left_estimated_tax_dollars)
          : (deltas.right_estimated_tax ?? deltas.right_estimated_tax_dollars)),
    );
  }
  return numericOrNull(
    nested?.effective_tax_on_holding ??
      (side === "left"
        ? deltas.left_effective_tax_on_holding
        : deltas.right_effective_tax_on_holding),
  );
}

function sharedDeltaMetric(
  deltas: CompareDeltas | null | undefined,
  metric: TaxDragMetric,
): number | null {
  if (!deltas) return null;
  if (metric === "tax_dollars") {
    return numericOrNull(deltas.estimated_tax ?? deltas.estimated_tax_dollars);
  }
  return numericOrNull(deltas.effective_tax_on_holding);
}

/**
 * Chart value for one side of a compare period.
 *
 * - `matched: false` → N/A (ignore totals and deltas)
 * - `matched: true` + totals `"0.00"` / 0 → real zero
 * - Prefer `*.totals.estimated_tax` / `*.totals.effective_tax_on_holding`
 * - `matched: true` + null totals → `period.deltas.*` (secondary only)
 * - fund_vs_fund: never use shared deltas (right−left is null when the
 *   peer is unmatched and would wipe a matched fund’s bars)
 */
export function taxDragValueFromIllustration(
  illustration: CompareIllustration | null | undefined,
  metric: TaxDragMetric = "tax_dollars",
  deltas?: CompareDeltas | null,
  side?: "left" | "right",
  sharedDelta = false,
  holdingFallback?: number | null,
): number | null {
  if (!illustration || illustrationIsUnmatched(illustration)) return null;
  const fromTotals = totalsMetric(illustration, metric, holdingFallback);
  if (fromTotals != null) return fromTotals;
  if (!illustrationIsMatched(illustration)) return null;
  const holding = holdingDollars(illustration, holdingFallback);
  if (side) {
    const perSide = perSideDeltaMetric(deltas, metric, side);
    if (perSide != null) return perSide;
    const otherMetric: TaxDragMetric = metric === "tax_dollars" ? "effective_tax" : "tax_dollars";
    const otherVal = perSideDeltaMetric(deltas, otherMetric, side);
    if (otherVal != null && holding != null && holding !== 0) {
      return metric === "tax_dollars" ? otherVal * holding : otherVal / holding;
    }
  }
  if (!sharedDelta) return null;
  const shared = sharedDeltaMetric(deltas, metric);
  if (shared != null) return shared;
  if (metric === "effective_tax") {
    const dollars = sharedDeltaMetric(deltas, "tax_dollars");
    if (dollars != null && holding != null && holding !== 0) return dollars / holding;
  }
  if (metric === "tax_dollars") {
    const rate = sharedDeltaMetric(deltas, "effective_tax");
    if (rate != null && holding != null && holding !== 0) return rate * holding;
  }
  return null;
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
  sharedDelta = false,
  holdingFallback?: number | null,
): number | null {
  return taxDragValueFromIllustration(
    period[side],
    metric,
    period.deltas,
    side,
    sharedDelta,
    holdingFallback,
  );
}

function pickMetric(
  illustration: CompareIllustration | null | undefined,
  metric: TaxDragMetric,
  deltas: CompareDeltas | null | undefined,
  side: "left" | "right",
  sharedDelta: boolean,
  holdingFallback?: number | null,
): number | null {
  return taxDragValueFromIllustration(
    illustration,
    metric,
    deltas,
    side,
    sharedDelta,
    holdingFallback,
  );
}

/** Calendar year from a number, ISO date, or a label that contains 19xx/20xx. */
export function calendarYearFromUnknown(value: unknown): number {
  if (value == null || value === "") return 0;
  if (typeof value === "number" && Number.isFinite(value)) {
    const year = Math.trunc(value);
    return year >= 1900 && year <= 2100 ? year : 0;
  }
  const text = String(value).trim();
  const iso = text.match(/^((?:19|20)\d{2})(?:[-T/]|$)/);
  if (iso) return Number(iso[1]);
  const labeled = text.match(/\b((?:19|20)\d{2})\b/);
  if (labeled) return Number(labeled[1]);
  const numeric = Number(text);
  if (Number.isFinite(numeric)) {
    const year = Math.trunc(numeric);
    return year >= 1900 && year <= 2100 ? year : 0;
  }
  return 0;
}

export function illustrationVintageYear(
  illustration: CompareIllustration | null | undefined,
): number {
  if (!illustration) return 0;
  const extra = illustration as CompareIllustration & {
    year?: unknown;
    as_of?: unknown;
  };
  const first = Array.isArray(illustration.components)
    ? (illustration.components[0] as { as_of?: unknown; ex_date?: unknown } | undefined)
    : undefined;
  return (
    calendarYearFromUnknown(extra.year) ||
    calendarYearFromUnknown(extra.as_of) ||
    calendarYearFromUnknown(illustration.label) ||
    calendarYearFromUnknown(first?.as_of) ||
    calendarYearFromUnknown(first?.ex_date)
  );
}

/**
 * Resolve a compare period onto a calendar year.
 * `period.year` may be 0 / a date string / omitted; fall back to as_of then sides.
 */
export function comparePeriodCalendarYear(period: {
  year?: unknown;
  as_of?: unknown;
  label?: unknown;
  left?: CompareIllustration | null;
  right?: CompareIllustration | null;
}): number {
  return (
    calendarYearFromUnknown(period.year) ||
    calendarYearFromUnknown(period.as_of) ||
    calendarYearFromUnknown(period.label) ||
    illustrationVintageYear(period.right) ||
    illustrationVintageYear(period.left)
  );
}

/**
 * Map `POST /illustrate/compare` periods onto calendar-year points.
 *
 * Each fund/vintage uses **that side’s** `matched` independently. Do not
 * require both left and right for a year to chart a bar. `comparePeriodIsCovered`
 * is only for the delta-difference chart.
 *
 * `mode: "yoy"` pairs consecutive vintages (Data sets `period.year` to the
 * newer year; `right` is that vintage, `left` is the prior). Client ticker
 * labels (`AGTHX`) must not hide the older year — write both vintages onto
 * the growth axis (typically 2021–2025). Matched sides with null totals
 * still chart from `period.deltas.*` (same-fund YoY). Years not present
 * in `periods` are not invented.
 *
 * `fund_vs_fund`: pass `side` (`left` / `right`) for that fund’s individual
 * series. Shared `deltas.estimated_tax` (right−left) is **not** used — a
 * missing peer would null it and wipe the matched fund.
 *
 * `$` reads `left`/`right` `totals.estimated_tax` at the request
 * `holding_dollars`. Do not chart `summary.total_tax_difference`.
 * `%` prefers `totals.effective_tax_on_holding`, else tax / holding
 * (illustration holding, else summary `normalized_holding_dollars` / $10k).
 */
export function toTaxDragPeriods(
  response: CompareResponse,
  metric: TaxDragMetric = "tax_dollars",
  side: "left" | "right" | "auto" = "auto",
): TaxDragYearPoint[] {
  const byYear = new Map<number, TaxDragYearPoint>();
  const holdingFallback = numericOrNull(response.summary?.normalized_holding_dollars) ?? 10_000;

  const write = (year: number, value: number | null) => {
    if (!Number.isFinite(year) || year <= 0) return;
    const prior = byYear.get(year);
    if (prior && prior.value != null && value == null) return;
    byYear.set(year, { year, value });
  };

  for (const period of response.periods) {
    const yoy = response.mode === "yoy";
    const leftValue = pickMetric(
      period.left,
      metric,
      period.deltas,
      "left",
      yoy,
      holdingFallback,
    );
    const rightValue = pickMetric(
      period.right,
      metric,
      period.deltas,
      "right",
      yoy,
      holdingFallback,
    );
    const periodYear = comparePeriodCalendarYear(period);

    if (yoy) {
      const olderFromLabel = illustrationVintageYear(period.left);
      const newerFromLabel = illustrationVintageYear(period.right);
      // Zip pairs: Data sets period.year to the newer vintage; left is prior.
      // Calendar-year rows (both sides tickers, or both already that year)
      // must not shift a matched left onto year-1 when the caller asks for
      // a specific side — live AMCPX vs AGTHX is period.year × left/right.
      const calendarRow =
        periodYear > 0 &&
        ((olderFromLabel === 0 && newerFromLabel === 0) ||
          (olderFromLabel === periodYear && newerFromLabel === periodYear));
      if (calendarRow && side !== "auto") {
        write(periodYear, side === "right" ? rightValue : leftValue);
        continue;
      }
      if (
        calendarRow &&
        olderFromLabel === periodYear &&
        newerFromLabel === periodYear
      ) {
        write(periodYear, rightValue ?? leftValue);
        continue;
      }
      const olderYear = olderFromLabel || (periodYear > 1 ? periodYear - 1 : 0);
      const newerYear = newerFromLabel || periodYear;
      if (olderYear > 0) write(olderYear, leftValue);
      if (newerYear > 0) write(newerYear, rightValue);
      continue;
    }
    if (side === "right") {
      write(periodYear, rightValue);
    } else {
      write(periodYear, leftValue);
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
  sharedDelta = false,
): boolean {
  return (
    taxDragValueFromIllustration(illustration, "effective_tax", deltas, side, sharedDelta) !=
      null ||
    taxDragValueFromIllustration(illustration, "tax_dollars", deltas, side, sharedDelta) !=
      null
  );
}

/**
 * Both sides have a chartable tax value (including published 0).
 * Use only for the **delta** chart (right−left). Per-fund tax-drag series
 * must not call this — a missing FBGRX year must not hide AGTHX’s bar.
 */
export function comparePeriodIsCovered(period: {
  left?: CompareIllustration | null;
  right?: CompareIllustration | null;
  deltas?: CompareDeltas | null;
}): boolean {
  return (
    illustrationHasTaxDrag(period.left, period.deltas, "left", true) &&
    illustrationHasTaxDrag(period.right, period.deltas, "right", true)
  );
}
