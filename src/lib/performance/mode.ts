import { isRemoteDataApi } from "@/lib/data-api/config";
import type { PerformanceMode } from "@/lib/performance/types";

/**
 * Remote Data API → live. Local same-origin mock / tests without
 * NEXT_PUBLIC_DATA_API_URL → fixture. Never default remote calls to fixture.
 */
export function defaultPerformanceMode(): PerformanceMode {
  return isRemoteDataApi() ? "live" : "fixture";
}

/**
 * Resolve the mode sent on GET /performance and POST /performance/growth.
 * Live/auto are always honored. Fixture is kept only off the Data API.
 * When the live host is configured, fixture is rewritten to live so Compare
 * / Growth never force mock packs in Production.
 */
export function resolvePerformanceMode(
  requested?: string | null,
): PerformanceMode {
  const mode = requested?.trim().toLowerCase();
  if (isRemoteDataApi()) {
    return mode === "auto" ? "auto" : "live";
  }
  if (mode === "live" || mode === "auto" || mode === "fixture") {
    return mode;
  }
  return "fixture";
}
