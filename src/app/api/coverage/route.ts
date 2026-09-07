import { NextResponse } from "next/server";
import { TOP_ADVISOR_FAMILIES } from "@/lib/coverage";

export const dynamic = "force-dynamic";

/** Mock GET /coverage when the Data API is not running. */
export async function GET() {
  const live = TOP_ADVISOR_FAMILIES.filter((family) => family.coverage_tier === "live").length;
  return NextResponse.json({
    stub: true,
    top_n: TOP_ADVISOR_FAMILIES.length,
    implemented_count: live,
    stub_count: TOP_ADVISOR_FAMILIES.length - live,
    implemented_pct: Math.round((1000 * live) / TOP_ADVISOR_FAMILIES.length) / 10,
    logged_gap_count: 0,
    families: TOP_ADVISOR_FAMILIES,
  });
}
