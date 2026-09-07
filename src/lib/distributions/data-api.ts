/**
 * Optional Data team search API (PR #2).
 * When NEXT_PUBLIC_DATA_API_URL is set, callers can hit GET /distributions.
 * The Aftertax table still uses seeded FundEstimateView until those rows are
 * aggregated (one fund / snapshot rather than one row per estimate_type).
 */
export function getDataApiBaseUrl(): string | null {
  const value = process.env.NEXT_PUBLIC_DATA_API_URL?.trim();
  return value ? value.replace(/\/$/, "") : null;
}

export async function pingDistributionsApi(): Promise<boolean> {
  const base = getDataApiBaseUrl();
  if (!base) return false;
  try {
    const response = await fetch(`${base}/distributions?page_size=1`);
    return response.ok;
  } catch {
    return false;
  }
}
