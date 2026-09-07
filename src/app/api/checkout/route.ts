import { NextResponse } from "next/server";
import { createCheckoutSession } from "@/lib/stripe/checkout";

export const dynamic = "force-dynamic";

/**
 * Aftertax website owns Stripe Checkout Session creation.
 * Price: price_1UD6C0RqA7bY5N5qVleZso0d (product prod_VDXGeprN4QkxsM).
 * success_url → same search/portfolio flow (?checkout=success)
 * cancel_url → paywall (?checkout=cancel)
 *
 * Mocked demo does not require STRIPE_SECRET_KEY; this route stubs until keys exist.
 */
export async function POST() {
  const { result, status } = await createCheckoutSession();
  return NextResponse.json(result, { status });
}
