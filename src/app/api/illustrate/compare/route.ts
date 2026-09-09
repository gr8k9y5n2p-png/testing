import { NextResponse } from "next/server";
import {
  getLiveIllustrateUrl,
  proxyLiveDataApiPost,
} from "@/lib/data-api/config";
import {
  isCompareRequestValid,
  mockCompareResponse,
} from "@/lib/illustrate/compare-fixture";
import { toDataApiCompareBody } from "@/lib/illustrate/compare-request";
import type { CompareRequest } from "@/lib/illustrate/compare-types";

export const dynamic = "force-dynamic";

/**
 * POST /api/illustrate/compare.
 * Live Data API when NEXT_PUBLIC_DATA_API_URL / NEXT_PUBLIC_COMPARE_URL is set.
 * Localhost without those env vars still uses the sketch fixture.
 */
export async function POST(request: Request) {
  let body: CompareRequest;
  try {
    body = (await request.json()) as CompareRequest;
  } catch {
    return NextResponse.json({ detail: "Invalid JSON body" }, { status: 400 });
  }

  const live = getLiveIllustrateUrl("/illustrate/compare");
  if (live) {
    try {
      const upstream = await proxyLiveDataApiPost(live, toDataApiCompareBody(body));
      const text = await upstream.text();
      return new NextResponse(text, {
        status: upstream.status,
        headers: { "Content-Type": "application/json" },
      });
    } catch {
      return NextResponse.json(
        { detail: "Compare is unavailable from the Data API." },
        { status: 503 },
      );
    }
  }

  const invalid = isCompareRequestValid(body);
  if (invalid) {
    return NextResponse.json({ detail: invalid }, { status: 422 });
  }

  return NextResponse.json(mockCompareResponse(body));
}
