import { handleAccountSignUp } from "@/lib/account/http";

export const dynamic = "force-dynamic";

/** POST /api/account/signup { email, password } — sets aftertax_account. */
export async function POST(request: Request) {
  return handleAccountSignUp(request);
}
