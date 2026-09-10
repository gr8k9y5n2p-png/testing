import type {
  ComparePeriodOut,
  CompareUpcomingDistribution,
} from "./compare-types.ts";
import { isUpcomingPublicationStage } from "./publication-stage.ts";

/** Announced / upcoming chip payload. `null` hides the slot. */
export type UpcomingSummary = {
  dollars: number | null;
  asOf?: string | null;
  publicationStage?: string | null;
  label?: string | null;
  announced: boolean;
};

const UNANNOUNCED_STAGES = new Set([
  "",
  "unannounced",
  "not_announced",
  "none",
  "not announced",
]);

export function isAnnouncedStage(stage?: string | null): boolean {
  if (stage == null) return false;
  return !UNANNOUNCED_STAGES.has(stage.trim().toLowerCase());
}

/**
 * Sell-before-record: Upcoming only if unpaid announced.
 * Dollars alone are not enough — YoY / annual tax must not become a badge.
 */
export function sideIsAnnounced(
  dollars?: number | null,
  stage?: string | null,
): boolean {
  if (!isUpcomingPublicationStage(stage)) return false;
  return dollars != null || isAnnouncedStage(stage);
}

function nearlyEqualDollars(left: number | null | undefined, right: number | null | undefined) {
  if (left == null || right == null) return false;
  const leftN = Number(left);
  const rightN = Number(right);
  // Published $0 must not look like a copy of a $0 calendar-year tax cell.
  if (Math.abs(leftN) < 0.51 && Math.abs(rightN) < 0.51) return false;
  return Math.abs(leftN - rightN) < 0.51;
}

function periodTaxForSide(
  period: ComparePeriodOut,
  side: "left" | "right",
): number | null {
  const totals = period[side]?.totals;
  const value = totals?.estimated_tax ?? totals?.estimated_tax_dollars;
  if (value == null) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

/** True when upcoming $ is a copy of a calendar-year period (annual tax, not unpaid). */
export function upcomingLooksLikeAnnualTax(
  upcoming: CompareUpcomingDistribution | null | undefined,
  periods?: ComparePeriodOut[] | null,
  side: "left" | "right" | "either" = "either",
): boolean {
  if (!upcoming || !periods?.length) return false;
  const check = (prefer: "left" | "right") => {
    const dollars = prefer === "right" ? upcoming.right_dollars : upcoming.left_dollars;
    return periods.some((period) => nearlyEqualDollars(dollars, periodTaxForSide(period, prefer)));
  };
  if (side === "either") return check("left") || check("right");
  return check(side);
}

/**
 * Drop invented / historical upcoming. Null or paid/final stage → undisclosed.
 * Do not weaken the unpaid-only gate.
 */
export function gateCompareUpcoming(
  upcoming?: CompareUpcomingDistribution | null,
  periods?: ComparePeriodOut[] | null,
): CompareUpcomingDistribution | null {
  if (!upcoming) return null;
  const leftOk =
    sideIsAnnounced(upcoming.left_dollars, upcoming.left_publication_stage) &&
    !upcomingLooksLikeAnnualTax(upcoming, periods, "left");
  const rightOk =
    sideIsAnnounced(upcoming.right_dollars, upcoming.right_publication_stage) &&
    !upcomingLooksLikeAnnualTax(upcoming, periods, "right");
  if (!leftOk && !rightOk) return null;
  return {
    ...upcoming,
    left_dollars: leftOk ? upcoming.left_dollars ?? null : null,
    right_dollars: rightOk ? upcoming.right_dollars ?? null : null,
    left_publication_stage: leftOk ? upcoming.left_publication_stage ?? null : null,
    right_publication_stage: rightOk ? upcoming.right_publication_stage ?? null : null,
    left_as_of: leftOk ? upcoming.left_as_of ?? null : null,
    right_as_of: rightOk ? upcoming.right_as_of ?? null : null,
    delta_dollars: leftOk && rightOk ? upcoming.delta_dollars ?? null : null,
  };
}

function formatUpcomingUsd(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export function toUpcomingSummary(
  upcoming?: CompareUpcomingDistribution | null,
  prefer: "left" | "right" | "either" = "either",
  periods?: ComparePeriodOut[] | null,
): UpcomingSummary | null {
  const gated = gateCompareUpcoming(upcoming, periods);
  if (!gated) return null;

  const leftAnnounced = sideIsAnnounced(
    gated.left_dollars,
    gated.left_publication_stage,
  );
  const rightAnnounced = sideIsAnnounced(
    gated.right_dollars,
    gated.right_publication_stage,
  );

  const pick =
    prefer === "left"
      ? {
          dollars: gated.left_dollars ?? null,
          asOf: gated.left_as_of ?? null,
          publicationStage: gated.left_publication_stage ?? null,
          announced: leftAnnounced,
        }
      : prefer === "right"
        ? {
            dollars: gated.right_dollars ?? null,
            asOf: gated.right_as_of ?? null,
            publicationStage: gated.right_publication_stage ?? null,
            announced: rightAnnounced,
          }
        : rightAnnounced
          ? {
              dollars: gated.right_dollars ?? null,
              asOf: gated.right_as_of ?? null,
              publicationStage: gated.right_publication_stage ?? null,
              announced: true,
            }
          : {
              dollars: gated.left_dollars ?? null,
              asOf: gated.left_as_of ?? null,
              publicationStage: gated.left_publication_stage ?? null,
              announced: leftAnnounced,
            };

  if (!pick.announced && pick.dollars == null) return null;
  return {
    ...pick,
    label: pick.announced
      ? pick.dollars != null
        ? `Upcoming · ${formatUpcomingUsd(pick.dollars)}`
        : "Upcoming"
      : "Not announced",
  };
}
