import { PRODUCTION_ORIGIN, publicOrigin } from "@/lib/hosts";

/** Production apex. Brand chrome and ads-ready canonical. */
export const AFTERTAX_ORIGIN = PRODUCTION_ORIGIN;

export function getDataApiBaseUrl(): string | null {
  const value = process.env.NEXT_PUBLIC_DATA_API_URL?.trim();
  return value ? value.replace(/\/$/, "") : null;
}

/** Same-origin mock path, or the Data API host + path when NEXT_PUBLIC_DATA_API_URL is set. */
export function dataApiUrl(path: string): string {
  const clean = path.startsWith("/") ? path : `/${path}`;
  const base = getDataApiBaseUrl();
  return base ? `${base}${clean}` : `/api${clean}`;
}

export function getIllustrateEndpoint(): string {
  if (process.env.NEXT_PUBLIC_ILLUSTRATE_URL?.trim()) {
    return process.env.NEXT_PUBLIC_ILLUSTRATE_URL.replace(/\/$/, "");
  }
  return dataApiUrl("/illustrate");
}

export function isMockIllustrateEndpoint(endpoint = getIllustrateEndpoint()): boolean {
  return endpoint.startsWith("/");
}

export function isRemoteDataApi(): boolean {
  return Boolean(getDataApiBaseUrl());
}

/** Live illustrate host from Vercel env (server runtime, not only the client bundle). */
export function getLiveIllustrateUrl(path = "/illustrate"): string | null {
  const clean = path.startsWith("/") ? path : `/${path}`;
  if (clean === "/illustrate" && process.env.NEXT_PUBLIC_ILLUSTRATE_URL?.trim()) {
    return process.env.NEXT_PUBLIC_ILLUSTRATE_URL.replace(/\/$/, "");
  }
  if (
    clean === "/illustrate/compare" &&
    process.env.NEXT_PUBLIC_COMPARE_URL?.trim()
  ) {
    return process.env.NEXT_PUBLIC_COMPARE_URL.replace(/\/$/, "");
  }
  if (
    clean === "/illustrate/portfolio/compare" &&
    process.env.NEXT_PUBLIC_PORTFOLIO_COMPARE_URL?.trim()
  ) {
    return process.env.NEXT_PUBLIC_PORTFOLIO_COMPARE_URL.replace(/\/$/, "");
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
