import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import {
  FRIENDS_BETA_COOKIE,
  FRIENDS_BETA_PATH,
  friendsBetaGateDecision,
  friendsBetaPassword,
} from "@/lib/friends-beta";

/**
 * Friends-beta UI gate. On when FRIENDS_BETA_PASSWORD (or BETA_PASSWORD)
 * is set in Vercel Production. Off when unset. /api/* stays public so
 * Data API mocks and Render-backed fetches are not interrupted.
 */
export function proxy(request: NextRequest) {
  const decision = friendsBetaGateDecision({
    password: friendsBetaPassword(),
    pathname: request.nextUrl.pathname,
    search: request.nextUrl.search,
    cookie: request.cookies.get(FRIENDS_BETA_COOKIE)?.value,
  });

  if (decision.action === "next") {
    return NextResponse.next();
  }

  const url = request.nextUrl.clone();
  url.pathname = FRIENDS_BETA_PATH;
  url.search = "";
  if (decision.next && decision.next !== "/") {
    url.searchParams.set("next", decision.next);
  }
  return NextResponse.redirect(url);
}

export const config = {
  matcher: [
    "/((?!api|_next/static|_next/image|_next/webpack-hmr|favicon.ico|robots.txt|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)",
  ],
};
