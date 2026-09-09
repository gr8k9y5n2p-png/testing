"use client";

import {
  CHECKOUT_API_PATH,
  MANAGE_BILLING_LABEL,
  PORTAL_API_PATH,
  isBillingEnabled,
} from "@/lib/stripe/billing-copy";

/**
 * Friends beta: disabled. Do not POST while Checkout is off.
 *
 * When NEXT_PUBLIC_BILLING_ENABLED is on:
 * - new subscriber → POST CHECKOUT_API_PATH → redirect to session.url
 * - existing customer → POST PORTAL_API_PATH → redirect to portal url
 */
export function ManageBillingButton() {
  const live = isBillingEnabled();

  return (
    <button
      type="button"
      disabled
      aria-disabled="true"
      title={
        live
          ? `Ready to wire: POST ${CHECKOUT_API_PATH} or ${PORTAL_API_PATH}`
          : MANAGE_BILLING_LABEL
      }
      className="mt-3 inline-flex h-9 items-center rounded-md border border-line bg-notice px-3 text-sm text-muted"
    >
      {MANAGE_BILLING_LABEL}
    </button>
  );
}
