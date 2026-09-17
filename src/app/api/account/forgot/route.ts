import { handleAccountForgot } from "@/lib/account/http";

export const dynamic = "force-dynamic";

/** POST /api/account/forgot { email } — always 200 if the email is valid. */
export async function POST(request: Request) {
  return handleAccountForgot(request);
}
