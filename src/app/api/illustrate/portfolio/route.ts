import { NextResponse } from "next/server";
import { SAMPLE_FUNDS } from "@/data/seed";
import { isLiveCoveredFamily } from "@/lib/coverage";
import { proxyLiveOrDemo } from "@/lib/illustrate/illustrate-route";
import type { PortfolioIllustrateRequest } from "@/lib/illustrate/portfolio";
import { demoEngineNotes } from "@/lib/illustrate/user-facing-notes";

export const dynamic = "force-dynamic";

/** POST /api/illustrate/portfolio — live Data API when configured; localhost stub otherwise. */
export async function POST(request: Request) {
  let body: PortfolioIllustrateRequest;
  try {
    body = (await request.json()) as PortfolioIllustrateRequest;
  } catch {
    return NextResponse.json({ detail: "Invalid JSON body" }, { status: 400 });
  }

  return proxyLiveOrDemo({
    path: "/illustrate/portfolio",
    body,
    unavailableDetail: "Portfolio illustrate is unavailable from the Data API.",
    mock: () => mockPortfolioCoverage(body),
  });
}

function mockPortfolioCoverage(body: PortfolioIllustrateRequest) {
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
  return {
    coverage: {
      dollars_total: total,
      dollars_covered: covered,
      dollars_uncovered: uncovered,
      coverage_pct: total ? Math.round((covered / total) * 10000) / 100 : 0,
    },
    gaps,
    warnings: demoEngineNotes(
      "MOCK /illustrate/portfolio. Set NEXT_PUBLIC_DATA_API_URL to use the Data team endpoint.",
    ),
  };
}
