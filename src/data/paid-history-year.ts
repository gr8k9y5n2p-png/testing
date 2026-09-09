import { isoDate } from "./distribution-bucket.ts";
import type { FundEstimateView } from "./types.ts";

/** Calendar year of an ISO date. Invalid / missing values stay null. */
export function calendarYearOfIso(value: string | null | undefined): number | null {
  const date = isoDate(value);
  if (!date) return null;
  const year = Number(date.slice(0, 4));
  return Number.isFinite(year) ? year : null;
}

export function currentCalendarYear(now = new Date()): number {
  return now.getUTCFullYear();
}

/** Inclusive `GET /distributions` as_of window for one calendar year. */
export function asOfYearBounds(year: number): { asOfFrom: string; asOfTo: string } {
  return {
    asOfFrom: `${year}-01-01`,
    asOfTo: `${year}-12-31`,
  };
}

/**
 * Paid-history year is `as_of` (Announced). Fall back to distributionYear
 * only when as_of is missing — never invent a calendar day.
 */
export function paidHistoryCalendarYear(row: {
  asOfDate?: string | null;
  distributionYear?: number;
}): number | null {
  return (
    calendarYearOfIso(row.asOfDate) ??
    (typeof row.distributionYear === "number" && Number.isFinite(row.distributionYear)
      ? row.distributionYear
      : null)
  );
}

export function collectPaidHistoryYears(funds: FundEstimateView[]): number[] {
  const years = new Set<number>();
  for (const fund of funds) {
    if (fund.bucket === "paid") {
      const year = paidHistoryCalendarYear(fund);
      if (year) years.add(year);
    }
    for (const event of fund.paidHistory ?? []) {
      const year = paidHistoryCalendarYear(event);
      if (year) years.add(year);
    }
  }
  return [...years].sort((a, b) => b - a);
}

/**
 * Current calendar year when that year has paid/final rows; otherwise the
 * most recent year present in hydrated distributions. Empty universe → now.
 */
export function defaultPaidHistoryYear(
  funds: FundEstimateView[],
  nowYear = currentCalendarYear(),
): number {
  const years = collectPaidHistoryYears(funds);
  if (years.includes(nowYear)) return nowYear;
  if (years.length) return years[0];
  return nowYear;
}

/** Toggle options: years in the data plus the current and previous calendar years. */
export function paidHistoryYearOptions(
  funds: FundEstimateView[],
  nowYear = currentCalendarYear(),
): number[] {
  const years = new Set(collectPaidHistoryYears(funds));
  years.add(nowYear);
  years.add(nowYear - 1);
  return [...years].sort((a, b) => b - a);
}
