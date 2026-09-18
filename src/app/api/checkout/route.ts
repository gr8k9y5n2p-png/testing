import { NextResponse } from "next/server";
import { confirmCheckoutSession, createCheckoutSession } from "@/lib/stripe/checkout";

export const dynamic = "force-dynamic";

/**
 * Aftertax website owns Stripe Checkout Session creation.
 * Price: price_1UD6C0RqA7bY5N5qVleZso0d (product prod_VDXGeprN4QkxsM).
 * Soft-fails without STRIPE_SECRET_KEY (501). Requires Account session.
 */
export async function POST(request: Request) {
  const { result, status } = await createCheckoutSession(request);
  return NextResponse.json(result, { status });
}

/** Confirm a returning Checkout Session when the webhook is delayed. */
export async function PUT(request: Request) {
  let sessionId = "";
  try {
    const body = (await request.json()) as { session_id?: unknown };
    sessionId = typeof body.session_id === "string" ? body.session_id : "";
  } catch {
    sessionId = "";
  }
  const result = await confirmCheckoutSession(request, sessionId);
  return NextResponse.json(
    { ok: result.ok, detail: result.detail },
    { status: result.status },
  );
}
