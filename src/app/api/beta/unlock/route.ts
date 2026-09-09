import { NextResponse } from "next/server";
import {
  FRIENDS_BETA_COOKIE,
  FRIENDS_BETA_PATH,
  friendsBetaCookieOptions,
  friendsBetaPassword,
  friendsBetaSessionToken,
  passwordsMatch,
  safeNextPath,
} from "@/lib/friends-beta";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const form = await request.formData();
  const submitted = String(form.get("password") ?? "");
  const next = safeNextPath(String(form.get("next") ?? "/"));
  const expected = friendsBetaPassword();

  if (!expected) {
    return NextResponse.redirect(new URL(next, request.url), 303);
  }

  if (!passwordsMatch(submitted, expected)) {
    const url = new URL(FRIENDS_BETA_PATH, request.url);
    url.searchParams.set("error", "1");
    if (next !== "/") url.searchParams.set("next", next);
    return NextResponse.redirect(url, 303);
  }

  const response = NextResponse.redirect(new URL(next, request.url), 303);
  response.cookies.set(
    FRIENDS_BETA_COOKIE,
    friendsBetaSessionToken(expected),
    friendsBetaCookieOptions(new URL(request.url).protocol === "https:"),
  );
  return response;
}
