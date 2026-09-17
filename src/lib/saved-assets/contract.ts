/**
 * Shared saved-assets contract for Website Lists and Modules Portfolios.
 *
 * Import this module (or `@/components/illustrate`) — do not fork fetch.
 *
 * Auth required: email/password Account session cookie `aftertax_account`
 * (`acct_<uuid>.<hmac>`), issued on sign-up / sign-in. Saved-assets
 * requests without a session are 401. Stripe Checkout sets
 * `stripeCustomerId` (`cus_…`) on the same account email.
 *
 * Every row is scoped to that account id. Cross-account get/update/delete
 * is 404 (no existence leak). Soft-wall / Checkout do not gate Save/Open.
 */

export const SAVED_ASSETS_API_PATH = "/api/saved-assets" as const;
export const SAVED_ASSET_TYPES = ["list", "portfolio"] as const;
export const PORTFOLIO_PAYLOAD_VERSION = 1 as const;

/**
 * HTTP surface
 *
 * | Method | Path                         | Body                         | Success |
 * | ------ | ---------------------------- | ---------------------------- | ------- |
 * | GET    | /api/saved-assets?type=list  | —                            | 200 `{ items, count }` |
 * | GET    | /api/saved-assets?type=portfolio | —                        | 200 `{ items, count }` |
 * | POST   | /api/saved-assets            | `{ type, name, payload }`    | 201 create / 200 name upsert |
 * | GET    | /api/saved-assets/:id        | —                            | 200 `{ item }` |
 * | PATCH  | /api/saved-assets/:id        | `{ name?, payload? }`        | 200 `{ item }` |
 * | DELETE | /api/saved-assets/:id        | —                            | 200 `{ ok: true }` |
 */
export const SAVED_ASSETS_ENDPOINTS = {
  collection: SAVED_ASSETS_API_PATH,
  item: (id: string) => `${SAVED_ASSETS_API_PATH}/${encodeURIComponent(id)}`,
} as const;

/** Persisted row. `accountId` is never taken from the client body. */
export type SavedAssetRecord = {
  id: string;
  accountId: string;
  type: "list" | "portfolio";
  name: string;
  payload: unknown;
  createdAt: string;
  updatedAt: string;
};

export type SavedAssetCollectionResponse = {
  items: SavedAssetRecord[];
  count: number;
};

export type SavedAssetItemResponse = {
  item: SavedAssetRecord;
};

export type SavedAssetWriteBody = {
  type: "list" | "portfolio";
  name: string;
  payload: ListAssetPayload | PortfolioAssetPayload | Record<string, unknown>;
};

export type SavedAssetPatchBody = {
  name?: string;
  payload?: SavedAssetWriteBody["payload"];
};

/** Website Lists payload. Tickers only — no invented fund data. */
export type ListAssetPayload = {
  tickers: string[];
};

/**
 * Modules Portfolios envelope. Extra keys on `books` are allowed and stored.
 * Website does not interpret holdings beyond save/open.
 */
export type PortfolioAssetPayload = {
  version: typeof PORTFOLIO_PAYLOAD_VERSION;
  books: {
    bookDollars: number;
    current: unknown[];
    proposed: unknown[];
    currentUnit?: "pct" | "usd";
    proposedUnit?: "pct" | "usd";
    [key: string]: unknown;
  };
};

export const SAVED_ASSETS_CONTRACT = {
  apiPath: SAVED_ASSETS_API_PATH,
  types: SAVED_ASSET_TYPES,
  portfolioPayloadVersion: PORTFOLIO_PAYLOAD_VERSION,
  accountCookie: "aftertax_account",
  auth:
    "Email/password Account session required. Cookie aftertax_account. stripeCustomerId linked by Checkout on the same email.",
} as const;
