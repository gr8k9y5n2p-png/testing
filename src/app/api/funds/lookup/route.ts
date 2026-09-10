import { loadFundLookupFromDataApi } from "@/lib/data-api/fund-lookup";
import { isRemoteDataApi } from "@/lib/data-api/config";
import { normalizeTickerSymbol } from "@/lib/data-api/request-ticker";

export const dynamic = "force-dynamic";

const NO_STORE = { "Cache-Control": "no-store" };

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const ticker = normalizeTickerSymbol(searchParams.get("ticker") ?? "");
  if (!ticker) {
    return Response.json(
      { error: "invalid_ticker" },
      { status: 400, headers: NO_STORE },
    );
  }

  if (!isRemoteDataApi()) {
    return Response.json(
      {
        kind: "not_in_universe",
        ticker,
        addToUniverse: "POST /request/ticker",
        coverage_status: "not_in_universe",
      },
      { status: 404, headers: NO_STORE },
    );
  }

  const result = await loadFundLookupFromDataApi(ticker);
  if (result.kind === "found") {
    return Response.json(
      {
        kind: "found",
        coverage_status: result.coverageStatus,
        fund: result.fund,
        item: result.fund,
      },
      { headers: NO_STORE },
    );
  }
  if (result.kind === "not_in_universe") {
    return Response.json(
      {
        kind: "not_in_universe",
        ticker: result.ticker,
        coverage_status: "not_in_universe",
        add_to_universe: result.addToUniverse,
      },
      { status: 404, headers: NO_STORE },
    );
  }
  return Response.json(
    {
      error: "upstream",
      kind: "unavailable",
      source: { kind: "live", label: "Data API /funds/lookup unavailable" },
    },
    { status: 503, headers: NO_STORE },
  );
}
