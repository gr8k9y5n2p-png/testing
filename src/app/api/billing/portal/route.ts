import { NextResponse } from "next/server";
import { createCustomerPortalSession } from "@/lib/stripe/billing";

export const dynamic = "force-dynamic";

/**
 * Stripe Customer Portal stub. Friends beta keeps Checkout off —
 * this always returns 501 until billing is enabled.
 */
export async function POST() {
  const { result, status } = await createCustomerPortalSession();
  return NextResponse.json(result, { status });
}
