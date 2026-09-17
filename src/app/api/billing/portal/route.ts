import { NextResponse } from "next/server";
import { createCustomerPortalSession } from "@/lib/stripe/billing";

export const dynamic = "force-dynamic";

/**
 * Stripe Customer Portal for manage / cancel-at-period-end.
 * Soft-fails without STRIPE_SECRET_KEY (501). Requires Account session.
 */
export async function POST(request: Request) {
  const { result, status } = await createCustomerPortalSession(request);
  return NextResponse.json(result, { status });
}
