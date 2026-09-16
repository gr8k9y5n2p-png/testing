import { handleSavedAssetsCollection } from "@/lib/saved-assets/http";
import { getSavedAssetStore } from "@/lib/saved-assets/store";

export const dynamic = "force-dynamic";

/**
 * Account-scoped saved assets.
 * GET  /api/saved-assets?type=list|portfolio
 * POST /api/saved-assets  { type, name, payload }
 *
 * Identity: `aftertax_account` cookie (stub). Stripe Checkout later.
 */
export async function GET(request: Request) {
  return handleSavedAssetsCollection(request, getSavedAssetStore());
}

export async function POST(request: Request) {
  return handleSavedAssetsCollection(request, getSavedAssetStore());
}
