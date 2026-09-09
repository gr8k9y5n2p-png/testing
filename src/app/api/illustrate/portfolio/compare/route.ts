import { NextResponse } from "next/server";
import { toDataApiTaxRates } from "@/lib/illustrate/compare-request";
import {
  getPortfolioCompareUpstream,
  toPortfolioCompareRequestBody,
} from "@/lib/illustrate/portfolio-compare-client";
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
 * the Data API when configured. Localhost without an upstream stays on the
 * sketch fixture — never seed-math + MOCK banners on Production.
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

  const upstream = getPortfolioCompareUpstream();
  if (upstream) {
    try {
      const response = await fetch(upstream, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(body),
        cache: "no-store",
      });
      const text = await response.text();
      const contentType = response.headers.get("content-type") ?? "application/json";
      return new NextResponse(text, {
        status: response.status,
        headers: { "Content-Type": contentType },
      });
    } catch {
      return NextResponse.json(
        { detail: "Portfolio compare is unavailable from the Data API." },
        { status: 503 },
      );
    }
  }

  return NextResponse.json(
    mockPortfolioCompareResponse(body as PortfolioCompareRequest),
  );
}
