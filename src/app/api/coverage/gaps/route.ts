import { NextResponse } from "next/server";
import { SAMPLE_FUNDS } from "@/data/seed";
import { isLiveCoveredFamily, type CoverageGapIn } from "@/lib/coverage";

export const dynamic = "force-dynamic";

/**
 * Stub for Data team POST /coverage/gaps.
 * Accepts ticker / fund_name / fund_family / holding_dollars.
 */
export async function POST(request: Request) {
  let body: CoverageGapIn = {};
  try {
    body = (await request.json()) as CoverageGapIn;
  } catch {
    return NextResponse.json({ detail: "Invalid JSON body" }, { status: 400 });
  }

  const tickers = body.ticker ? [body.ticker] : [];
  if (!tickers.length && !body.fund_name) {
    return NextResponse.json(
      { detail: "ticker or fund_name is required" },
      { status: 422 },
    );
  }

  const ticker = body.ticker;
  const fund = ticker
    ? SAMPLE_FUNDS.find((item) => item.ticker.toUpperCase() === ticker.toUpperCase())
    : SAMPLE_FUNDS.find(
        (item) =>
          body.fund_name &&
          item.fundName.toLowerCase() === body.fund_name.toLowerCase(),
      );

  const family = fund?.family ?? body.fund_family ?? null;
  const covered = family ? isLiveCoveredFamily(family) : false;

  return NextResponse.json({
    stub: true,
    ticker: fund?.ticker ?? ticker ?? null,
    fund_name: fund?.fundName ?? body.fund_name ?? null,
    fund_family: family,
    holding_dollars: body.holding_dollars ?? null,
    adapter_implemented: covered,
    suggested_next_step: covered
      ? "Family is in live ingest; no gap."
      : "Flagged as uncovered. Do not treat sample illustrate dollars as book-complete.",
    detail: covered
      ? null
      : `${family ?? "Unknown family"} is not in live ingest yet (Capital Group is live today).`,
    note: "Replace with Data team POST /coverage/gaps when NEXT_PUBLIC_DATA_API_URL is set.",
  });
}
