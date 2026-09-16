import { handleAccountMe } from "@/lib/account/http";

export const dynamic = "force-dynamic";

/** GET /api/account/me — public account or { account: null }. */
export async function GET(request: Request) {
  return handleAccountMe(request);
}
