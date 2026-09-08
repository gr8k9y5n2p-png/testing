import type { PerformanceResponse } from "./types";

/** Advisor-facing empty state when GET /performance (or growth) has no pack. */
export const PERFORMANCE_UNAVAILABLE_LABEL = "Performance not available";
export const PERFORMANCE_UNAVAILABLE_HINT =
  "N/A — no performance pack. Aftertax does not invent a growth series.";

const MISSING_CODES = new Set([
  "uncovered",
  "not_found",
  "notfound",
  "no_performance",
  "missing_performance",
  "performance_not_found",
]);

export function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

/**
 * 404 / uncovered / no-pack from GET /performance or POST /performance/growth.
 * Not a hard module failure — skip that series.
 */
export function isMissingPerformanceError(error: unknown): boolean {
  if (!error || typeof error !== "object") return false;
  const status = "status" in error ? Number(error.status) : Number.NaN;
  if (status === 404) return true;
  const code =
    "code" in error && typeof error.code === "string" ? error.code.trim().toLowerCase() : "";
  if (code && MISSING_CODES.has(code)) return true;
  const message = error instanceof Error ? error.message : "";
  return /\buncovered\b/i.test(message);
}

/** Per-ticker fetch failure: skip the series instead of failing the module. */
export function performanceFromFetchError(error: unknown): null {
  if (isAbortError(error)) throw error;
  return null;
}

export function performanceCoveredFromRaw(raw: unknown): boolean | undefined {
  if (raw === false || raw === "false") return false;
  if (raw === true || raw === "true") return true;
  return undefined;
}

/** True when the payload is a real monthly series — never treat empty as $0 history. */
export function performancePackIsUsable(
  response: PerformanceResponse | null | undefined,
): response is PerformanceResponse {
  if (!response) return false;
  if (response.covered === false) return false;
  const points = response.fund?.points ?? [];
  return points.some((point) => {
    if (!point.date) return false;
    return Number.isFinite(point.growth_of_x);
  });
}

export function firstUsablePerformance(
  rows: Array<{ performance: PerformanceResponse | null }>,
): PerformanceResponse | null {
  for (const row of rows) {
    if (performancePackIsUsable(row.performance)) return row.performance;
  }
  return null;
}
