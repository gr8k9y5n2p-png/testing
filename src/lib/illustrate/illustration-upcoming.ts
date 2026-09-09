import {
  distributionBucket,
  type DistributionBucket,
} from "../../data/distribution-bucket.ts";
import type { FundEstimate } from "../../data/types.ts";
import type { IllustrationComponent, IllustrationTotals } from "./types.ts";

export type IllustrationFundGate = Pick<FundEstimate, "hasEstimate"> | null | undefined;

/**
 * Dollar Illustration Upcoming for every fund: unpaid prelim/estimate
 * components only. `has_estimate: false` and `final` / paid YE rows stay
 * out of Upcoming. Never treat holding-scaled illustration totals as
 * Upcoming — and never as Paid history (Paid history is `/distributions`).
 */
export function illustrationComponentBucket(
  component: Pick<
    IllustrationComponent,
    "as_of" | "record_date" | "ex_date" | "payable_date" | "publication_stage"
  >,
  fund?: IllustrationFundGate,
): DistributionBucket {
  if (fund?.hasEstimate === false) return "paid";
  return distributionBucket({
    asOfDate: component.as_of,
    recordDate: component.record_date,
    exDate: component.ex_date,
    payableDate: component.payable_date,
    publicationStage: component.publication_stage,
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

function num(value: number | null | undefined): number | null {
  if (value == null) return null;
  return Number.isFinite(value) ? value : null;
}

function sumNullable(
  values: Array<number | null>,
): number | null {
  if (values.every((value) => value == null)) return null;
  return values.reduce<number>((sum, value) => sum + (value ?? 0), 0);
}

/**
 * Totals for the Upcoming StatCards — unpaid prelim components only.
 * Empty / all-null → null so the UI shows Undisclosed, never $0 or paid YE $.
 */
export function upcomingIllustrationTotals(
  upcoming: IllustrationComponent[],
): IllustrationTotals | null {
  if (!upcoming.length) return null;
  const distribution = sumNullable(upcoming.map((row) => num(row.distribution_dollars)));
  const tax = sumNullable(upcoming.map((row) => num(row.estimated_tax_dollars)));
  if (distribution == null && tax == null) return null;
  return {
    distribution_dollars: distribution ?? 0,
    distribution_dollars_min: sumNullable(
      upcoming.map((row) => num(row.distribution_dollars_min)),
    ),
    distribution_dollars_max: sumNullable(
      upcoming.map((row) => num(row.distribution_dollars_max)),
    ),
    estimated_tax_dollars: tax ?? 0,
    estimated_tax_dollars_min: sumNullable(
      upcoming.map((row) => num(row.estimated_tax_dollars_min)),
    ),
    estimated_tax_dollars_max: sumNullable(
      upcoming.map((row) => num(row.estimated_tax_dollars_max)),
    ),
  };
}
