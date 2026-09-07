import { NextResponse } from "next/server";
import {
  isPortfolioCompareRequestValid,
  mockPortfolioCompareResponse,
} from "@/lib/illustrate/portfolio-compare-fixture";
import type { PortfolioCompareRequest } from "@/lib/illustrate/portfolio-compare-types";

export const dynamic = "force-dynamic";

/**
 * MOCK POST /illustrate/portfolio/compare.
 * Production math lives on the Data team FastAPI (PR #2). This route returns
 * the sketch-locked smoke book so the module still demos on localhost.
 */
export async function POST(request: Request) {
  let body: PortfolioCompareRequest;
  try {
    body = (await request.json()) as PortfolioCompareRequest;
  } catch {
    return NextResponse.json({ detail: "Invalid JSON body" }, { status: 400 });
  }

  const invalid = isPortfolioCompareRequestValid(body);
  if (invalid) {
    return NextResponse.json({ detail: invalid }, { status: 422 });
  }

  return NextResponse.json(mockPortfolioCompareResponse(body));
}
