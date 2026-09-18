import { mapFundsApiItem, type FundsApiItem } from "@/data/funds-list";
import { isRemoteDataApi } from "@/lib/data-api/config";
import { fetchDataApi } from "@/lib/data-api/fetch";
import { looksLikeExactTicker } from "@/lib/data-api/request-ticker";

export const maxDuration = 10;

function isFundsApiItem(row: unknown): row is FundsApiItem {
  if (!row || typeof row !== "object") return false;
  const record = row as Record<string, unknown>;
  return (
    "fund_name" in record ||
    "fund_identifier" in record ||
    "fundName" in record ||
    "ticker" in record
  );
}

function itemFromLookupPayload(payload: unknown): FundsApiItem | null {
  if (!payload || typeof payload !== "object") return null;
  const record = payload as {
    item?: unknown;
    items?: unknown;
    data?: unknown;
  };
  if (isFundsApiItem(payload)) return payload;
  if (isFundsApiItem(record.item)) return record.item;
  if (Array.isArray(record.items) && isFundsApiItem(record.items[0])) {
    return record.items[0];
  }
  if (isFundsApiItem(record.data)) return record.data;
  return null;
}

/**
 * Exact ticker confirm. Data GET /funds/lookup with ticker= only.
 * Do not call GET /funds with a ticker query param — that is not a filter
 * and returns a default page. Miss → 404 not_in_universe. No hydrate.
 */
export async function GET(request: Request) {
  const ticker = (
    new URL(request.url).searchParams.get("ticker") ?? ""
  )
    .trim()
    .toUpperCase();
  if (!looksLikeExactTicker(ticker)) {
    return Response.json({ error: "invalid_ticker", items: [] }, { status: 400 });
  }
  if (!isRemoteDataApi()) {
    return Response.json(
      { error: "not_in_universe", ticker, items: [] },
      { status: 404 },
    );
  }

  const response = await fetchDataApi(
    `/funds/lookup?ticker=${encodeURIComponent(ticker)}`,
  );
  if (response.status === 404) {
    return Response.json(
      { error: "not_in_universe", ticker, items: [] },
      { status: 404 },
    );
  }
  if (!response.ok) {
    return Response.json(
      {
        error: "upstream",
        source: { kind: "live", label: "Data API /funds/lookup unavailable" },
        items: [],
      },
      { status: 503 },
    );
  }

  const item = itemFromLookupPayload(await response.json().catch(() => null));
  const matchTicker = (item?.ticker ?? "").trim().toUpperCase();
  if (!item || matchTicker !== ticker) {
    return Response.json(
      { error: "not_in_universe", ticker, items: [] },
      { status: 404 },
    );
  }

  const view = mapFundsApiItem(item);
  return Response.json({
    source: { kind: "live", label: "Data API /funds/lookup" },
    ticker,
    item: view,
    items: [view],
  });
}
