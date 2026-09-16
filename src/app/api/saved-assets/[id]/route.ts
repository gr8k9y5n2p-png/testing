import { handleSavedAssetItem } from "@/lib/saved-assets/http";
import { getSavedAssetStore } from "@/lib/saved-assets/store";

export const dynamic = "force-dynamic";

/**
 * GET / PATCH / DELETE /api/saved-assets/:id
 * 404 when missing or owned by another account — do not leak existence.
 */
export async function GET(
  request: Request,
  context: { params: Promise<{ id: string }> },
) {
  const { id } = await context.params;
  return handleSavedAssetItem(request, id, getSavedAssetStore());
}

export async function PATCH(
  request: Request,
  context: { params: Promise<{ id: string }> },
) {
  const { id } = await context.params;
  return handleSavedAssetItem(request, id, getSavedAssetStore());
}

export async function DELETE(
  request: Request,
  context: { params: Promise<{ id: string }> },
) {
  const { id } = await context.params;
  return handleSavedAssetItem(request, id, getSavedAssetStore());
}
