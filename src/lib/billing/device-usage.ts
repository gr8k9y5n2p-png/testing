import {
  EMPTY_USAGE,
  FREEMIUM_COOKIE,
  FREEMIUM_COOKIE_MAX_AGE_SEC,
  FREEMIUM_STORAGE_KEY,
  mergeUsage,
  normalizeUsage,
  usageFromCookieValue,
  type DeviceUsage,
} from "./limits";

export function readBrowserUsageCookie(): DeviceUsage {
  if (typeof document === "undefined") return emptyCopy();
  const parts = document.cookie.split("; ");
  const prefix = `${FREEMIUM_COOKIE}=`;
  for (const part of parts) {
    if (part.startsWith(prefix)) {
      return usageFromCookieValue(part.slice(prefix.length));
    }
  }
  return emptyCopy();
}

export function writeBrowserUsageCookie(usage: DeviceUsage): void {
  if (typeof document === "undefined") return;
  document.cookie = [
    `${FREEMIUM_COOKIE}=${encodeURIComponent(JSON.stringify(normalizeUsage(usage)))}`,
    "Path=/",
    "SameSite=Lax",
    `Max-Age=${FREEMIUM_COOKIE_MAX_AGE_SEC}`,
  ].join("; ");
}

export function readBrowserUsageStorage(): DeviceUsage {
  if (typeof window === "undefined") return emptyCopy();
  try {
    return usageFromCookieValue(window.localStorage.getItem(FREEMIUM_STORAGE_KEY));
  } catch {
    return emptyCopy();
  }
}

export function writeBrowserUsageStorage(usage: DeviceUsage): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(
      FREEMIUM_STORAGE_KEY,
      JSON.stringify(normalizeUsage(usage)),
    );
  } catch {
    /* private mode / quota */
  }
}

/** Max/union of SSR seed + cookie + localStorage so no source can reset another. */
export function readBrowserUsage(seed: DeviceUsage = EMPTY_USAGE): DeviceUsage {
  return mergeUsage(
    mergeUsage(normalizeUsage(seed), readBrowserUsageCookie()),
    readBrowserUsageStorage(),
  );
}

export function writeBrowserUsage(usage: DeviceUsage): void {
  const next = normalizeUsage(usage);
  writeBrowserUsageStorage(next);
  writeBrowserUsageCookie(next);
}

function emptyCopy(): DeviceUsage {
  return { searches: 0, compareKeys: [], portfolioKeys: [] };
}
