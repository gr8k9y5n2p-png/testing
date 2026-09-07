import { NextResponse } from "next/server";
import { createCheckoutSession } from "@/lib/stripe/checkout";

export const dynamic = "force-dynamic";

/**
 * Aftertax website owns Stripe Checkout Session creation.
 * Price: price_1UD6C0RqA7bY5N5qVleZso0d (product prod_VDXGeprN4QkxsM).
 * Return URLs default to staging.getaftertax.com until ads are green-lit.
 * Test mode later — do not block on live keys. This route stubs without STRIPE_SECRET_KEY.
 */
export async function POST() {
  const { result, status } = await createCheckoutSession();
  return NextResponse.json(result, { status });
}
