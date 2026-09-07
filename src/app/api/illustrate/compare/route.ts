import { NextResponse } from "next/server";
import {
  isCompareRequestValid,
  mockCompareResponse,
} from "@/lib/illustrate/compare-fixture";
import type { CompareRequest } from "@/lib/illustrate/compare-types";

export const dynamic = "force-dynamic";

/**
 * MOCK POST /illustrate/compare.
 * Production math lives on the Data team FastAPI (PR #2). This route returns
 * the sketch-locked fixture so the tax-delta card still demos on localhost.
 */
export async function POST(request: Request) {
  let body: CompareRequest;
  try {
    body = (await request.json()) as CompareRequest;
  } catch {
    return NextResponse.json({ detail: "Invalid JSON body" }, { status: 400 });
  }

  const invalid = isCompareRequestValid(body);
  if (invalid) {
    return NextResponse.json({ detail: invalid }, { status: 422 });
  }

  return NextResponse.json(mockCompareResponse(body));
}
