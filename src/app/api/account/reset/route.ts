import { handleAccountReset } from "@/lib/account/http";

export const dynamic = "force-dynamic";

/** POST /api/account/reset { token, password } — sets aftertax_account. */
export async function POST(request: Request) {
  return handleAccountReset(request);
}
