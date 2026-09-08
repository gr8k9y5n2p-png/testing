import { formatCompactUsd } from "@/lib/charts/money-axis";
import { formatUsd } from "@/lib/format";
import type { CompareUpcomingDistribution } from "@/lib/illustrate/compare-types";
import {
  TAX_DRAG_NA_LABEL,
  type TaxDragMetric,
} from "@/lib/illustrate/tax-drag-map";

export {
  TAX_DRAG_NA_LABEL,
  alignTaxDragYears,
  comparePeriodIsCovered,
  illustrationIsMatched,
  taxDragLineFromPeriods,
  toCompareTaxDragSeries,
  toNegativeTaxDrag,
  toTaxDragPeriods,
  unionTaxDragYears,
} from "@/lib/illustrate/tax-drag-map";
export type {
  TaxDragFundSeries,
  TaxDragLinePoint,
  TaxDragMetric,
  TaxDragYearPoint,
} from "@/lib/illustrate/tax-drag-map";

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

export function sideIsAnnounced(
  dollars?: number | null,
  stage?: string | null,
): boolean {
  if (dollars != null) return true;
  return isAnnouncedStage(stage);
}

export function toUpcomingSummary(
  upcoming?: CompareUpcomingDistribution | null,
  prefer: "left" | "right" | "either" = "either",
): UpcomingSummary | null {
  if (!upcoming) return null;

  const leftAnnounced = sideIsAnnounced(
    upcoming.left_dollars,
    upcoming.left_publication_stage,
  );
  const rightAnnounced = sideIsAnnounced(
    upcoming.right_dollars,
    upcoming.right_publication_stage,
  );

  const pick =
    prefer === "left"
      ? {
          dollars: upcoming.left_dollars ?? null,
          asOf: upcoming.left_as_of ?? null,
          publicationStage: upcoming.left_publication_stage ?? null,
          announced: leftAnnounced,
        }
      : prefer === "right"
        ? {
            dollars: upcoming.right_dollars ?? null,
            asOf: upcoming.right_as_of ?? null,
            publicationStage: upcoming.right_publication_stage ?? null,
            announced: rightAnnounced,
          }
        : rightAnnounced
          ? {
              dollars: upcoming.right_dollars ?? null,
              asOf: upcoming.right_as_of ?? null,
              publicationStage: upcoming.right_publication_stage ?? null,
              announced: true,
            }
          : {
              dollars: upcoming.left_dollars ?? null,
              asOf: upcoming.left_as_of ?? null,
              publicationStage: upcoming.left_publication_stage ?? null,
              announced: leftAnnounced,
            };

  if (!pick.announced && pick.dollars == null) return null;
  return {
    ...pick,
    label: pick.announced
      ? pick.dollars != null
        ? `Upcoming · ${formatUsd(pick.dollars, 0)}`
        : "Upcoming"
      : "Not announced",
  };
}

export function formatTaxDragPoint(
  value: number | null | undefined,
  metric: TaxDragMetric,
): string {
  if (value == null) return TAX_DRAG_NA_LABEL;
  return formatTaxDragValue(value, metric);
}

export function formatTaxDragValue(
  value: number,
  metric: TaxDragMetric,
): string {
  if (metric === "effective_tax") {
    const pct = value * 100;
    if (Math.abs(pct) < 0.005) return "0%";
    const tenths = Number((Math.abs(pct) * 10).toFixed(6));
    const digits = Math.abs(pct) >= 10 || Number.isInteger(tenths) ? 1 : 2;
    return `${pct.toFixed(digits)}%`;
  }
  return Math.abs(value) >= 1000 ? formatCompactUsd(value) : formatUsd(value, 0);
}
