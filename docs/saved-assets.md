# Saved assets contract (Lists + Portfolios)

Modules and Website share one account-scoped store. Import from
`@/lib/saved-assets/contract` or `@/components/illustrate`. Do not fork fetch.

Auth is required. Email/password sign-up and sign-in (Account menu / `/account`)
set a signed httpOnly `aftertax_account` cookie. Saved-assets calls without a
session return **401**. Friends-beta shared password stays a separate site gate.

Stripe Checkout later (held off) creates/links a Stripe Customer on the **same
account email** and stores `stripeCustomerId` (`cus_…`) on the account record.
Do not enable Checkout or the soft-wall here.

## Endpoints

| Method | Path | Body | Success |
| --- | --- | --- | --- |
| GET | `/api/saved-assets?type=list` | — | `200 { items, count }` |
| GET | `/api/saved-assets?type=portfolio` | — | `200 { items, count }` |
| POST | `/api/saved-assets` | `{ type, name, payload }` | `201` create / `200` same-name upsert |
| GET | `/api/saved-assets/:id` | — | `200 { item }` |
| PATCH | `/api/saved-assets/:id` | `{ name?, payload? }` | `200 { item }` |
| DELETE | `/api/saved-assets/:id` | — | `200 { ok: true }` |

Cross-account get / update / delete is **404**. `accountId` is never taken from the body.

## Record shape

```ts
type SavedAssetRecord = {
  id: string;           // sav_<uuid>
  accountId: string;    // acct_<uuid> from email/password Account
  type: "list" | "portfolio";
  name: string;
  payload: unknown;
  createdAt: string;    // ISO
  updatedAt: string;    // ISO
};
```

## List payload (Website)

```ts
{ tickers: string[] }
```

## Portfolio payload (Modules)

Stable envelope. Modules owns `books` (Current / Proposed holdings). Extra keys are stored as-is.

```ts
{
  version: 1,
  books: {
    bookDollars: number,
    current: unknown[],
    proposed: unknown[],
    currentUnit?: "pct" | "usd",
    proposedUnit?: "pct" | "usd",
  }
}
```

Helpers: `toPortfolioAssetPayload(getBooks())` and `parsePortfolioBooksPayload(item.payload)`
(also accepts a flat books object). Never invent holdings.

## Account

| Method | Path | Body |
| --- | --- | --- |
| POST | `/api/account/signup` | `{ email, password }` |
| POST | `/api/account/signin` | `{ email, password }` |
| POST | `/api/account/signout` | — |
| GET | `/api/account/me` | — |

Public account: `{ id, email, stripeCustomerId }` (`stripeCustomerId` is `null` until Checkout).

## Persistence

JSON `SavedAssetStore` — `.data/saved-assets.json` locally, `/tmp/aftertax-saved-assets.json` on Vercel. Override with `SAVED_ASSETS_PATH`. Swap for Neon/Postgres later without changing this HTTP contract.
