/**
 * Charge-ready freemium limits (locked 2026-09-19).
 * Soft wall after these — blur + CTA, not a homepage hard block.
 * Homepage Upcoming / Announced is subscription-gated (not usage-counted).
 */

export const FREE_SEARCH_LIMIT = 5;
export const FREE_COMPARE_LIMIT = 3;
export const FREE_PORTFOLIO_LIMIT = 3;

export const FREEMIUM_COOKIE = "aftertax_freemium";
export const FREEMIUM_STORAGE_KEY = "aftertax.freemium.v2";
export const FREEMIUM_COOKIE_MAX_AGE_SEC = 400 * 24 * 60 * 60;

export type UsageKind = "search" | "compare" | "portfolio";

export type DeviceUsage = {
  searches: number;
  compareKeys: string[];
  portfolioKeys: string[];
};

export type Entitlement = {
  configured: boolean;
  secretConfigured: boolean;
  subscribed: boolean;
  subscriptionStatus: string | null;
  cancelAtPeriodEnd: boolean;
  currentPeriodEnd: string | null;
  signedIn: boolean;
  bypass: boolean;
  usage: DeviceUsage;
  remaining: {
    searches: number;
    compares: number;
    portfolios: number;
  };
  walls: {
    search: boolean;
    compare: boolean;
    portfolio: boolean;
    /** Entire Lists tab — not usage-counted. True unless subscribed or bypass. */
    lists: boolean;
    /** Homepage Upcoming / Announced — not usage-counted. True unless subscribed or bypass. */
    upcoming: boolean;
  };
  detail: string | null;
};

export const EMPTY_USAGE: DeviceUsage = {
  searches: 0,
  compareKeys: [],
  portfolioKeys: [],
};

/**
 * Soft-wall is ON unless NEXT_PUBLIC_FREEMIUM_DISABLED is explicitly
 * true / 1 / on. Charge-ready default — no Vercel flag required.
 */
export function isFreemiumDisabled(
  env: NodeJS.ProcessEnv = process.env,
): boolean {
  const raw = env.NEXT_PUBLIC_FREEMIUM_DISABLED;
  if (raw == null || raw.trim() === "") return false;
  const normalized = raw.trim().toLowerCase();
  return normalized === "true" || normalized === "1" || normalized === "on";
}

export function emptyUsage(): DeviceUsage {
  return {
    searches: 0,
    compareKeys: [],
    portfolioKeys: [],
  };
}

/** Parse `aftertax_freemium` (raw JSON or URI-encoded). */
export function usageFromCookieValue(
  raw: string | null | undefined,
): DeviceUsage {
  if (raw == null || raw.trim() === "") return emptyUsage();
  const attempts = [raw];
  try {
    attempts.push(decodeURIComponent(raw));
  } catch {
    /* keep raw only */
  }
  for (const attempt of attempts) {
    try {
      return normalizeUsage(JSON.parse(attempt));
    } catch {
      /* try next encoding */
    }
  }
  return emptyUsage();
}

export function normalizeUsage(value: unknown): DeviceUsage {
  if (!value || typeof value !== "object") return emptyUsage();
  const raw = value as Partial<DeviceUsage>;
  const searches = Number(raw.searches);
  return {
    searches: Number.isFinite(searches) && searches > 0 ? Math.floor(searches) : 0,
    compareKeys: uniqueKeys(raw.compareKeys),
    portfolioKeys: uniqueKeys(raw.portfolioKeys),
  };
}

export function uniqueKeys(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  const seen = new Set<string>();
  for (const item of value) {
    if (typeof item !== "string") continue;
    const key = item.trim();
    if (!key || seen.has(key)) continue;
    seen.add(key);
  }
  return [...seen];
}

export function compareSessionKey(tickers: string[]): string {
  return [...new Set(tickers.map((ticker) => ticker.trim().toUpperCase()).filter(Boolean))]
    .sort()
    .join(",");
}

export function portfolioReviewKey(current: string[], proposed: string[]): string {
  return `${compareSessionKey(current)}|${compareSessionKey(proposed)}`;
}

export function incrementUsage(
  current: DeviceUsage,
  kind: UsageKind,
  key?: string,
): DeviceUsage {
  const next = {
    searches: current.searches,
    compareKeys: [...current.compareKeys],
    portfolioKeys: [...current.portfolioKeys],
  };
  if (kind === "search") {
    next.searches += 1;
    return next;
  }
  const normalized = key?.trim();
  if (!normalized) return next;
  if (kind === "compare" && !next.compareKeys.includes(normalized)) {
    next.compareKeys.push(normalized);
  }
  if (kind === "portfolio" && !next.portfolioKeys.includes(normalized)) {
    next.portfolioKeys.push(normalized);
  }
  return next;
}

/** Login merge: take the higher usage so signing in cannot reset a device. */
export function mergeUsage(account: DeviceUsage, device: DeviceUsage): DeviceUsage {
  return {
    searches: Math.max(account.searches, device.searches),
    compareKeys: uniqueKeys([...account.compareKeys, ...device.compareKeys]),
    portfolioKeys: uniqueKeys([...account.portfolioKeys, ...device.portfolioKeys]),
  };
}

export function usageWalls(usage: DeviceUsage): {
  search: boolean;
  compare: boolean;
  portfolio: boolean;
} {
  return {
    search: usage.searches >= FREE_SEARCH_LIMIT,
    compare: usage.compareKeys.length >= FREE_COMPARE_LIMIT,
    portfolio: usage.portfolioKeys.length >= FREE_PORTFOLIO_LIMIT,
  };
}

export function remainingFromUsage(usage: DeviceUsage): {
  searches: number;
  compares: number;
  portfolios: number;
} {
  return {
    searches: Math.max(0, FREE_SEARCH_LIMIT - usage.searches),
    compares: Math.max(0, FREE_COMPARE_LIMIT - usage.compareKeys.length),
    portfolios: Math.max(0, FREE_PORTFOLIO_LIMIT - usage.portfolioKeys.length),
  };
}

const ENTITLED = new Set(["active", "trialing", "past_due"]);

export function isSubscriptionEntitled(input: {
  subscriptionStatus?: string | null;
  cancelAtPeriodEnd?: boolean;
  currentPeriodEnd?: string | null;
}): boolean {
  const status = input.subscriptionStatus?.trim().toLowerCase() ?? "";
  if (ENTITLED.has(status)) return true;
  if (status === "canceled" || input.cancelAtPeriodEnd) {
    const end = input.currentPeriodEnd ? Date.parse(input.currentPeriodEnd) : NaN;
    return Number.isFinite(end) && end > Date.now();
  }
  return false;
}
