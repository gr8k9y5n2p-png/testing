/**
 * Dynamic `process.env[name]` so Vercel runtime values still win when Next
 * inlined an empty `NEXT_PUBLIC_*` at build time.
 */
export function readRuntimeEnv(name: string): string | null {
  const value = process.env[name];
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

/** Production / Vercel preview: never seed math, never MOCK banners. */
export function isProductionRuntime(): boolean {
  if (process.env.NODE_ENV === "production") return true;
  const vercel = readRuntimeEnv("VERCEL_ENV");
  return vercel === "production" || vercel === "preview";
}

/**
 * Localhost demo engine only. False when NODE_ENV=production or any live
 * Data API / illustrate URL is present (build-time or server runtime).
 */
export function allowDemoEngine(): boolean {
  if (isProductionRuntime()) return false;
  if (readRuntimeEnv("NEXT_PUBLIC_DATA_API_URL")) return false;
  if (readRuntimeEnv("NEXT_PUBLIC_ILLUSTRATE_URL")) return false;
  if (readRuntimeEnv("NEXT_PUBLIC_COMPARE_URL")) return false;
  if (readRuntimeEnv("NEXT_PUBLIC_PORTFOLIO_COMPARE_URL")) return false;
  return true;
}
