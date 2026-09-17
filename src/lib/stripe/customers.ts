import type Stripe from "stripe";
import type { AccountRecord, AccountStore } from "../account/store.ts";

export async function ensureStripeCustomer(
  stripe: Stripe,
  store: AccountStore,
  account: AccountRecord,
): Promise<string> {
  if (account.stripeCustomerId) return account.stripeCustomerId;

  const existing = await stripe.customers.list({
    email: account.email,
    limit: 1,
  });
  const customer =
    existing.data[0] ??
    (await stripe.customers.create({
      email: account.email,
      metadata: { accountId: account.id },
    }));

  await store.updateBilling(account.id, { stripeCustomerId: customer.id });
  return customer.id;
}
