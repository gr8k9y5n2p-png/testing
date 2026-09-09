import { STRIPE } from "@/lib/copy";
import { publicOrigin } from "@/lib/hosts";

/**
 * Billing hooks for later Checkout + Customer Portal.
 *
 * Friends beta: Soft-wall and Checkout stay off. This module does not
 * create live Checkout Sessions or Portal sessions.
 *
 * Next steps when billing is turned on:
 * - STRIPE_SECRET_KEY + optional STRIPE_PRICE_ID → existing createCheckoutSession()
 * - Persist a Stripe customer id on the account
 * - POST /api/billing/portal → createCustomerPortalSession() below
 * - Return users to /account
 */
export const BILLING_PLAN_LABEL = "$39 / user / month";
export const MANAGE_BILLING_LABEL = "Manage billing — coming soon";
export const BILLING_STUB_NOTE =
  "Billing and subscription management will be available when Checkout is on.";

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
