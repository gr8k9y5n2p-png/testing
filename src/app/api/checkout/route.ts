import { NextResponse } from "next/server";
import { STRIPE } from "@/lib/copy";
import { checkoutUrls } from "@/lib/data-api/config";

export const dynamic = "force-dynamic";

/**
 * Stub Checkout Session creator. Aftertax (this UI) owns Stripe Checkout.
 * When STRIPE_SECRET_KEY is set, create a Session against STRIPE_PRICE_ID.
 * success_url → https://getaftertax.com/?checkout=success
 * cancel_url → https://getaftertax.com/?checkout=cancel
 */
export async function POST() {
  const priceId = process.env.STRIPE_PRICE_ID ?? STRIPE.priceId;
  const secret = process.env.STRIPE_SECRET_KEY;
  const urls = checkoutUrls();

  if (!secret) {
    return NextResponse.json(
      {
        stub: true,
        detail:
          "Stripe Checkout is not configured. Set STRIPE_SECRET_KEY to create a live session.",
        price_id: priceId,
        product_id: STRIPE.productId,
        ...urls,
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
      ...urls,
    },
    { status: 501 },
  );
}
