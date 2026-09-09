import { NextResponse } from "next/server";
import { SAMPLE_FUNDS } from "@/data/seed";
import {
  isValidTickerSymbol,
  normalizeTickerSymbol,
  TICKER_REQUEST,
  type TickerRequestInput,
} from "@/lib/data-api/request-ticker";

export const dynamic = "force-dynamic";

/**
 * Stub for Data team POST /request/ticker.
 * No auth in beta. Queued tickers do not invent performance or distributions.
 */
export async function POST(request: Request) {
  let body: TickerRequestInput = { ticker: "" };
  try {
    body = (await request.json()) as TickerRequestInput;
  } catch {
    return NextResponse.json({ detail: "Invalid JSON body" }, { status: 400 });
  }

  const ticker = normalizeTickerSymbol(body.ticker);
  if (!isValidTickerSymbol(ticker)) {
    return NextResponse.json({ detail: "invalid ticker", ticker }, { status: 422 });
  }

  const covered = SAMPLE_FUNDS.some(
    (fund) => fund.ticker.toUpperCase() === ticker,
  );
  if (covered) {
    return NextResponse.json({ status: "already_covered", ticker });
  }

  return NextResponse.json(
    {
      id: `req_${ticker}`,
      ticker,
      status: "queued",
      message: TICKER_REQUEST.issuerSearch,
    },
    { status: 201 },
  );
}
