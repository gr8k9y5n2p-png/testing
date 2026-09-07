import { NextResponse } from "next/server";
import { createCheckoutSession } from "@/lib/stripe/checkout";

export const dynamic = "force-dynamic";

/**
 * Aftertax website owns Stripe Checkout Session creation.
 * Price: price_1UD6C0RqA7bY5N5qVleZso0d (product prod_VDXGeprN4QkxsM).
 * success_url → https://getaftertax.com/?checkout=success (same search/portfolio flow)
 * cancel_url → https://getaftertax.com/?checkout=cancel (paywall)
 *
 * Mocked demo does not require STRIPE_SECRET_KEY; this route stubs until keys exist.
 */
export async function POST() {
  const { result, status } = await createCheckoutSession();
  return NextResponse.json(result, { status });
}
