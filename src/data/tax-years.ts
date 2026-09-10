/**
 * Tax years Data actually has. Never invent a calendar range or $0 year.
 * Search Year dropdown lists these plus an All years option.
 */

import { isoDate } from "./distribution-bucket.ts";
import type { FundEstimate, PaidDistributionEvent } from "./types.ts";

/** Plausible fund-distribution tax year. Outside this is noise, not coverage. */
const YEAR_MIN = 1990;
const YEAR_MAX = 2100;

export function isTaxYear(value: unknown): value is number {
  return (
    typeof value === "number" &&
    Number.isInteger(value) &&
    value >= YEAR_MIN &&
    value <= YEAR_MAX
  );
}

export function taxYearFromUnknown(value: unknown): number | null {
  if (isTaxYear(value)) return value;
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (/^\d{4}$/.test(trimmed)) {
      const year = Number(trimmed);
      return isTaxYear(year) ? year : null;
    }
    return taxYearFromIso(trimmed);
  }
  if (typeof value === "number" && Number.isFinite(value)) {
    const year = Math.trunc(value);
    return isTaxYear(year) ? year : null;
  }
  return null;
}

export function taxYearFromIso(value: string | null | undefined): number | null {
  const year = Number((isoDate(value) ?? String(value ?? "")).slice(0, 4));
  return isTaxYear(year) ? year : null;
}

/** Newest first. Drops invalid / invented values. */
export function mergeTaxYears(
  ...lists: Array<Iterable<unknown> | null | undefined>
): number[] {
  const years = new Set<number>();
  for (const list of lists) {
    if (!list) continue;
    for (const value of list) {
      const year = taxYearFromUnknown(value);
      if (year != null) years.add(year);
    }
  }
  return [...years].sort((a, b) => b - a);
}

function addDateYear(years: Set<number>, value: string | null | undefined) {
  const year = taxYearFromIso(value);
  if (year != null) years.add(year);
}

export function collectTaxYearsFromPaidEvent(
  event: Pick<
    PaidDistributionEvent,
    "distributionYear" | "asOfDate" | "recordDate" | "exDate" | "payableDate"
  >,
): number[] {
  const years = new Set<number>();
  if (isTaxYear(event.distributionYear)) years.add(event.distributionYear);
  addDateYear(years, event.payableDate);
  addDateYear(years, event.exDate);
  addDateYear(years, event.recordDate);
  addDateYear(years, event.asOfDate);
  return [...years];
}

export function collectTaxYearsFromFund(
  fund: Pick<
    FundEstimate,
    | "distributionYear"
    | "asOfDate"
    | "recordDate"
    | "exDate"
    | "payableDate"
    | "publishedAt"
    | "paidHistory"
  >,
): number[] {
  const years = new Set<number>(collectTaxYearsFromPaidEvent(fund));
  addDateYear(years, fund.publishedAt);
  for (const event of fund.paidHistory ?? []) {
    for (const year of collectTaxYearsFromPaidEvent(event)) years.add(year);
  }
  return [...years];
}

export function collectTaxYearsFromFunds(
  funds: Iterable<
    Pick<
      FundEstimate,
      | "distributionYear"
      | "asOfDate"
      | "recordDate"
      | "exDate"
      | "payableDate"
      | "publishedAt"
      | "paidHistory"
    >
  >,
): number[] {
  return mergeTaxYears(
    [...funds].flatMap((fund) => collectTaxYearsFromFund(fund)),
  );
}

/**
 * Years Data / coverage already enumerated. Accepts `years`, `tax_years`,
 * `available_years`, `distribution_years`, nested `facets`, and ISO dates.
 * Does not fill a missing range.
 */
export function taxYearsFromPayload(payload: unknown): number[] {
  if (payload == null) return [];
  if (Array.isArray(payload)) return mergeTaxYears(payload);
  if (typeof payload !== "object") {
    const year = taxYearFromUnknown(payload);
    return year != null ? [year] : [];
  }

  const record = payload as Record<string, unknown>;
  const lists: unknown[][] = [
    record.years,
    record.tax_years,
    record.taxYears,
    record.available_years,
    record.availableYears,
    record.distribution_years,
    record.distributionYears,
    record.calendar_years,
    record.calendarYears,
  ].map((value) => (Array.isArray(value) ? value : value == null ? [] : [value]));
  const facets = record.facets;
  if (facets && typeof facets === "object") {
    lists.push(taxYearsFromPayload(facets));
  }
  if (record.coverage && typeof record.coverage === "object") {
    lists.push(taxYearsFromPayload(record.coverage));
  }
  return mergeTaxYears(...lists);
}
