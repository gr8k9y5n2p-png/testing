/**
 * Portfolio compare `periods[]` → ticker × year tax matrix.
 * Import-free so Node tests can load it without `@/` aliases.
 *
 * Historical tax drag is separate from Upcoming. A period row with published
 * tax densifies even when Upcoming left the holding uncovered.
 */

import { portfolioPeriodTaxIsUnmatched } from "./portfolio-compare-years.ts";

export type PeriodHoldingTaxMapped = {
  ticker: string;
  holding_index?: number;
  matched: boolean;
  estimated_tax: number | null;
  covered?: boolean;
  gap_reason?: string | null;
};

export type PeriodMapped = {
  year: number;
  as_of?: string | null;
  current: PeriodHoldingTaxMapped[];
  proposed: PeriodHoldingTaxMapped[];
};

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

function numOrNull(value: unknown): number | null {
  if (value == null || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function isoOrNull(value: unknown): string | null {
  if (value == null || value === "") return null;
  const day = String(value).trim().slice(0, 10);
  return /^\d{4}-\d{2}-\d{2}$/.test(day) ? day : String(value);
}

/** Calendar year from a number, ISO date, or a label that contains 19xx/20xx. */
export function calendarYearFromPeriodValue(value: unknown): number {
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

export function calendarYearFromPeriod(raw: Record<string, unknown>): number {
  return (
    calendarYearFromPeriodValue(raw.year) ||
    calendarYearFromPeriodValue(raw.as_of) ||
    calendarYearFromPeriodValue(raw.asOf) ||
    calendarYearFromPeriodValue(raw.label) ||
    calendarYearFromPeriodValue(raw.period)
  );
}

/**
 * Ticker from the same fields Search densifies (ticker, identifier, selectors, label).
 * Long fund names are not tickers — those rows still map by holding_index.
 */
export function periodHoldingTicker(raw: Record<string, unknown>): string {
  const selectors =
    raw.selectors && typeof raw.selectors === "object" && !Array.isArray(raw.selectors)
      ? (raw.selectors as Record<string, unknown>)
      : {};
  const candidates = [
    raw.ticker,
    raw.fund_identifier,
    raw.fundIdentifier,
    raw.symbol,
    selectors.ticker,
    selectors.fund_identifier,
    raw.label,
  ];
  for (const candidate of candidates) {
    if (typeof candidate !== "string") continue;
    const text = candidate.trim();
    if (!text) continue;
    if (text.length <= 12 && /^[A-Za-z][A-Za-z0-9.-]*$/.test(text)) {
      return text.toUpperCase();
    }
  }
  return "";
}

function looksLikeHolding(value: unknown): boolean {
  if (value == null || typeof value !== "object" || Array.isArray(value)) return false;
  const row = value as Record<string, unknown>;
  return (
    row.estimated_tax != null ||
    row.estimatedTax != null ||
    row.estimated_tax_dollars != null ||
    row.ticker != null ||
    row.fund_identifier != null ||
    row.label != null ||
    row.totals != null ||
    row.illustration != null ||
    row.matched != null ||
    row.covered != null ||
    row.holding_index != null
  );
}

function periodHoldingTaxFromRaw(
  raw: unknown,
  index: number,
): PeriodHoldingTaxMapped | null {
  if (raw == null || typeof raw !== "object") return null;
  const row = asRecord(raw);
  const illustration = row.illustration ? asRecord(row.illustration) : null;
  const totals = illustration ? asRecord(illustration.totals) : asRecord(row.totals);
  const ticker = periodHoldingTicker(row);
  const tax = numOrNull(
    row.estimated_tax ??
      row.estimatedTax ??
      row.estimated_tax_dollars ??
      totals.estimated_tax ??
      totals.estimated_tax_dollars,
  );

  if (!ticker && tax == null && row.holding_index == null && row.matched == null) {
    return null;
  }

  const matchedRaw = row.matched ?? illustration?.matched;
  const coveredRaw = row.covered ?? illustration?.covered;
  const gap = row.gap_reason ?? row.gapReason ?? illustration?.gap_reason;
  const unmatched = portfolioPeriodTaxIsUnmatched({
    matched: matchedRaw,
    covered: coveredRaw,
    gapReason: gap,
    estimatedTax: tax,
  });

  return {
    ticker,
    holding_index: numOrNull(row.holding_index) ?? index,
    matched: unmatched ? false : true,
    estimated_tax: unmatched ? null : tax,
    covered:
      coveredRaw === false || coveredRaw === "false"
        ? false
        : coveredRaw == null
          ? undefined
          : true,
    gap_reason: gap == null ? null : String(gap),
  };
}

export function normalizePeriodSide(raw: unknown): PeriodHoldingTaxMapped[] {
  if (raw == null) return [];
  if (Array.isArray(raw)) {
    return raw
      .map((item, index) => periodHoldingTaxFromRaw(item, index))
      .filter((item): item is PeriodHoldingTaxMapped => item != null);
  }
  const row = asRecord(raw);
  if (Array.isArray(row.holdings)) return normalizePeriodSide(row.holdings);
  if (Array.isArray(row.funds)) return normalizePeriodSide(row.funds);
  if (looksLikeHolding(row)) {
    const mapped = periodHoldingTaxFromRaw(row, 0);
    return mapped ? [mapped] : [];
  }
  return Object.entries(row)
    .map(([key, value], index) => {
      if (!looksLikeHolding(value)) return null;
      const holding = asRecord(value);
      if (!periodHoldingTicker(holding) && /^[A-Za-z][A-Za-z0-9.-]{0,11}$/.test(key)) {
        return periodHoldingTaxFromRaw({ ...holding, ticker: key }, index);
      }
      return periodHoldingTaxFromRaw(holding, index);
    })
    .filter((item): item is PeriodHoldingTaxMapped => item != null);
}

function normalizeOnePeriod(raw: unknown): PeriodMapped[] {
  if (raw == null || typeof raw !== "object") return [];
  const row = asRecord(raw);
  const year = calendarYearFromPeriod(row);
  if (!(year > 0)) return [];
  return [
    {
      year,
      as_of: isoOrNull(row.as_of ?? row.asOf),
      current: normalizePeriodSide(row.current ?? row.left),
      proposed: normalizePeriodSide(row.proposed ?? row.right),
    },
  ];
}

export function normalizePortfolioComparePeriods(raw: unknown): PeriodMapped[] {
  if (Array.isArray(raw)) {
    return raw.flatMap(normalizeOnePeriod);
  }
  if (raw == null || typeof raw !== "object") return [];
  const record = asRecord(raw);
  if (Array.isArray(record.periods)) {
    return normalizePortfolioComparePeriods(record.periods);
  }
  return Object.entries(record).flatMap(([key, value]) => {
    if (value == null || typeof value !== "object") return [];
    const row = asRecord(value);
    return normalizeOnePeriod(row.year == null ? { ...row, year: key } : row);
  });
}
