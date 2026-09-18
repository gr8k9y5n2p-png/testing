import { publicOrigin } from "../hosts.ts";
import { readAccountIdFromRequest } from "../account/session.ts";
import { getAccountStore } from "../account/store.ts";
import {
  BILLING_NOT_CONFIGURED,
  BILLING_SIGN_IN,
  BILLING_STUB_NOTE,
} from "./billing-copy.ts";
import { createStripeClient } from "./client.ts";
import { stripePriceId, stripeProductId } from "./config.ts";
import { ensureStripeCustomer } from "./customers.ts";

export {
  BILLING_PLAN_LABEL,
  BILLING_STUB_NOTE,
  BILLING_NOT_CONFIGURED,
  CHECKOUT_API_PATH,
  MANAGE_BILLING_LABEL,
  PORTAL_API_PATH,
  isBillingEnabled,
} from "./billing-copy.ts";

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
  needs_account?: boolean;
  needs_checkout?: boolean;
};

export type PortalLive = {
  stub: false;
  url: string;
  price_id: string;
  return_url: string;
};

export type PortalResult = PortalStub | PortalLive;

function portalReturnUrl(): string {
  return process.env.STRIPE_PORTAL_RETURN_URL?.trim() || billingPortalReturnUrl();
}

function stubPortal(detail: string, extra: Partial<PortalStub> = {}): PortalStub {
  return {
    stub: true,
    detail,
    price_id: stripePriceId(),
    product_id: stripeProductId(),
    return_url: portalReturnUrl(),
    ...extra,
  };
}

/**
 * Customer Portal for manage / cancel-at-period-end.
 * Soft-fails when Stripe keys or an Account session are missing.
 */
export async function createCustomerPortalSession(
  request?: Request,
): Promise<{
  result: PortalResult;
  status: number;
}> {
  const stripe = createStripeClient();
  if (!stripe) {
    return { status: 501, result: stubPortal(BILLING_NOT_CONFIGURED) };
  }
  if (!request) {
    return {
      status: 401,
      result: stubPortal(BILLING_SIGN_IN, { needs_account: true }),
    };
  }

  const accountId = readAccountIdFromRequest(request);
  const store = getAccountStore();
  let account = null;
  try {
    account = accountId ? await store.findById(accountId) : null;
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Account store read failed.";
    return { status: 502, result: stubPortal(message) };
  }
  if (!account) {
    return {
      status: 401,
      result: stubPortal(BILLING_SIGN_IN, { needs_account: true }),
    };
  }

  try {
    const customerId = await ensureStripeCustomer(stripe, store, account);
    const session = await stripe.billingPortal.sessions.create({
      customer: customerId,
      return_url: portalReturnUrl(),
    });
    if (!session.url) {
      return {
        status: 502,
        result: stubPortal(BILLING_STUB_NOTE),
      };
    }
    return {
      status: 200,
      result: {
        stub: false,
        url: session.url,
        price_id: stripePriceId(),
        return_url: portalReturnUrl(),
      },
    };
  } catch (error) {
    const message =
      error instanceof Error ? error.message : BILLING_STUB_NOTE;
    return { status: 502, result: stubPortal(message) };
  }
}
