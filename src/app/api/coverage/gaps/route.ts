import { NextResponse } from "next/server";
import { SAMPLE_FUNDS } from "@/data/seed";
import { isLiveCoveredFamily } from "@/lib/coverage";

export const dynamic = "force-dynamic";

/**
 * Stub for upcoming Data team POST /coverage/gaps.
 * Flags tickers whose family is not in live ingest (Capital Group today).
 */
export async function POST(request: Request) {
  let tickers: string[] = [];
  try {
    const body = (await request.json()) as { tickers?: string[] };
    tickers = body.tickers ?? [];
  } catch {
    return NextResponse.json({ detail: "Invalid JSON body" }, { status: 400 });
  }

  const uncovered = tickers
    .map((ticker) => {
      const fund = SAMPLE_FUNDS.find(
        (item) => item.ticker.toUpperCase() === ticker.toUpperCase(),
      );
      if (!fund) {
        return {
          ticker,
          reason: "Ticker is not in the current sample/ingest universe.",
        };
      }
      if (!isLiveCoveredFamily(fund.family)) {
        return {
          ticker: fund.ticker,
          family: fund.family,
          reason: `${fund.family} is not in live ingest yet. Illustration uses sample data.`,
        };
      }
      return null;
    })
    .filter((item) => item != null);

  return NextResponse.json({
    stub: true,
    uncovered,
    note: "Replace with Data team POST /coverage/gaps when available.",
  });
}
