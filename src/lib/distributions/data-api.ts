import { getDataApiBaseUrl, dataApiUrl } from "@/lib/data-api/config";

export { getDataApiBaseUrl, dataApiUrl };

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
