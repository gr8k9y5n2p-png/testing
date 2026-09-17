export const STRIPE_DEFAULTS = {
  productId: "prod_VDXGeprN4QkxsM",
  priceId: "price_1UD6C0RqA7bY5N5qVleZso0d",
  accountId: "acct_1UD66TRqA7bY5N5q",
} as const;

export function stripeSecretKey(
  env: NodeJS.ProcessEnv = process.env,
): string | null {
  const value = env.STRIPE_SECRET_KEY?.trim();
  return value || null;
}

export function stripePublishableKey(
  env: NodeJS.ProcessEnv = process.env,
): string | null {
  const value = env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY?.trim();
  return value || null;
}

export function stripePriceId(env: NodeJS.ProcessEnv = process.env): string {
  return env.STRIPE_PRICE_ID?.trim() || STRIPE_DEFAULTS.priceId;
}

export function stripeProductId(env: NodeJS.ProcessEnv = process.env): string {
  return env.STRIPE_PRODUCT_ID?.trim() || STRIPE_DEFAULTS.productId;
}

export function stripeWebhookSecret(
  env: NodeJS.ProcessEnv = process.env,
): string | null {
  const value = env.STRIPE_WEBHOOK_SECRET?.trim();
  return value || null;
}

/** Server can start Checkout / Portal when the secret key is present. */
export function isStripeSecretConfigured(
  env: NodeJS.ProcessEnv = process.env,
): boolean {
  return Boolean(stripeSecretKey(env));
}

/**
 * Client-safe gate. Publishable key in the bundle means Vercel env is set.
 * Secret-only deploys still work server-side; the CTA fails soft via 501.
 */
export function isBillingConfigured(
  env: NodeJS.ProcessEnv = process.env,
): boolean {
  return Boolean(stripePublishableKey(env) || stripeSecretKey(env));
}

export function checkoutIntegrationId(): string {
  const alphabet = "abcdefghijklmnopqrstuvwxyz";
  let suffix = "";
  for (let i = 0; i < 8; i += 1) {
    suffix += alphabet[Math.floor(Math.random() * alphabet.length)];
  }
  return `aftertax_web_${suffix}`;
}
