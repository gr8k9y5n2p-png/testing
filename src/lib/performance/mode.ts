import type { PerformanceMode } from "./types";

function remoteDataApiConfigured(
  env: NodeJS.ProcessEnv = process.env,
): boolean {
  return Boolean(env.NEXT_PUBLIC_DATA_API_URL?.trim());
}

/**
 * Remote Data API → live. Local same-origin mock / tests without
 * NEXT_PUBLIC_DATA_API_URL → fixture. Never default remote calls to fixture.
 */
export function defaultPerformanceMode(
  env: NodeJS.ProcessEnv = process.env,
): PerformanceMode {
  return remoteDataApiConfigured(env) ? "live" : "fixture";
}

/**
 * Resolve the mode sent on GET /performance and POST /performance/growth.
 * Live/auto are always honored. Fixture is kept only off the Data API.
 * When the live host is configured, fixture is rewritten to live so Compare
 * / Growth never force mock packs in Production.
 */
export function resolvePerformanceMode(
  requested?: string | null,
  env: NodeJS.ProcessEnv = process.env,
): PerformanceMode {
  const mode = requested?.trim().toLowerCase();
  if (remoteDataApiConfigured(env)) {
    return mode === "auto" ? "auto" : "live";
  }
  if (mode === "live" || mode === "auto" || mode === "fixture") {
    return mode;
  }
  return "fixture";
}
