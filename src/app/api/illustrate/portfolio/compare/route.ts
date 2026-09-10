import { NextResponse } from "next/server";
import { toDataApiTaxRates } from "@/lib/illustrate/compare-request";
import { proxyLiveOrDemo } from "@/lib/illustrate/illustrate-route";
import { toPortfolioCompareRequestBody } from "@/lib/illustrate/portfolio-compare-client";
import {
  isPortfolioCompareRequestValid,
  mockPortfolioCompareResponse,
} from "@/lib/illustrate/portfolio-compare-fixture";
import type { PortfolioCompareRequest } from "@/lib/illustrate/portfolio-compare-types";

export const dynamic = "force-dynamic";

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

/**
 * Same-origin Portfolio Compare. Maps UI tax_rates aliases, then proxies to
 * the Data API when configured. Production never returns seed-math + MOCK banners.
 */
export async function POST(request: Request) {
  let raw: unknown;
  try {
    raw = await request.json();
  } catch {
    return NextResponse.json({ detail: "Invalid JSON body" }, { status: 400 });
  }

  const incoming = asRecord(raw);
  const body = toPortfolioCompareRequestBody({
    ...(incoming as unknown as PortfolioCompareRequest),
    tax_rates: toDataApiTaxRates(
      incoming.tax_rates as Record<string, unknown> | undefined,
    ),
  });

  const invalid = isPortfolioCompareRequestValid(body as PortfolioCompareRequest);
  if (invalid) {
    return NextResponse.json({ detail: invalid }, { status: 422 });
  }

  return proxyLiveOrDemo({
    path: "/illustrate/portfolio/compare",
    body,
    unavailableDetail: "Portfolio compare is unavailable from the Data API.",
    mock: () => mockPortfolioCompareResponse(body as PortfolioCompareRequest),
  });
}
