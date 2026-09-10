import { NextResponse } from "next/server";
import { IllustrateHttpError, mockIllustrate } from "@/lib/illustrate/mock-engine";
import { proxyLiveOrDemo } from "@/lib/illustrate/illustrate-route";
import { toDataApiIllustrateBody } from "@/lib/illustrate/illustrate-request";
import type { IllustrateRequest } from "@/lib/illustrate/types";

export const dynamic = "force-dynamic";

/**
 * POST /api/illustrate.
 * Live Data API when configured. Production never runs seed math or emits
 * MOCK banners — even if NEXT_PUBLIC_* was missing from the client bundle.
 */
export async function POST(request: Request) {
  let body: IllustrateRequest;
  try {
    body = (await request.json()) as IllustrateRequest;
  } catch {
    return NextResponse.json({ detail: "Invalid JSON body" }, { status: 400 });
  }

  try {
    return await proxyLiveOrDemo({
      path: "/illustrate",
      body: toDataApiIllustrateBody(body),
      unavailableDetail: "Illustrate is unavailable from the Data API.",
      mock: () => mockIllustrate(body),
    });
  } catch (error) {
    if (error instanceof IllustrateHttpError) {
      return NextResponse.json(
        { detail: error.message, code: error.code },
        { status: error.status },
      );
    }
    throw error;
  }
}
