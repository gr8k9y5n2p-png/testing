import { handleAccountSignIn } from "@/lib/account/http";

export const dynamic = "force-dynamic";

/** POST /api/account/signin { email, password } — sets aftertax_account. */
export async function POST(request: Request) {
  return handleAccountSignIn(request);
}
