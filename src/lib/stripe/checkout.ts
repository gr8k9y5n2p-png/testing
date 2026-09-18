import { checkoutUrls } from "../data-api/config.ts";
import { readAccountIdFromRequest } from "../account/session.ts";
import { getAccountStore } from "../account/store.ts";
import {
  BILLING_NOT_CONFIGURED,
  BILLING_SIGN_IN,
} from "./billing-copy.ts";
import { createStripeClient } from "./client.ts";
import {
  STRIPE_DEFAULTS,
  checkoutIntegrationId,
  stripePriceId,
  stripeProductId,
} from "./config.ts";
import { ensureStripeCustomer } from "./customers.ts";
import { applyCheckoutCompleted } from "./webhook.ts";

export type CheckoutStub = {
  stub: true;
  url?: never;
  detail: string;
  price_id: string;
  product_id: string;
  account_id: string;
  success_url: string;
  cancel_url: string;
  needs_account?: boolean;
};

export type CheckoutLive = {
  stub: false;
  url: string;
  session_id: string;
  price_id: string;
  success_url: string;
  cancel_url: string;
};

export type CheckoutResult = CheckoutStub | CheckoutLive;

function urlsWithSession(): { success_url: string; cancel_url: string } {
  const urls = checkoutUrls();
  const joiner = urls.success_url.includes("?") ? "&" : "?";
  return {
    success_url: `${urls.success_url}${joiner}session_id={CHECKOUT_SESSION_ID}`,
    cancel_url: urls.cancel_url,
  };
}

function stubResult(
  detail: string,
  extra: Partial<CheckoutStub> = {},
): CheckoutStub {
  return {
    stub: true,
    detail,
    price_id: stripePriceId(),
    product_id: stripeProductId(),
    account_id: STRIPE_DEFAULTS.accountId,
    ...urlsWithSession(),
    ...extra,
  };
}

/**
 * Aftertax website owns Checkout Session creation (server-side).
 * Without STRIPE_SECRET_KEY this returns 501 and the funnel still works.
 */
export async function createCheckoutSession(
  request?: Request,
): Promise<{
  result: CheckoutResult;
  status: number;
}> {
  const priceId = stripePriceId();
  const urls = urlsWithSession();
  const stripe = createStripeClient();

  if (!stripe) {
    return {
      status: 501,
      result: stubResult(BILLING_NOT_CONFIGURED),
    };
  }

  if (!request) {
    return {
      status: 401,
      result: stubResult(BILLING_SIGN_IN, { needs_account: true }),
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
    return { status: 502, result: stubResult(message) };
  }
  if (!account) {
    return {
      status: 401,
      result: stubResult(BILLING_SIGN_IN, { needs_account: true }),
    };
  }

  try {
    const customerId = await ensureStripeCustomer(stripe, store, account);
    const session = await stripe.checkout.sessions.create({
      mode: "subscription",
      customer: customerId,
      client_reference_id: account.id,
      line_items: [{ price: priceId, quantity: 1 }],
      success_url: urls.success_url,
      cancel_url: urls.cancel_url,
      metadata: { accountId: account.id },
      subscription_data: { metadata: { accountId: account.id } },
      integration_identifier: checkoutIntegrationId(),
    });

    if (!session.url || !session.id) {
      return {
        status: 502,
        result: stubResult(
          "Stripe Checkout Session creation failed. Search and illustrate still work.",
        ),
      };
    }

    return {
      status: 200,
      result: {
        stub: false,
        url: session.url,
        session_id: session.id,
        price_id: priceId,
        ...urls,
      },
    };
  } catch (error) {
    const message =
      error instanceof Error
        ? error.message
        : "Stripe Checkout Session creation failed.";
    return {
      status: 502,
      result: stubResult(message),
    };
  }
}

export async function confirmCheckoutSession(
  request: Request,
  sessionId: string,
): Promise<{ ok: boolean; detail: string; status: number }> {
  const stripe = createStripeClient();
  if (!stripe) {
    return { ok: false, detail: BILLING_NOT_CONFIGURED, status: 501 };
  }
  const id = sessionId.trim();
  if (!id.startsWith("cs_")) {
    return { ok: false, detail: "Missing Checkout Session id.", status: 400 };
  }
  try {
    const session = await stripe.checkout.sessions.retrieve(id, {
      expand: ["subscription", "customer"],
    });
    await applyCheckoutCompleted(getAccountStore(), session);
    return { ok: true, detail: "Subscription confirmed.", status: 200 };
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Could not confirm Checkout.";
    return { ok: false, detail: message, status: 502 };
  }
}
