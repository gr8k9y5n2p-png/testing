import type Stripe from "stripe";
import type { AccountBillingPatch, AccountStore } from "../account/store.ts";

export function customerIdFrom(
  customer: string | { id?: string } | null | undefined,
): string | null {
  if (!customer) return null;
  if (typeof customer === "string") return customer;
  return customer.id ?? null;
}

export function subscriptionPeriodEnd(
  subscription: Stripe.Subscription,
): string | null {
  const itemEnd = subscription.items?.data?.[0]?.current_period_end;
  const cancelAt = subscription.cancel_at;
  const unix = itemEnd ?? cancelAt;
  if (!unix) return null;
  return new Date(unix * 1000).toISOString();
}

export function billingPatchFromSubscription(
  subscription: Stripe.Subscription,
): AccountBillingPatch {
  return {
    stripeCustomerId: customerIdFrom(subscription.customer),
    stripeSubscriptionId: subscription.id,
    subscriptionStatus: subscription.status,
    cancelAtPeriodEnd: Boolean(subscription.cancel_at_period_end),
    currentPeriodEnd: subscriptionPeriodEnd(subscription),
  };
}

export async function applySubscriptionToAccount(
  store: AccountStore,
  subscription: Stripe.Subscription,
  accountId?: string | null,
): Promise<void> {
  const customerId = customerIdFrom(subscription.customer);
  const metadataAccountId =
    accountId ||
    (typeof subscription.metadata?.accountId === "string"
      ? subscription.metadata.accountId
      : null);

  const row =
    (metadataAccountId ? await store.findById(metadataAccountId) : null) ??
    (customerId ? await store.findByStripeCustomerId(customerId) : null);

  if (!row) return;
  await store.updateBilling(row.id, billingPatchFromSubscription(subscription));
}

export async function clearSubscriptionForCustomer(
  store: AccountStore,
  customerId: string | null,
  accountId?: string | null,
): Promise<void> {
  const row =
    (accountId ? await store.findById(accountId) : null) ??
    (customerId ? await store.findByStripeCustomerId(customerId) : null);
  if (!row) return;
  await store.updateBilling(row.id, {
    stripeCustomerId: customerId ?? row.stripeCustomerId,
    stripeSubscriptionId: null,
    subscriptionStatus: "canceled",
    cancelAtPeriodEnd: false,
    currentPeriodEnd: null,
  });
}
