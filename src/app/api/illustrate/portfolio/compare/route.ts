import { NextResponse } from "next/server";
import {
  getLiveIllustrateUrl,
  proxyLiveDataApiPost,
} from "@/lib/data-api/config";
import {
  isPortfolioCompareRequestValid,
  mockPortfolioCompareResponse,
} from "@/lib/illustrate/portfolio-compare-fixture";
import { toPortfolioCompareRequestBody } from "@/lib/illustrate/portfolio-compare-client";
import type { PortfolioCompareRequest } from "@/lib/illustrate/portfolio-compare-types";

export const dynamic = "force-dynamic";

/**
 * POST /api/illustrate/portfolio/compare.
 * Live Data API when configured. Never seed-math + MOCK banners on Production.
 */
export async function POST(request: Request) {
  let body: PortfolioCompareRequest;
  try {
    body = (await request.json()) as PortfolioCompareRequest;
  } catch {
    return NextResponse.json({ detail: "Invalid JSON body" }, { status: 400 });
  }

  const live = getLiveIllustrateUrl("/illustrate/portfolio/compare");
  if (live) {
    try {
      const upstream = await proxyLiveDataApiPost(
        live,
        toPortfolioCompareRequestBody(body),
      );
      const text = await upstream.text();
      return new NextResponse(text, {
        status: upstream.status,
        headers: { "Content-Type": "application/json" },
      });
    } catch {
      return NextResponse.json(
        { detail: "Portfolio compare is unavailable from the Data API." },
        { status: 503 },
      );
    }
  }

  const invalid = isPortfolioCompareRequestValid(body);
  if (invalid) {
    return NextResponse.json({ detail: invalid }, { status: 422 });
  }

  return NextResponse.json(mockPortfolioCompareResponse(body));
}
