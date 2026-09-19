import { isListsEntitled, readEntitlement } from "../stripe/entitlement.ts";
import type { SavedAssetAccess } from "./http.ts";

export async function savedAssetAccessFromRequest(
  request: Request,
): Promise<SavedAssetAccess> {
  const { entitlement } = await readEntitlement(request);
  return { listsEntitled: isListsEntitled(entitlement) };
}
