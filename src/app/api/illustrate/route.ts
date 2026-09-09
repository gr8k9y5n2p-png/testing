import { NextResponse } from "next/server";
import {
  getLiveIllustrateUrl,
  proxyLiveDataApiPost,
} from "@/lib/data-api/config";
import { IllustrateHttpError, mockIllustrate } from "@/lib/illustrate/mock-engine";
import { toDataApiIllustrateBody } from "@/lib/illustrate/illustrate-request";
import type { IllustrateRequest } from "@/lib/illustrate/types";

export const dynamic = "force-dynamic";

/**
 * POST /api/illustrate.
 * When NEXT_PUBLIC_DATA_API_URL or NEXT_PUBLIC_ILLUSTRATE_URL is set (Vercel
 * Production), proxy the live Data API. Never run seed math or emit MOCK banners.
 * Localhost without those env vars still uses the demo engine.
 */
export async function POST(request: Request) {
  let body: IllustrateRequest;
  try {
    body = (await request.json()) as IllustrateRequest;
  } catch {
    return NextResponse.json({ detail: "Invalid JSON body" }, { status: 400 });
  }

  const live = getLiveIllustrateUrl("/illustrate");
  if (live) {
    try {
      const upstream = await proxyLiveDataApiPost(live, toDataApiIllustrateBody(body));
      const text = await upstream.text();
      return new NextResponse(text, {
        status: upstream.status,
        headers: { "Content-Type": "application/json" },
      });
    } catch {
      return NextResponse.json(
        { detail: "Illustrate is unavailable from the Data API." },
        { status: 503 },
      );
    }
  }

  try {
    const result = mockIllustrate(body);
    return NextResponse.json(result);
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
