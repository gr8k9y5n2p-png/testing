import { NextResponse } from "next/server";
import { TOP_ADVISOR_FAMILIES } from "@/lib/coverage";

export const dynamic = "force-dynamic";

/**
 * Mock GET /fund-families (coverage_tier, priority, aum_rank).
 * Prefer the Data API list when NEXT_PUBLIC_DATA_API_URL is set.
 */
export async function GET() {
  return NextResponse.json(TOP_ADVISOR_FAMILIES);
}
