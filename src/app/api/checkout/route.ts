import { NextResponse } from "next/server";
import { STRIPE } from "@/lib/copy";

export const dynamic = "force-dynamic";

/**
 * Stub Checkout Session creator. Aftertax (this UI) owns Stripe Checkout.
 * When STRIPE_SECRET_KEY is set, replace this with a real Session against
 * STRIPE_PRICE_ID. success_url → search/portfolio flow; cancel_url → paywall.
 */
export async function POST() {
  const priceId = process.env.STRIPE_PRICE_ID ?? STRIPE.priceId;
  const secret = process.env.STRIPE_SECRET_KEY;

  if (!secret) {
    return NextResponse.json(
      {
        stub: true,
        detail:
          "Stripe Checkout is not configured. Set STRIPE_SECRET_KEY to create a live session.",
        price_id: priceId,
        product_id: STRIPE.productId,
      },
      { status: 501 },
    );
  }

  return NextResponse.json(
    {
      stub: true,
      detail:
        "Stripe key is present but Checkout Session creation is not implemented in this template yet.",
      price_id: priceId,
    },
    { status: 501 },
  );
}
