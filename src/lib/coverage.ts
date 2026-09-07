/**
 * Coverage model for upcoming Data team GET /fund-families
 * (`coverage_tier`, `priority`, `aum_rank`) and POST /coverage/gaps.
 *
 * Live ingest today: Capital Group / American Funds. Illustrate still runs on
 * sample rows for other families, but the UI must flag the gap so tax impact
 * is not silently understated.
 */

export type CoverageTier = "live" | "planned" | "uncovered";

export type FundFamilyCoverage = {
  display_name: string;
  slug: string;
  coverage_tier: CoverageTier;
  /** 1 = highest AUM / advisor relevance among the top-10 plan. */
  priority: number;
  aum_rank: number | null;
};

export const TOP_ADVISOR_FAMILIES: FundFamilyCoverage[] = [
  { display_name: "BlackRock / iShares", slug: "blackrock", coverage_tier: "planned", priority: 1, aum_rank: 1 },
  { display_name: "Vanguard", slug: "vanguard", coverage_tier: "planned", priority: 2, aum_rank: 2 },
  { display_name: "Fidelity", slug: "fidelity", coverage_tier: "planned", priority: 3, aum_rank: 3 },
  { display_name: "State Street / SPDR", slug: "state_street", coverage_tier: "planned", priority: 4, aum_rank: 4 },
  { display_name: "J.P. Morgan AM", slug: "jpmorgan", coverage_tier: "planned", priority: 5, aum_rank: 5 },
  { display_name: "Goldman Sachs AM", slug: "goldman_sachs", coverage_tier: "planned", priority: 6, aum_rank: 6 },
  { display_name: "Capital Group", slug: "capital_group", coverage_tier: "live", priority: 7, aum_rank: 7 },
  { display_name: "PIMCO", slug: "pimco", coverage_tier: "planned", priority: 8, aum_rank: 8 },
  { display_name: "Invesco", slug: "invesco", coverage_tier: "planned", priority: 9, aum_rank: 9 },
  { display_name: "T. Rowe Price", slug: "t_rowe_price", coverage_tier: "planned", priority: 10, aum_rank: 10 },
];

/** Seed uses "American Funds" for Capital Group products. */
export const LIVE_INGEST_FAMILIES = new Set(["American Funds", "Capital Group"]);

export const PLANNED_COVERAGE_FAMILIES = TOP_ADVISOR_FAMILIES.map(
  (family) => family.display_name,
);

export function isLiveCoveredFamily(family: string): boolean {
  return LIVE_INGEST_FAMILIES.has(family);
}

export type CoverageGapIn = {
  ticker?: string;
  fund_name?: string;
  fund_family?: string;
  holding_dollars?: number;
};

export async function reportCoverageGap(body: CoverageGapIn): Promise<void> {
  if (!body.ticker && !body.fund_name) return;
  const base = process.env.NEXT_PUBLIC_DATA_API_URL?.replace(/\/$/, "");
  const endpoint = base ? `${base}/coverage/gaps` : "/api/coverage/gaps";
  try {
    await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    /* Gap logging is best-effort; never block illustrate. */
  }
}
