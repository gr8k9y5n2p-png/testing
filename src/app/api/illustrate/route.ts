import { NextResponse } from "next/server";
import { IllustrateHttpError, mockIllustrate } from "@/lib/illustrate/mock-engine";
import type { IllustrateRequest } from "@/lib/illustrate/types";

export const dynamic = "force-dynamic";

/**
 * MOCK POST /illustrate.
 * Production math lives on the Data team service. This route exists so the
 * Aftertax UI can demo without that backend. Point NEXT_PUBLIC_ILLUSTRATE_URL
 * at the real host to skip this mock.
 */
export async function POST(request: Request) {
  let body: IllustrateRequest;
  try {
    body = (await request.json()) as IllustrateRequest;
  } catch {
    return NextResponse.json({ detail: "Invalid JSON body" }, { status: 400 });
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
