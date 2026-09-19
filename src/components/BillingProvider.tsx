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
  readBrowserUsage,
  writeBrowserUsage,
} from "@/lib/billing/device-usage";
import {
  EMPTY_USAGE,
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
let cachedKey = "__unset__";
let cachedUsage: DeviceUsage = EMPTY_USAGE;

function emit() {
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  if (typeof window !== "undefined") {
    window.addEventListener("storage", emit);
  }
  return () => {
    listeners.delete(listener);
    if (listeners.size === 0 && typeof window !== "undefined") {
      window.removeEventListener("storage", emit);
    }
  };
}

function subscribeNoop() {
  return () => {};
}

function clientTrue() {
  return true;
}

function serverFalse() {
  return false;
}

function snapshotUsage(seed: DeviceUsage): DeviceUsage {
  const merged = readBrowserUsage(seed);
  const raw = JSON.stringify(merged);
  if (raw === cachedKey) return cachedUsage;
  cachedKey = raw;
  cachedUsage = merged;
  return cachedUsage;
}

function writeDeviceUsage(usage: DeviceUsage) {
  const next = normalizeUsage(usage);
  writeBrowserUsage(next);
  cachedKey = JSON.stringify(next);
  cachedUsage = next;
  emit();
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
      lists: !unlimited,
      highlights: !unlimited,
      upcoming: !unlimited,
    },
    detail: remote.detail,
  };
}

function applyRemote(next: Entitlement, seed: DeviceUsage) {
  const usage = mergeUsage(snapshotUsage(seed), next.usage);
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

export function BillingProvider({
  children,
  initialUsage = EMPTY_USAGE,
}: {
  children: ReactNode;
  initialUsage?: DeviceUsage;
}) {
  const { account } = useAccountSession();
  const seedKey = JSON.stringify(normalizeUsage(initialUsage));
  const seed = useMemo(
    () => normalizeUsage(JSON.parse(seedKey) as DeviceUsage),
    [seedKey],
  );
  const getServerSnapshot = useCallback(() => seed, [seed]);
  const getClientSnapshot = useCallback(() => snapshotUsage(seed), [seed]);
  const mounted = useSyncExternalStore(subscribeNoop, clientTrue, serverFalse);
  const liveUsage = useSyncExternalStore(
    subscribe,
    getClientSnapshot,
    getServerSnapshot,
  );
  const usage = mounted ? liveUsage : seed;
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
      applyRemote((await response.json()) as Entitlement, seed);
    } catch {
      /* keep local snapshot */
    }
  }, [seed]);

  useEffect(() => {
    cachedKey = "__unset__";
    emit();
    let cancelled = false;
    const timer = window.setTimeout(() => {
      void fetch(USAGE_API_PATH, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          accept: "application/json",
          "content-type": "application/json",
        },
        body: JSON.stringify({ merge: snapshotUsage(seed) }),
      })
        .then((response) => (response.ok ? response.json() : null))
        .then((body: Entitlement | null) => {
          if (!cancelled && body) applyRemote(body, seed);
        })
        .catch(() => {
          /* keep local snapshot */
        });
    }, 0);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [account?.id, account?.subscribed, seed]);

  const postKind = useCallback(
    (kind: UsageKind, key?: string) => {
      writeDeviceUsage(incrementUsage(snapshotUsage(seed), kind, key));
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
          if (body) applyRemote(body, seed);
        })
        .catch(() => {
          /* local increment already applied */
        });
    },
    [seed],
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
