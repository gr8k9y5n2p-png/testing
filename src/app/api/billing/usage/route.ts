import { NextResponse } from "next/server";
import { isHttpsRequest } from "@/lib/account/session";
import { normalizeUsage, type UsageKind } from "@/lib/billing/limits";
import {
  mergeSignedInUsage,
  recordUsage,
  serializeUsageCookie,
} from "@/lib/stripe/entitlement";

export const dynamic = "force-dynamic";

const KINDS = new Set<UsageKind>(["search", "compare", "portfolio"]);

/**
 * POST { kind, key? } increments a freemium counter.
 * POST { merge: DeviceUsage } merges anonymous device usage into the account.
 */
export async function POST(request: Request) {
  let body: {
    kind?: unknown;
    key?: unknown;
    merge?: unknown;
  } = {};
  try {
    body = (await request.json()) as typeof body;
  } catch {
    return NextResponse.json({ detail: "Invalid JSON body." }, { status: 400 });
  }

  if (body.merge && typeof body.merge === "object") {
    const { entitlement, usage } = await mergeSignedInUsage(
      request,
      normalizeUsage(body.merge),
    );
    const response = NextResponse.json(entitlement);
    response.headers.append(
      "set-cookie",
      serializeUsageCookie(usage, isHttpsRequest(request)),
    );
    return response;
  }

  const kind = typeof body.kind === "string" ? body.kind : "";
  if (!KINDS.has(kind as UsageKind)) {
    return NextResponse.json({ detail: "Unknown usage kind." }, { status: 400 });
  }
  const key = typeof body.key === "string" ? body.key : undefined;
  const { entitlement, usage } = await recordUsage(
    request,
    kind as UsageKind,
    key,
  );
  const response = NextResponse.json(entitlement);
  response.headers.append(
    "set-cookie",
    serializeUsageCookie(usage, isHttpsRequest(request)),
  );
  return response;
}
