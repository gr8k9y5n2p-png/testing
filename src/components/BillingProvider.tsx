"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useSyncExternalStore,
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
  type Entitlement,
  type UsageKind,
} from "@/lib/billing/limits";
import {
  ENTITLEMENT_API_PATH,
  USAGE_API_PATH,
} from "@/lib/stripe/billing-copy";
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

const listeners = new Set<() => void>();
let cachedRaw: string | null | undefined;
let cachedUsage: DeviceUsage = EMPTY_USAGE;

function emit() {
  listeners.forEach((listener) => listener());
}

function readDeviceUsage(): DeviceUsage {
  if (typeof window === "undefined") return EMPTY_USAGE;
  const raw = window.localStorage.getItem(FREEMIUM_STORAGE_KEY);
  if (raw === cachedRaw) return cachedUsage;
  cachedRaw = raw;
  if (!raw) {
    cachedUsage = EMPTY_USAGE;
    return cachedUsage;
  }
  try {
    cachedUsage = normalizeUsage(JSON.parse(raw));
  } catch {
    cachedUsage = EMPTY_USAGE;
  }
  return cachedUsage;
}

function writeDeviceUsage(usage: DeviceUsage) {
  if (typeof window === "undefined") return;
  const raw = JSON.stringify(usage);
  window.localStorage.setItem(FREEMIUM_STORAGE_KEY, raw);
  cachedRaw = raw;
  cachedUsage = usage;
  emit();
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

type RemoteBilling = Pick<
  Entitlement,
  | "configured"
  | "subscribed"
  | "subscriptionStatus"
  | "cancelAtPeriodEnd"
  | "currentPeriodEnd"
  | "signedIn"
  | "bypass"
  | "detail"
>;

const emptyRemote: RemoteBilling = {
  configured: false,
  subscribed: false,
  subscriptionStatus: null,
  cancelAtPeriodEnd: false,
  currentPeriodEnd: null,
  signedIn: false,
  bypass: isFreemiumDisabled(),
  detail: "Billing is not configured. Add Stripe keys in Vercel to enable Checkout.",
};

let remoteBilling: RemoteBilling = emptyRemote;
const remoteListeners = new Set<() => void>();

function setRemoteBilling(next: RemoteBilling) {
  remoteBilling = next;
  remoteListeners.forEach((listener) => listener());
}

function subscribeRemote(listener: () => void) {
  remoteListeners.add(listener);
  return () => remoteListeners.delete(listener);
}

function entitlementOf(usage: DeviceUsage, remote: RemoteBilling): Entitlement {
  const bypass = remote.bypass || isFreemiumDisabled();
  const unlimited = bypass || remote.subscribed;
  const remaining = remainingFromUsage(usage);
  const walls = usageWalls(usage);
  return {
    configured: remote.configured,
    secretConfigured: false,
    subscribed: remote.subscribed,
    subscriptionStatus: remote.subscriptionStatus,
    cancelAtPeriodEnd: remote.cancelAtPeriodEnd,
    currentPeriodEnd: remote.currentPeriodEnd,
    signedIn: remote.signedIn,
    bypass,
    usage,
    remaining,
    walls: {
      search: unlimited ? false : walls.search,
      compare: unlimited ? false : walls.compare,
      portfolio: unlimited ? false : walls.portfolio,
    },
    detail: remote.detail,
  };
}

function applyRemote(next: Entitlement) {
  const usage = mergeUsage(readDeviceUsage(), next.usage);
  writeDeviceUsage(usage);
  setRemoteBilling({
    configured: next.configured,
    subscribed: next.subscribed,
    subscriptionStatus: next.subscriptionStatus,
    cancelAtPeriodEnd: next.cancelAtPeriodEnd,
    currentPeriodEnd: next.currentPeriodEnd,
    signedIn: next.signedIn,
    bypass: next.bypass,
    detail: next.detail,
  });
}

export function BillingProvider({ children }: { children: ReactNode }) {
  const { account } = useAccountSession();
  const usage = useSyncExternalStore(subscribe, readDeviceUsage, () => EMPTY_USAGE);
  const remote = useSyncExternalStore(
    subscribeRemote,
    () => remoteBilling,
    () => emptyRemote,
  );

  const refresh = useCallback(async () => {
    try {
      const response = await fetch(ENTITLEMENT_API_PATH, {
        credentials: "same-origin",
        headers: { accept: "application/json" },
      });
      if (!response.ok) return;
      applyRemote((await response.json()) as Entitlement);
    } catch {
      /* keep local snapshot */
    }
  }, []);

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
          if (!cancelled && body) applyRemote(body);
        })
        .catch(() => {
          /* keep local snapshot */
        });
    }, 0);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [account?.id, account?.subscribed]);

  const postKind = useCallback((kind: UsageKind, key?: string) => {
    writeDeviceUsage(incrementUsage(readDeviceUsage(), kind, key));
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
        if (body) applyRemote(body);
      })
      .catch(() => {
        /* local increment already applied */
      });
  }, []);

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
    const result = remote.subscribed
      ? await startCustomerPortal()
      : await startCheckout();
    if (result.url) {
      window.location.assign(result.url);
    }
    return result;
  }, [remote.subscribed]);

  const entitlement = entitlementOf(usage, {
    ...remote,
    signedIn: Boolean(account) || remote.signedIn,
    subscribed: Boolean(account?.subscribed) || remote.subscribed,
  });
  const unlimited = entitlement.bypass || entitlement.subscribed;
  const value = useMemo<BillingContextValue>(
    () => ({
      entitlement,
      remaining: entitlement.remaining,
      walls: entitlement.walls,
      unlimited,
      configured: entitlement.configured,
      subscribed: entitlement.subscribed,
      signedIn: entitlement.signedIn,
      recordSearch,
      recordCompare,
      recordPortfolio,
      unlock,
      manageBilling,
      refresh,
    }),
    [
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
