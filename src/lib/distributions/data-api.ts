import { getDataApiBaseUrl } from "@/lib/data-api/config";

export { getDataApiBaseUrl };

export async function pingDistributionsApi(): Promise<boolean> {
  const base = getDataApiBaseUrl();
  if (!base) return false;
  try {
    const response = await fetch(`${base}/health`);
    return response.ok;
  } catch {
    return false;
  }
}

export async function fetchFundFamilies() {
  const base = getDataApiBaseUrl();
  const endpoint = base ? `${base}/fund-families` : null;
  if (!endpoint) return null;
  try {
    const response = await fetch(endpoint);
    if (!response.ok) return null;
    return (await response.json()) as unknown;
  } catch {
    return null;
  }
}

export async function fetchCoverage() {
  const base = getDataApiBaseUrl();
  const endpoint = base ? `${base}/coverage` : "/api/coverage/gaps";
  try {
    const response = await fetch(endpoint);
    if (!response.ok) return null;
    return (await response.json()) as unknown;
  } catch {
    return null;
  }
}
