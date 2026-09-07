import { HOST } from "@/lib/copy";

export const AFTERTAX_ORIGIN = `https://${HOST}`;

export function getDataApiBaseUrl(): string | null {
  const value = process.env.NEXT_PUBLIC_DATA_API_URL?.trim();
  return value ? value.replace(/\/$/, "") : null;
}

export function getIllustrateEndpoint(): string {
  if (process.env.NEXT_PUBLIC_ILLUSTRATE_URL?.trim()) {
    return process.env.NEXT_PUBLIC_ILLUSTRATE_URL.replace(/\/$/, "");
  }
  const base = getDataApiBaseUrl();
  if (base) return `${base}/illustrate`;
  return "/api/illustrate";
}

export function isMockIllustrateEndpoint(endpoint = getIllustrateEndpoint()): boolean {
  return endpoint.startsWith("/");
}

export function checkoutUrls() {
  const origin = process.env.AFTERTAX_PUBLIC_URL?.replace(/\/$/, "") || AFTERTAX_ORIGIN;
  return {
    success_url: `${origin}/?checkout=success`,
    cancel_url: `${origin}/?checkout=cancel`,
  };
}
