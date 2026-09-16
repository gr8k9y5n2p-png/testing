import { handleAccountSignOut } from "@/lib/account/http";

export const dynamic = "force-dynamic";

/** POST /api/account/signout — clears aftertax_account. */
export async function POST(request: Request) {
  return handleAccountSignOut(request);
}
