/** Client-safe billing chrome. Checkout still starts from POST /api/checkout. */

export const CHECKOUT_API_PATH = "/api/checkout";
export const PORTAL_API_PATH = "/api/billing/portal";
export const ENTITLEMENT_API_PATH = "/api/billing/entitlement";
export const USAGE_API_PATH = "/api/billing/usage";
export const BILLING_PLAN_LABEL = "$39 / user / month";
export const MANAGE_BILLING_LABEL = "Manage billing";
export const UNLOCK_BILLING_LABEL = "Unlock full access";
export const BILLING_NOT_CONFIGURED =
  "Billing is not configured. Add Stripe keys in Vercel to enable Checkout.";
export const BILLING_SIGN_IN = "Sign in to subscribe. Checkout links a Customer to this account email.";
export const BILLING_CREATE_ACCOUNT =
  "Create an account to subscribe. Checkout links a Customer to this account email.";
export const BILLING_CANCEL_NOTE =
  "Cancel anytime in the Customer Portal. Cancellation takes effect at period end.";
export const BILLING_STUB_NOTE = BILLING_NOT_CONFIGURED;

/** True when a publishable (or server secret) Stripe key is present. */
export function isBillingEnabled(): boolean {
  const publishable = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY?.trim();
  if (publishable) return true;
  if (typeof window === "undefined" && process.env.STRIPE_SECRET_KEY?.trim()) {
    return true;
  }
  return false;
}
