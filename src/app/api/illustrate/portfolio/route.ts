import { NextResponse } from "next/server";
import { SAMPLE_FUNDS } from "@/data/seed";
import { isLiveCoveredFamily } from "@/lib/coverage";
import type { PortfolioIllustrateRequest } from "@/lib/illustrate/portfolio";

export const dynamic = "force-dynamic";

/** MOCK POST /illustrate/portfolio — coverage-aware stub until Data API is running. */
export async function POST(request: Request) {
  let body: PortfolioIllustrateRequest;
  try {
    body = (await request.json()) as PortfolioIllustrateRequest;
  } catch {
    return NextResponse.json({ detail: "Invalid JSON body" }, { status: 400 });
  }

  const holdings = body.holdings ?? [];
  let covered = 0;
  let uncovered = 0;
  const gaps: { ticker?: string; fund_family?: string; holding_dollars: number; reason: string }[] =
    [];

  for (const holding of holdings) {
    const fund = SAMPLE_FUNDS.find(
      (item) =>
        (holding.ticker && item.ticker.toUpperCase() === holding.ticker.toUpperCase()) ||
        (holding.fund_identifier &&
          item.ticker.toUpperCase() === holding.fund_identifier.toUpperCase()),
    );
    const dollars = holding.holding_dollars ?? 0;
    const family = fund?.family ?? holding.fund_family;
    if (fund && isLiveCoveredFamily(fund.family)) {
      covered += dollars;
    } else {
      uncovered += dollars;
      gaps.push({
        ticker: holding.ticker ?? fund?.ticker,
        fund_family: family,
        holding_dollars: dollars,
        reason: family
          ? `${family} is not in live ingest yet.`
          : "Ticker is not in the current universe.",
      });
    }
  }

  const total = covered + uncovered;
  return NextResponse.json({
    coverage: {
      dollars_total: total,
      dollars_covered: covered,
      dollars_uncovered: uncovered,
      coverage_pct: total ? Math.round((covered / total) * 10000) / 100 : 0,
    },
    gaps,
    warnings: [
      "MOCK /illustrate/portfolio. Set NEXT_PUBLIC_DATA_API_URL to use the Data team endpoint.",
    ],
  });
}
