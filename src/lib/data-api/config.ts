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

/** Checkout return URLs default to staging until ads are green-lit. */
export function checkoutUrls() {
  const origin = publicOrigin();
  return {
    success_url: `${origin}/?checkout=success`,
    cancel_url: `${origin}/?checkout=cancel`,
  };
}
