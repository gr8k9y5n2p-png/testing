import { PRODUCTION_ORIGIN, publicOrigin } from "@/lib/hosts";
import { allowDemoEngine, readRuntimeEnv } from "./runtime-env.ts";

export {
  allowDemoEngine,
  isProductionRuntime,
  readRuntimeEnv,
} from "./runtime-env.ts";

/** Production apex. Brand chrome and ads-ready canonical. */
export const AFTERTAX_ORIGIN = PRODUCTION_ORIGIN;

function isBrowser(): boolean {
  return typeof window !== "undefined";
}

export function sameOriginApiUrl(path: string): string {
  const clean = path.startsWith("/") ? path : `/${path}`;
  return `/api${clean}`;
}

export function getDataApiBaseUrl(): string | null {
  const value = readRuntimeEnv("NEXT_PUBLIC_DATA_API_URL");
  return value ? value.replace(/\/$/, "") : null;
}

/** Same-origin mock path, or the Data API host + path when NEXT_PUBLIC_DATA_API_URL is set. */
export function dataApiUrl(path: string): string {
  const clean = path.startsWith("/") ? path : `/${path}`;
  const base = getDataApiBaseUrl();
  return base ? `${base}${clean}` : `/api${clean}`;
}

/**
 * Browser always posts same-origin `/api/illustrate` so a missing client
 * bundle env cannot skip the server proxy. Server may still use the live host.
 */
export function getIllustrateEndpoint(): string {
  if (isBrowser()) return sameOriginApiUrl("/illustrate");
  const override = readRuntimeEnv("NEXT_PUBLIC_ILLUSTRATE_URL");
  if (override) return override.replace(/\/$/, "");
  return dataApiUrl("/illustrate");
}

/** Demo/seed illustrate — not "the URL starts with /". Same-origin can proxy live. */
export function isMockIllustrateEndpoint(_endpoint = getIllustrateEndpoint()): boolean {
  return allowDemoEngine();
}

export function isRemoteDataApi(): boolean {
  return Boolean(getDataApiBaseUrl());
}

/** Live illustrate host from Vercel env (server runtime, not only the client bundle). */
export function getLiveIllustrateUrl(path = "/illustrate"): string | null {
  const clean = path.startsWith("/") ? path : `/${path}`;
  if (clean === "/illustrate") {
    const override = readRuntimeEnv("NEXT_PUBLIC_ILLUSTRATE_URL");
    if (override) return override.replace(/\/$/, "");
  }
  if (clean === "/illustrate/compare") {
    const override = readRuntimeEnv("NEXT_PUBLIC_COMPARE_URL");
    if (override) return override.replace(/\/$/, "");
  }
  if (clean === "/illustrate/portfolio/compare") {
    const override = readRuntimeEnv("NEXT_PUBLIC_PORTFOLIO_COMPARE_URL");
    if (override) return override.replace(/\/$/, "");
  }
  const base = getDataApiBaseUrl();
  return base ? `${base}${clean}` : null;
}

export async function proxyLiveDataApiPost(
  url: string,
  body: unknown,
): Promise<Response> {
  return fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
  });
}

/** Checkout return URLs default to staging until ads are green-lit. */
export function checkoutUrls() {
  const origin = publicOrigin();
  return {
    success_url: `${origin}/?checkout=success`,
    cancel_url: `${origin}/?checkout=cancel`,
  };
}
