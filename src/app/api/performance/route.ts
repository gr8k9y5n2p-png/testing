import { NextResponse } from "next/server";
import {
  isPerformanceRequestValid,
  mockPerformanceResponse,
  PerformanceMockError,
} from "@/lib/performance/mock";
import type { PerformanceAssetClass, PerformanceGrowthRequest } from "@/lib/performance/types";

export const dynamic = "force-dynamic";

function asAssetClass(value: string | null): PerformanceAssetClass | null {
  if (value === "equity" || value === "fixed_income" || value === "international") {
    return value;
  }
  return null;
}

/**
 * MOCK GET /performance.
 * Production series live on the Data team FastAPI (PR #2).
 * This route returns fixture monthly growth_of_x so localhost still demos.
 */
export async function GET(request: Request) {
  const url = new URL(request.url);
  const body: PerformanceGrowthRequest = {
    ticker: url.searchParams.get("ticker"),
    fund_identifier: url.searchParams.get("fund_identifier"),
    benchmark: url.searchParams.get("benchmark"),
    asset_class: asAssetClass(url.searchParams.get("asset_class")),
    benchmark_hint: asAssetClass(url.searchParams.get("benchmark_hint")),
    start_dollars: url.searchParams.has("start_dollars")
      ? Number(url.searchParams.get("start_dollars"))
      : 10_000,
    start_date: url.searchParams.get("start_date"),
    end_date: url.searchParams.get("end_date"),
    mode: url.searchParams.get("mode") ?? "fixture",
  };

  const invalid = isPerformanceRequestValid(body);
  if (invalid) {
    return NextResponse.json({ detail: invalid }, { status: 422 });
  }

  try {
    return NextResponse.json(mockPerformanceResponse(body));
  } catch (error) {
    if (error instanceof PerformanceMockError) {
      return NextResponse.json({ detail: error.message }, { status: error.status });
    }
    throw error;
  }
}
