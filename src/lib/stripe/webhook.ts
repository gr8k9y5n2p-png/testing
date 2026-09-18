import type Stripe from "stripe";
import { getAccountStore, type AccountStore } from "../account/store.ts";
import { BILLING_NOT_CONFIGURED } from "./billing-copy.ts";
import { createStripeClient } from "./client.ts";
import { stripeWebhookSecret } from "./config.ts";
import { customerIdFrom } from "./subscriptions.ts";
import {
  applySubscriptionToAccount,
  clearSubscriptionForCustomer,
} from "./subscriptions.ts";

export type WebhookResult = {
  received: boolean;
  stub?: boolean;
  type?: string;
  detail?: string;
};

export async function applyCheckoutCompleted(
  store: AccountStore,
  session: Stripe.Checkout.Session,
): Promise<void> {
  const accountId =
    (typeof session.client_reference_id === "string"
      ? session.client_reference_id
      : null) ||
    (typeof session.metadata?.accountId === "string"
      ? session.metadata.accountId
      : null);
  const customerId = customerIdFrom(session.customer);
  const row =
    (accountId ? await store.findById(accountId) : null) ??
    (customerId ? await store.findByStripeCustomerId(customerId) : null);
  if (row && customerId) {
    await store.updateBilling(row.id, { stripeCustomerId: customerId });
  }

  const subscription = session.subscription;
  if (subscription && typeof subscription !== "string") {
    await applySubscriptionToAccount(store, subscription, row?.id ?? accountId);
    return;
  }
  if (typeof subscription === "string") {
    const stripe = createStripeClient();
    if (!stripe) return;
    const live = await stripe.subscriptions.retrieve(subscription);
    await applySubscriptionToAccount(store, live, row?.id ?? accountId);
  }
}

export async function handleStripeWebhook(
  request: Request,
): Promise<{ result: WebhookResult; status: number }> {
  const stripe = createStripeClient();
  const secret = stripeWebhookSecret();
  if (!stripe || !secret) {
    return {
      status: 501,
      result: {
        received: false,
        stub: true,
        detail: BILLING_NOT_CONFIGURED,
      },
    };
  }

  const signature = request.headers.get("stripe-signature");
  if (!signature) {
    return {
      status: 400,
      result: { received: false, detail: "Missing stripe-signature header." },
    };
  }

  let event: Stripe.Event;
  try {
    const payload = await request.text();
    event = stripe.webhooks.constructEvent(payload, signature, secret);
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Invalid webhook signature.";
    return {
      status: 400,
      result: { received: false, detail: message },
    };
  }

  const store = getAccountStore();
  try {
    switch (event.type) {
      case "checkout.session.completed":
        await applyCheckoutCompleted(
          store,
          event.data.object as Stripe.Checkout.Session,
        );
        break;
      case "customer.subscription.updated":
        await applySubscriptionToAccount(
          store,
          event.data.object as Stripe.Subscription,
        );
        break;
      case "customer.subscription.deleted":
        {
          const subscription = event.data.object as Stripe.Subscription;
          await clearSubscriptionForCustomer(
            store,
            customerIdFrom(subscription.customer),
            typeof subscription.metadata?.accountId === "string"
              ? subscription.metadata.accountId
              : null,
          );
        }
        break;
      case "invoice.paid":
        {
          const invoice = event.data.object as Stripe.Invoice & {
            parent?: { subscription_details?: { subscription?: unknown } };
            subscription?: unknown;
          };
          const fromParent = invoice.parent?.subscription_details?.subscription;
          const fromLegacy = invoice.subscription;
          const subscriptionId =
            typeof fromParent === "string"
              ? fromParent
              : typeof fromLegacy === "string"
                ? fromLegacy
                : null;
          if (subscriptionId) {
            const live = await stripe.subscriptions.retrieve(subscriptionId);
            await applySubscriptionToAccount(store, live);
          }
        }
        break;
      default:
        break;
    }
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Webhook handler failed.";
    return {
      status: 500,
      result: { received: false, type: event.type, detail: message },
    };
  }

  return {
    status: 200,
    result: { received: true, type: event.type },
  };
}
