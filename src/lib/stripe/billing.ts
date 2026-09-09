import { STRIPE } from "@/lib/copy";
import { publicOrigin } from "@/lib/hosts";
import { BILLING_STUB_NOTE } from "./billing-copy";

export {
  BILLING_PLAN_LABEL,
  BILLING_STUB_NOTE,
  CHECKOUT_API_PATH,
  MANAGE_BILLING_LABEL,
  PORTAL_API_PATH,
  isBillingEnabled,
} from "./billing-copy";

/**
 * Billing hooks for later Checkout + Customer Portal.
 *
 * Friends beta: Soft-wall and Checkout stay off. Account must not start
 * a live Checkout Session or Customer Portal session.
 *
 * Next steps when billing is turned on:
 * 1. Set NEXT_PUBLIC_BILLING_ENABLED=true (this flag is the Account gate)
 * 2. STRIPE_SECRET_KEY + optional STRIPE_PRICE_ID → POST /api/checkout
 *    (existing createCheckoutSession)
 * 3. Persist a Stripe customer id on the account
 * 4. POST /api/billing/portal → createCustomerPortalSession() below
 * 5. Return users to /account (or STRIPE_PORTAL_RETURN_URL)
 */

export function billingPortalReturnUrl(): string {
  return `${publicOrigin()}/account`;
}

export type PortalStub = {
  stub: true;
  url?: never;
  detail: string;
  price_id: string;
  product_id: string;
  return_url: string;
};

export type PortalLive = {
  stub: false;
  url: string;
  price_id: string;
  return_url: string;
};

export type PortalResult = PortalStub | PortalLive;

/** Always stubs for friends beta. Wire Stripe Customer Portal here later. */
export async function createCustomerPortalSession(): Promise<{
  result: PortalResult;
  status: number;
}> {
  const priceId = process.env.STRIPE_PRICE_ID?.trim() || STRIPE.priceId;
  const returnUrl =
    process.env.STRIPE_PORTAL_RETURN_URL?.trim() || billingPortalReturnUrl();

  // TODO: When Checkout is on, look up the Stripe customer and POST
  // https://api.stripe.com/v1/billing_portal/sessions with return_url.
  return {
    status: 501,
    result: {
      stub: true,
      detail: BILLING_STUB_NOTE,
      price_id: priceId,
      product_id: STRIPE.productId,
      return_url: returnUrl,
    },
  };
}
