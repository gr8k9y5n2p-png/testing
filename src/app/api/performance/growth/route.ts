import { NextResponse } from "next/server";
import {
  isPerformanceRequestValid,
  mockPerformanceResponse,
  PerformanceMockError,
} from "@/lib/performance/mock";
import type { PerformanceGrowthRequest } from "@/lib/performance/types";

export const dynamic = "force-dynamic";

/**
 * MOCK POST /performance/growth.
 * Same Growth of $X payload as GET /performance. Falls back here when the
 * Data API host is unset or down.
 */
export async function POST(request: Request) {
  let body: PerformanceGrowthRequest;
  try {
    body = (await request.json()) as PerformanceGrowthRequest;
  } catch {
    return NextResponse.json({ detail: "Invalid JSON body" }, { status: 400 });
  }

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
