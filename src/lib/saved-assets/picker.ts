/**
 * Open-dialog helpers for account-scoped saved assets.
 * Delete is wired to DELETE /api/saved-assets/:id (session-scoped).
 */

export function savedAssetDeleteLabel(
  type: "list" | "portfolio",
  name: string,
): string {
  return type === "list" ? `Delete list ${name}` : `Delete portfolio ${name}`;
}

export function savedAssetDeleteConfirm(
  type: "list" | "portfolio",
  name: string,
): string {
  return type === "list"
    ? `Delete list ${name}?`
    : `Delete portfolio ${name}?`;
}

export function applyDeletedPickerItem<T extends { id: string }>(
  items: readonly T[],
  selectedId: string | null,
  deletedId: string,
): { items: T[]; selectedId: string | null } {
  return {
    items: items.filter((row) => row.id !== deletedId),
    selectedId: selectedId === deletedId ? null : selectedId,
  };
}
