import Stripe from "stripe";
import { stripeSecretKey } from "./config.ts";

/**
 * Server-only Stripe client. Returns null when STRIPE_SECRET_KEY is unset
 * so Checkout / Portal / webhooks fail soft instead of crashing.
 */
export function createStripeClient(
  env: NodeJS.ProcessEnv = process.env,
): Stripe | null {
  const secret = stripeSecretKey(env);
  if (!secret) return null;
  return new Stripe(secret, {
    timeout: 8_000,
    maxNetworkRetries: 0,
  });
}
