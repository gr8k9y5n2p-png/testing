/**
 * Account-scoped saved assets.
 *
 * Types:
 * - `list` — ticker list (Lists page). Payload `{ tickers: string[] }`.
 * - `portfolio` — Current/Proposed books + holdings. Payload is opaque JSON
 *   Modules owns. Website stores it as-is; see `portfolio-payload.ts` for the
 *   suggested snapshot shape `PortfolioCompare` already exposes.
 *
 * CRUD lives at `/api/saved-assets`. Every row is scoped to `accountId`
 * from the Account session cookie (`src/lib/account/session.ts`).
 */

export const SAVED_ASSET_TYPES = ["list", "portfolio"] as const;
export type SavedAssetType = (typeof SAVED_ASSET_TYPES)[number];

export const SAVED_ASSET_NAME_MAX = 80;

export type SavedAsset = {
  id: string;
  accountId: string;
  type: SavedAssetType;
  name: string;
  payload: unknown;
  createdAt: string;
  updatedAt: string;
};

export type SavedAssetWrite = {
  type: SavedAssetType;
  name: string;
  payload: unknown;
};

export type SavedAssetPatch = {
  name?: string;
  payload?: unknown;
};

export type ListAssetPayload = {
  tickers: string[];
};

export function isSavedAssetType(value: unknown): value is SavedAssetType {
  return value === "list" || value === "portfolio";
}
