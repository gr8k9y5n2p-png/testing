/**
 * Coverage model for Data team GET /fund-families and GET /coverage
 * (`coverage_tier`, `priority`, `aum_rank`) and POST /coverage/gaps.
 *
 * Live ingest fallback (when the Data API is down): Capital Group / American Funds.
 * Other families must be flagged so tax impact is not silently understated.
 */

import { dataApiUrl, isRemoteDataApi } from "@/lib/data-api/config";

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

const FAMILY_ALIASES: Record<string, string> = {
  "american funds": "capital_group",
  "capital group": "capital_group",
  "j.p. morgan am": "jpmorgan",
  "j.p. morgan asset management": "jpmorgan",
  "blackrock / ishares": "blackrock",
  "state street / spdr": "state_street",
  "goldman sachs am": "goldman_sachs",
  "t. rowe price": "t_rowe_price",
};

export function familySlug(family: string): string {
  const key = family.trim().toLowerCase();
  if (FAMILY_ALIASES[key]) return FAMILY_ALIASES[key];
  return key.replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "");
}

export function findFamilyCoverage(
  family: string,
  families: FundFamilyCoverage[] = TOP_ADVISOR_FAMILIES,
): FundFamilyCoverage | undefined {
  const slug = familySlug(family);
  const lower = family.trim().toLowerCase();
  return families.find(
    (item) =>
      item.slug === slug ||
      item.display_name.toLowerCase() === lower ||
      familySlug(item.display_name) === slug,
  );
}

export function isLiveCoveredFamily(
  family: string,
  families: FundFamilyCoverage[] = TOP_ADVISOR_FAMILIES,
): boolean {
  const match = findFamilyCoverage(family, families);
  if (match) return match.coverage_tier === "live";
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
  const endpoint = dataApiUrl("/coverage/gaps");
  const fallback = "/api/coverage/gaps";
  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (isRemoteDataApi() && !response.ok && response.status >= 500) {
      await fetch(fallback, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
    }
  } catch {
    if (isRemoteDataApi()) {
      try {
        await fetch(fallback, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
      } catch {
        /* Gap logging is best-effort; never block illustrate. */
      }
    }
  }
}
