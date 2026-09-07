import { NextResponse } from "next/server";
import { TOP_ADVISOR_FAMILIES } from "@/lib/coverage";

export const dynamic = "force-dynamic";

/**
 * Stub for upcoming GET /fund-families (coverage_tier, priority, aum_rank).
 * Prefer the Data API when NEXT_PUBLIC_DATA_API_URL is set.
 */
export async function GET() {
  return NextResponse.json({
    stub: true,
    families: TOP_ADVISOR_FAMILIES,
  });
}
