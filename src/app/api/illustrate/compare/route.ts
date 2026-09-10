import { NextResponse } from "next/server";
import { proxyLiveOrDemo } from "@/lib/illustrate/illustrate-route";
import {
  isCompareRequestValid,
  mockCompareResponse,
} from "@/lib/illustrate/compare-fixture";
import { toDataApiCompareBody } from "@/lib/illustrate/compare-request";
import type { CompareRequest } from "@/lib/illustrate/compare-types";

export const dynamic = "force-dynamic";

/**
 * POST /api/illustrate/compare.
 * Live Data API when configured. Production never runs the sketch fixture.
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

  return proxyLiveOrDemo({
    path: "/illustrate/compare",
    body: toDataApiCompareBody(body),
    unavailableDetail: "Compare is unavailable from the Data API.",
    mock: () => mockCompareResponse(body),
  });
}
