"use client";

import { FREE_SEARCH_LIMIT, isFreemiumDisabled } from "@/lib/billing/limits";
import { useBilling } from "@/components/BillingProvider";

export { isFreemiumDisabled, FREE_SEARCH_LIMIT };

/** Search-page adapter over the charge-ready billing counters. */
export function useFreemium() {
  const billing = useBilling();
  return {
    remaining: billing.remaining.searches,
    unlimited: billing.unlimited,
    searchedTickers: [] as string[],
    trySearch: () => ({
      allowed: true,
      remaining: billing.remaining.searches,
      isNew: true,
    }),
    unlockStub: () => {
      void billing.unlock();
    },
    bypass: billing.entitlement.bypass,
    walls: billing.walls,
    recordSearch: billing.recordSearch,
  };
}
