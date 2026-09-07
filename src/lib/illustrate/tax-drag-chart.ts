import { formatUsd } from "@/lib/format";
import type {
  CompareIllustration,
  CompareResponse,
  CompareUpcomingDistribution,
} from "@/lib/illustrate/compare-types";

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

function pickMetric(
  illustration: CompareIllustration | null | undefined,
  metric: TaxDragMetric,
): number | null {
  if (!illustration || illustration.matched === false) return null;
  const totals = illustration.totals;
  if (!totals) return null;
  if (metric === "tax_dollars") {
    const tax = totals.estimated_tax_dollars ?? totals.estimated_tax;
    return tax == null ? null : Number(tax);
  }
  const rate = totals.effective_tax_on_holding;
  return rate == null ? null : Number(rate);
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
 * `right` is that vintage, `left` is the prior). Gaps stay `null` when a
 * side is unmatched — years not present in `periods` are not invented.
 */
export function toTaxDragPeriods(
  response: CompareResponse,
  metric: TaxDragMetric = "tax_dollars",
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
    write(period.year, period.left);
  }

  return [...byYear.values()].sort((a, b) => a.year - b.year);
}

/**
 * Overlay series: same calendar years, connecting only real values.
 * Callers that want a descending YoY *change* line can pass their own series.
 */
export function taxDragLineFromPeriods(
  periods: TaxDragYearPoint[],
): TaxDragLinePoint[] {
  return periods.map((point) => ({ year: point.year, value: point.value }));
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

export function formatTaxDragValue(
  value: number,
  metric: TaxDragMetric,
): string {
  if (metric === "effective_tax") {
    return `${(value * 100).toFixed(Math.abs(value * 100) >= 1 ? 1 : 2)}%`;
  }
  return formatUsd(value, 0);
}
