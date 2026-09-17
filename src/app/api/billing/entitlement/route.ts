import { NextResponse } from "next/server";
import { isHttpsRequest } from "@/lib/account/session";
import {
  readEntitlement,
  serializeUsageCookie,
} from "@/lib/stripe/entitlement";

export const dynamic = "force-dynamic";

/** Current subscription + freemium counters (account or device cookie). */
export async function GET(request: Request) {
  const { entitlement } = await readEntitlement(request);
  const response = NextResponse.json(entitlement);
  response.headers.append(
    "set-cookie",
    serializeUsageCookie(entitlement.usage, isHttpsRequest(request)),
  );
  return response;
}
