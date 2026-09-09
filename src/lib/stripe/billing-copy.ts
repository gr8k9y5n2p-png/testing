/** Client-safe billing chrome. Do not start Checkout from here. */

export const CHECKOUT_API_PATH = "/api/checkout";
export const PORTAL_API_PATH = "/api/billing/portal";
export const BILLING_PLAN_LABEL = "$39 / user / month";
export const MANAGE_BILLING_LABEL = "Manage billing — coming soon";
export const BILLING_STUB_NOTE =
  "Billing and subscription management will be available when Checkout is on.";

/** Account gate. Unset / false keeps Checkout and Portal off in the UI. */
export function isBillingEnabled(): boolean {
  const raw = process.env.NEXT_PUBLIC_BILLING_ENABLED?.trim().toLowerCase();
  return raw === "true" || raw === "1";
}
