/**
 * Eric-locked NAV math (2026-09-10) for Search / Dollar Illustration /
 * Compare / Portfolio / Lists.
 *
 * Upcoming Dist $ = est $/share × (holding $ ÷ weekly nav_per_share)
 * Aftertax live % of NAV = Dist $/share ÷ latest weekly nav_per_share
 *   (FCPGX $7.277 ÷ $42.94 = 16.9%). Never manager-published
 *   percent_of_nav unless the UI explicitly labels that print
 *   manager-published. publishedPctOfNav is that separately labeled field.
 * Paid / historical % of NAV = Dist $/share ÷ nav_on_distribution_day
 *   (ex-day NAV). Never today's weekly NAV.
 *
 * Missing estimate or NAV → null → UI "—". Never invent.
 */

import {
  isoDate,
  normalizePublicationStage,
  utcTodayIso,
} from "../../data/distribution-bucket.ts";
import { formatOptionalDate, formatPct, formatUsd } from "../format.ts";

export const SOFT_DASH = "—";

export function parseFiniteNumber(value: unknown): number | null {
  if (value == null || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

/** Weekly / distribution-day NAV. 0 and negatives are unknown — never invent. */
export function parsePositiveNav(value: unknown): number | null {
  const parsed = parseFiniteNumber(value);
  return parsed != null && parsed > 0 ? parsed : null;
}

/** Keep a typed NAV; otherwise autofill the live weekly print. Never invent. */
export function fillNavPerShareInput(
  typedInput: unknown,
  liveNav: unknown,
): string {
  if (parsePositiveNav(typedInput) != null) {
    return String(typedInput).trim();
  }
  const nav = parsePositiveNav(liveNav);
  if (nav != null) return String(nav);
  return typeof typedInput === "string" ? typedInput : "";
}

/**
 * Distribution day is ex_date, else payable_date — matches Data.
 * Historical % of NAV uses that day's print when the day is on or before
 * today, or the row is `final` / `paid`. Never fall back to weekly NAV.
 */
export function usesDistributionDayNav(
  row: {
    publicationStage?: string | null;
    publication_stage?: string | null;
    exDate?: string | null;
    ex_date?: string | null;
    payableDate?: string | null;
    payable_date?: string | null;
  },
  today = utcTodayIso(),
): boolean {
  const day =
    isoDate(row.exDate ?? row.ex_date) ??
    isoDate(row.payableDate ?? row.payable_date);
  if (day != null && day <= today) return true;
  const stage = normalizePublicationStage(
    row.publicationStage ?? row.publication_stage,
  );
  return stage === "final" || stage === "paid";
}

/** Upcoming Dist $ = est $/share × (holding $ ÷ weekly NAV). */
export function upcomingDistDollars(
  estPerShare: unknown,
  holdingDollars: unknown,
  weeklyNav: unknown,
): number | null {
  const perShare = parseFiniteNumber(estPerShare);
  const holding = parsePositiveNav(holdingDollars);
  const nav = parsePositiveNav(weeklyNav);
  if (perShare == null || holding == null || nav == null) return null;
  return perShare * (holding / nav);
}

/** Upcoming % of NAV = est $/share ÷ weekly NAV × 100. */
export function upcomingPctOfNav(
  estPerShare: unknown,
  weeklyNav: unknown,
): number | null {
  const perShare = parseFiniteNumber(estPerShare);
  const nav = parsePositiveNav(weeklyNav);
  if (perShare == null || nav == null) return null;
  return (perShare / nav) * 100;
}

/** Historical % of NAV = dist $/share ÷ nav_on_distribution_day × 100. */
export function historicalPctOfNav(
  distPerShare: unknown,
  navOnDistributionDay: unknown,
): number | null {
  const perShare = parseFiniteNumber(distPerShare);
  const nav = parsePositiveNav(navOnDistributionDay);
  if (perShare == null || nav == null) return null;
  return (perShare / nav) * 100;
}

/**
 * Split NAV series by publication: weekly for unpaid Upcoming, day NAV
 * for paid / historical. Callers must not pass weekly NAV as day NAV.
 */
export function pctOfNavForUnpaidOrPaid(input: {
  unpaid: boolean;
  perShare: unknown;
  weeklyNav: unknown;
  navOnDistributionDay: unknown;
}): number | null {
  if (input.unpaid) return upcomingPctOfNav(input.perShare, input.weeklyNav);
  return historicalPctOfNav(input.perShare, input.navOnDistributionDay);
}

/**
 * Issuer-published `amount_unit=percent_of_nav` is left as-is.
 * `percent` (share of income) is not % of NAV — callers must not pass it.
 */
export function publishedPctOfNav(
  amount: unknown,
  amountUnit: string | null | undefined,
): number | null {
  if ((amountUnit ?? "").trim().toLowerCase() !== "percent_of_nav") return null;
  return parseFiniteNumber(amount);
}

export type PctOfNavInputs = {
  /** Sum of published percent_of_nav characters. Null when none published. */
  publishedPctNav?: number | null;
  /** Sum of published per_share characters. */
  perShare?: number | null;
  /** GET /funds weekly nav_per_share. */
  weeklyNav?: number | null;
  /** GET /distributions nav_on_distribution_day. */
  navOnDistributionDay?: number | null;
  publicationStage?: string | null;
  exDate?: string | null;
  payableDate?: string | null;
  today?: string;
};

/**
 * Aftertax % of NAV. Live/upcoming is always Dist $/share ÷ weekly NAV.
 * Historical/paid is Dist $/share ÷ nav_on_distribution_day.
 * Manager-published percent_of_nav is ignored here — keep it on
 * publishedPctOfNav for a separately labeled field only.
 */
export function resolvePctOfNav(input: PctOfNavInputs): number | null {
  if (usesDistributionDayNav(input, input.today)) {
    return historicalPctOfNav(input.perShare, input.navOnDistributionDay);
  }
  return upcomingPctOfNav(input.perShare, input.weeklyNav);
}

/** Search / Lists / Dollar Ill live %: Dist $/share ÷ the correct NAV series. */
export function pctOfNavForFund(
  fund: {
    estimatedDistributionAmount?: number | null;
    estimatedDistributionPctNav?: number | null;
    publishedPctOfNav?: number | null;
    nav?: number | null;
    navOnDistributionDay?: number | null;
    publicationStage?: string | null;
    exDate?: string | null;
    payableDate?: string | null;
  },
  today?: string,
): number | null {
  return resolvePctOfNav({
    perShare: fund.estimatedDistributionAmount,
    weeklyNav: fund.nav,
    navOnDistributionDay: fund.navOnDistributionDay,
    publicationStage: fund.publicationStage,
    exDate: fund.exDate,
    payableDate: fund.payableDate,
    today,
  });
}

export function formatSoftPct(
  value: number | null | undefined,
  digits = 2,
): string {
  if (value == null || !Number.isFinite(value)) return SOFT_DASH;
  return formatPct(value, digits);
}

export function formatSoftNav(
  value: number | null | undefined,
  digits = 2,
): string {
  const nav = parsePositiveNav(value);
  return nav == null ? SOFT_DASH : formatUsd(nav, digits);
}

export function formatWeeklyNavLabel(input: {
  nav?: number | null;
  navAsOf?: string | null;
}): string {
  const price = formatSoftNav(input.nav);
  if (price === SOFT_DASH) return SOFT_DASH;
  const asOf = formatOptionalDate(input.navAsOf);
  return asOf === SOFT_DASH ? price : `${price} as of ${asOf}`;
}
