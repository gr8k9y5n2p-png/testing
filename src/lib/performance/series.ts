import type { PerformanceResponse } from "./types.ts";

/** True when GET /performance (or growth) returned monthly fund points. */
export function performanceHasFundSeries(
  response: PerformanceResponse | null | undefined,
): boolean {
  const points = response?.fund?.points;
  return Array.isArray(points) && points.some((point) => Boolean(point.date));
}

export function usablePerformance(
  response: PerformanceResponse | null | undefined,
): PerformanceResponse | null {
  return performanceHasFundSeries(response) ? (response ?? null) : null;
}

/**
 * 404 / empty / unknown-ticker from /performance. Not a reason to invent
 * growth or tax-drag series, and not a reason to fail sibling funds.
 */
export function isPerformanceUnavailable(error: unknown): boolean {
  if (error && typeof error === "object" && "status" in error) {
    const status = Number((error as { status: unknown }).status);
    if (status === 404 || status === 422) return true;
  }
  const message = error instanceof Error ? error.message : String(error ?? "");
  return /no performance fixture|unknown fund ticker|not found|\b404\b/i.test(
    message,
  );
}
