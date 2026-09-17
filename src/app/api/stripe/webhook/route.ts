import { NextResponse } from "next/server";
import { handleStripeWebhook } from "@/lib/stripe/webhook";

export const dynamic = "force-dynamic";

/**
 * Stripe webhooks: checkout.session.completed,
 * customer.subscription.updated / deleted, invoice.paid.
 * Verifies stripe-signature when STRIPE_WEBHOOK_SECRET is set.
 */
export async function POST(request: Request) {
  const { result, status } = await handleStripeWebhook(request);
  return NextResponse.json(result, { status });
}
