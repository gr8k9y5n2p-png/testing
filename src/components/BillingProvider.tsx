"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useAccountSession } from "@/components/AccountSession";
import {
  EMPTY_USAGE,
  FREEMIUM_STORAGE_KEY,
  incrementUsage,
  isFreemiumDisabled,
  mergeUsage,
  normalizeUsage,
  remainingFromUsage,
  usageWalls,
  type DeviceUsage,
  type UsageKind,
} from "@/lib/billing/limits";
import {
  ENTITLEMENT_API_PATH,
  USAGE_API_PATH,
} from "@/lib/stripe/billing-copy";
import type { Entitlement } from "@/lib/billing/limits";
import { startCheckout, startCustomerPortal } from "@/lib/stripe/client-actions";

type BillingContextValue = {
  entitlement: Entitlement;
  remaining: Entitlement["remaining"];
  walls: Entitlement["walls"];
  unlimited: boolean;
  configured: boolean;
  subscribed: boolean;
  signedIn: boolean;
  recordSearch: () => void;
  recordCompare: (key: string) => void;
  recordPortfolio: (key: string) => void;
  unlock: () => Promise<{ url?: string; detail: string; needsAccount?: boolean }>;
  manageBilling: () => Promise<{ url?: string; detail: string; needsAccount?: boolean }>;
  refresh: () => Promise<void>;
};

const BillingContext = createContext<BillingContextValue | null>(null);

function readDeviceUsage(): DeviceUsage {
  if (typeof window === "undefined") return { ...EMPTY_USAGE };
  try {
    const raw = window.localStorage.getItem(FREEMIUM_STORAGE_KEY);
    return raw ? normalizeUsage(JSON.parse(raw)) : { ...EMPTY_USAGE };
  } catch {
    return { ...EMPTY_USAGE };
  }
}

function writeDeviceUsage(usage: DeviceUsage) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(FREEMIUM_STORAGE_KEY, JSON.stringify(usage));
}

function localEntitlement(usage: DeviceUsage, subscribed: boolean): Entitlement {
  const bypass = isFreemiumDisabled();
  const remaining = remainingFromUsage(usage);
  const walls = usageWalls(usage);
  const unlimited = bypass || subscribed;
  return {
    configured: Boolean(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY?.trim()),
    secretConfigured: false,
    subscribed,
    subscriptionStatus: null,
    cancelAtPeriodEnd: false,
    currentPeriodEnd: null,
    signedIn: subscribed,
    bypass,
    usage,
    remaining,
    walls: {
      search: unlimited ? false : walls.search,
      compare: unlimited ? false : walls.compare,
      portfolio: unlimited ? false : walls.portfolio,
    },
    detail: process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY?.trim()
      ? null
      : "Billing is not configured. Add Stripe keys in Vercel to enable Checkout.",
  };
}

export function BillingProvider({ children }: { children: ReactNode }) {
  const { account } = useAccountSession();
  const [entitlement, setEntitlement] = useState<Entitlement>(() =>
    localEntitlement(readDeviceUsage(), Boolean(account?.subscribed)),
  );
  const apply = useCallback((next: Entitlement) => {
    const usage = mergeUsage(readDeviceUsage(), next.usage);
    const remaining = remainingFromUsage(usage);
    const walls = usageWalls(usage);
    const unlimited = next.bypass || next.subscribed;
    const merged: Entitlement = {
      ...next,
      usage,
      remaining,
      walls: {
        search: unlimited ? false : walls.search,
        compare: unlimited ? false : walls.compare,
        portfolio: unlimited ? false : walls.portfolio,
      },
    };
    setEntitlement(merged);
    writeDeviceUsage(usage);
  }, []);

  const refresh = useCallback(async () => {
    try {
      const response = await fetch(ENTITLEMENT_API_PATH, {
        credentials: "same-origin",
        headers: { accept: "application/json" },
      });
      if (!response.ok) return;
      const body = (await response.json()) as Entitlement;
      apply(body);
    } catch {
      /* keep local snapshot */
    }
  }, [apply]);

  useEffect(() => {
    let cancelled = false;
    const timer = window.setTimeout(() => {
      const load = account?.id
        ? fetch(USAGE_API_PATH, {
            method: "POST",
            credentials: "same-origin",
            headers: {
              accept: "application/json",
              "content-type": "application/json",
            },
            body: JSON.stringify({ merge: readDeviceUsage() }),
          })
        : fetch(ENTITLEMENT_API_PATH, {
            credentials: "same-origin",
            headers: { accept: "application/json" },
          });
      void load
        .then((response) => (response.ok ? response.json() : null))
        .then((body: Entitlement | null) => {
          if (!cancelled && body) apply(body);
        })
        .catch(() => {
          /* keep local snapshot */
        });
    }, 0);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [account?.id, apply]);

  const postKind = useCallback(
    (kind: UsageKind, key?: string) => {
      const next = incrementUsage(readDeviceUsage(), kind, key);
      writeDeviceUsage(next);
      setEntitlement((current) => {
        const usage = mergeUsage(current.usage, next);
        return localEntitlement(usage, current.subscribed || Boolean(account?.subscribed));
      });
      void fetch(USAGE_API_PATH, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          accept: "application/json",
          "content-type": "application/json",
        },
        body: JSON.stringify({ kind, key }),
      })
        .then((response) => (response.ok ? response.json() : null))
        .then((body: Entitlement | null) => {
          if (body) apply(body);
        })
        .catch(() => {
          /* local increment already applied */
        });
    },
    [account?.subscribed, apply],
  );

  const recordSearch = useCallback(() => {
    postKind("search");
  }, [postKind]);

  const recordCompare = useCallback(
    (key: string) => {
      if (!key.trim()) return;
      postKind("compare", key);
    },
    [postKind],
  );

  const recordPortfolio = useCallback(
    (key: string) => {
      if (!key.trim()) return;
      postKind("portfolio", key);
    },
    [postKind],
  );

  const unlock = useCallback(async () => {
    const result = await startCheckout();
    if (result.url) {
      window.location.assign(result.url);
    }
    return result;
  }, []);

  const manageBilling = useCallback(async () => {
    const result = entitlement.subscribed
      ? await startCustomerPortal()
      : await startCheckout();
    if (result.url) {
      window.location.assign(result.url);
    }
    return result;
  }, [entitlement.subscribed]);

  const unlimited = entitlement.bypass || entitlement.subscribed;
  const value = useMemo<BillingContextValue>(
    () => ({
      entitlement,
      remaining: entitlement.remaining,
      walls: entitlement.walls,
      unlimited,
      configured: entitlement.configured,
      subscribed: entitlement.subscribed,
      signedIn: Boolean(account) || entitlement.signedIn,
      recordSearch,
      recordCompare,
      recordPortfolio,
      unlock,
      manageBilling,
      refresh,
    }),
    [
      account,
      entitlement,
      manageBilling,
      recordCompare,
      recordPortfolio,
      recordSearch,
      refresh,
      unlimited,
      unlock,
    ],
  );

  return (
    <BillingContext.Provider value={value}>{children}</BillingContext.Provider>
  );
}

export function useBilling(): BillingContextValue {
  const context = useContext(BillingContext);
  if (!context) {
    throw new Error("useBilling must be used within BillingProvider");
  }
  return context;
}
