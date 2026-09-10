import {
  distributionBucket,
  normalizePublicationStage,
  type DistributionBucket,
} from "../../data/distribution-bucket.ts";
import type { FundEstimate } from "../../data/types.ts";
import type { IllustrationComponent, IllustrationTotals } from "./types.ts";

export type IllustrationFundGate = Pick<
  FundEstimate,
  "hasEstimate" | "publicationStage" | "bucket"
> | null | undefined;

/**
 * Dollar Illustration Upcoming for every fund: unpaid prelim/estimate
 * components only. `has_estimate: false` and `final` / paid YE rows stay
 * out of Upcoming. Live illustrate may omit `publication_stage` on an
 * unpaid prelim (FBGRX) — inherit the /distributions stage so a
 * still-future unpaid estimate is not treated as paid/stale.
 * Never treat holding-scaled illustration totals as Upcoming — and never
 * as Paid history (Paid history is `/distributions`).
 */
export function illustrationComponentBucket(
  component: Pick<
    IllustrationComponent,
    "as_of" | "record_date" | "ex_date" | "payable_date" | "publication_stage"
  >,
  fund?: IllustrationFundGate,
): DistributionBucket {
  // Live illustrate often omits publication_stage (FBGRX). Inherit the
  // /distributions stage so a still-future unpaid prelim is not paid/stale.
  const inheritedStage =
    normalizePublicationStage(component.publication_stage) ??
    normalizePublicationStage(fund?.publicationStage);
  if (fund?.hasEstimate === false && fund.bucket !== "upcoming") {
    return "paid";
  }
  return distributionBucket({
    asOfDate: component.as_of,
    recordDate: component.record_date,
    exDate: component.ex_date,
    payableDate: component.payable_date,
    publicationStage: inheritedStage,
  });
}

export function splitIllustrationComponents(
  components: IllustrationComponent[],
  fund?: IllustrationFundGate,
): { upcoming: IllustrationComponent[]; paid: IllustrationComponent[] } {
  const upcoming: IllustrationComponent[] = [];
  const paid: IllustrationComponent[] = [];
  for (const component of components) {
    if (illustrationComponentBucket(component, fund) === "upcoming") {
      upcoming.push(component);
    } else {
      paid.push(component);
    }
  }
  return { upcoming, paid };
}

function num(value: number | string | null | undefined): number | null {
  if (value == null || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function sumNullable(
  values: Array<number | null>,
): number | null {
  if (values.every((value) => value == null)) return null;
  return values.reduce<number>((sum, value) => sum + (value ?? 0), 0);
}

function isRollupTotal(type: string | null | undefined): boolean {
  return (type ?? "").trim().toLowerCase() === "total";
}

/**
 * Totals for the Upcoming StatCards — unpaid prelim components only.
 * Live illustrate returns dollar fields as strings and may emit both
 * per_share and percent_of_nav rows for the same event (FBGRX) — prefer
 * typed per_share so Dist $ is not double-counted. Empty / all-null →
 * null so the UI shows Undisclosed, never $0 or paid YE $.
 */
export function upcomingIllustrationTotals(
  upcoming: IllustrationComponent[],
): IllustrationTotals | null {
  const typed = upcoming.filter((row) => !isRollupTotal(row.estimate_type));
  const source = typed.length ? typed : upcoming;
  const perShare = source.filter((row) => row.amount_unit === "per_share");
  const rows = perShare.length ? perShare : source;
  if (!rows.length) return null;
  const distribution = sumNullable(rows.map((row) => num(row.distribution_dollars)));
  const tax = sumNullable(rows.map((row) => num(row.estimated_tax_dollars)));
  if (distribution == null && tax == null) return null;
  return {
    distribution_dollars: distribution ?? 0,
    distribution_dollars_min: sumNullable(
      rows.map((row) => num(row.distribution_dollars_min)),
    ),
    distribution_dollars_max: sumNullable(
      rows.map((row) => num(row.distribution_dollars_max)),
    ),
    estimated_tax_dollars: tax ?? 0,
    estimated_tax_dollars_min: sumNullable(
      rows.map((row) => num(row.estimated_tax_dollars_min)),
    ),
    estimated_tax_dollars_max: sumNullable(
      rows.map((row) => num(row.estimated_tax_dollars_max)),
    ),
  };
}
