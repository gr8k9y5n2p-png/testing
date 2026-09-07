import { STRIPE } from "@/lib/copy";
import { checkoutUrls } from "@/lib/data-api/config";

export type CheckoutStub = {
  stub: true;
  url?: never;
  detail: string;
  price_id: string;
  product_id: string;
  account_id: string;
  success_url: string;
  cancel_url: string;
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

/**
 * Aftertax website owns Checkout Session creation (server-side).
 * Without STRIPE_SECRET_KEY the mocked demo still works: this returns a stub.
 */
export async function createCheckoutSession(): Promise<{
  result: CheckoutResult;
  status: number;
}> {
  const priceId = process.env.STRIPE_PRICE_ID?.trim() || STRIPE.priceId;
  const secret = process.env.STRIPE_SECRET_KEY?.trim();
  const urls = checkoutUrls();

  if (!secret) {
    return {
      status: 501,
      result: {
        stub: true,
        detail:
          "Stripe Checkout is not configured. Set STRIPE_SECRET_KEY to create a live session.",
        price_id: priceId,
        product_id: STRIPE.productId,
        account_id: STRIPE.accountId,
        ...urls,
      },
    };
  }

  const body = new URLSearchParams();
  body.set("mode", "subscription");
  body.set("line_items[0][price]", priceId);
  body.set("line_items[0][quantity]", "1");
  body.set("success_url", urls.success_url);
  body.set("cancel_url", urls.cancel_url);

  const response = await fetch("https://api.stripe.com/v1/checkout/sessions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${secret}`,
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body,
  });

  const payload = (await response.json()) as {
    id?: string;
    url?: string;
    error?: { message?: string };
  };

  if (!response.ok || !payload.url || !payload.id) {
    return {
      status: 502,
      result: {
        stub: true,
        detail:
          payload.error?.message ??
          "Stripe Checkout Session creation failed. The mocked demo can still run without a live session.",
        price_id: priceId,
        product_id: STRIPE.productId,
        account_id: STRIPE.accountId,
        ...urls,
      },
    };
  }

  return {
    status: 200,
    result: {
      stub: false,
      url: payload.url,
      session_id: payload.id,
      price_id: priceId,
      ...urls,
    },
  };
}
