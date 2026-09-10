/**
 * Data `coverage_status` (`awaiting_estimate` | `estimate_announced`)
 * when present on /funds. A miss is empty exact-ticker /funds +
 * POST /request/ticker (`not_in_universe`). Prefer the published field
 * when present; otherwise infer from /funds hit + has_estimate / Upcoming.
 */

export const COVERAGE_STATUSES = [
  "awaiting_estimate",
  "estimate_announced",
  "not_in_universe",
] as const;

export type CoverageStatus = (typeof COVERAGE_STATUSES)[number];

export const AWAITING_ESTIMATE_LABEL = "Awaiting Estimate";
export const ADD_TO_UNIVERSE_LABEL = "Add to universe";

function normalizeCoverageStatus(raw: unknown): CoverageStatus | null {
  const key = String(raw ?? "")
    .trim()
    .toLowerCase()
    .replace(/[\s-]+/g, "_");
  if (key === "awaiting_estimate" || key === "awaiting") return "awaiting_estimate";
  if (key === "estimate_announced" || key === "announced") return "estimate_announced";
  if (key === "not_in_universe" || key === "not_found") return "not_in_universe";
  return null;
}

export function resolveCoverageStatus(input: {
  coverageStatus?: unknown;
  foundInFunds?: boolean;
  hasEstimate?: boolean | null;
  hasUpcoming?: boolean;
}): CoverageStatus {
  const published = normalizeCoverageStatus(input.coverageStatus);
  if (published) return published;
  if (input.foundInFunds === false) return "not_in_universe";
  if (input.hasUpcoming === true || input.hasEstimate === true) {
    return "estimate_announced";
  }
  if (input.foundInFunds === true) return "awaiting_estimate";
  return "not_in_universe";
}

/** Chip on Search matches. Null when announced or unknown. */
export function fundPickerCoverageLabel(fund: {
  coverageStatus?: unknown;
  hasEstimate?: boolean | null;
  bucket?: string | null;
}): string | null {
  const status = resolveCoverageStatus({
    coverageStatus: fund.coverageStatus,
    foundInFunds: true,
    hasEstimate: fund.hasEstimate,
    hasUpcoming: fund.bucket === "upcoming" || fund.hasEstimate === true,
  });
  return status === "awaiting_estimate" ? AWAITING_ESTIMATE_LABEL : null;
}
