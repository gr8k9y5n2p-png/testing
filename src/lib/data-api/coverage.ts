import { fetchDataApi } from "@/lib/data-api/fetch";
import {
  TOP_ADVISOR_FAMILIES,
  type CoverageTier,
  type FundFamilyCoverage,
} from "@/lib/coverage";

export type DataFundFamily = {
  slug: string;
  display_name: string;
  implemented?: boolean;
  coverage_tier?: string;
  aum_rank?: number | null;
  priority?: number | null;
  notes?: string | null;
};

export type DataCoverageSnapshot = {
  top_n: number;
  implemented_count: number;
  stub_count: number;
  implemented_pct: number;
  logged_gap_count: number;
  families: FundFamilyCoverage[];
};

function asTier(value: string | undefined, implemented?: boolean): CoverageTier {
  if (implemented === true || value === "implemented" || value === "live") return "live";
  if (value === "uncovered") return "uncovered";
  return "planned";
}

export function normalizeFundFamily(row: DataFundFamily): FundFamilyCoverage {
  return {
    display_name: row.display_name,
    slug: row.slug,
    coverage_tier: asTier(row.coverage_tier, row.implemented),
    priority: row.priority ?? row.aum_rank ?? 99,
    aum_rank: row.aum_rank ?? null,
  };
}

function parseFamilies(payload: unknown): FundFamilyCoverage[] {
  if (Array.isArray(payload)) {
    return payload.map((row) => normalizeFundFamily(row as DataFundFamily));
  }
  if (payload && typeof payload === "object" && "families" in payload) {
    const families = (payload as { families?: unknown }).families;
    if (Array.isArray(families)) {
      return families.map((row) => normalizeFundFamily(row as DataFundFamily));
    }
  }
  return [];
}

export async function loadCoverageSnapshot(): Promise<DataCoverageSnapshot> {
  try {
    const coverageRes = await fetchDataApi("/coverage");
    if (coverageRes.ok) {
      const raw = (await coverageRes.json()) as Record<string, unknown>;
      const families = parseFamilies(raw);
      if (families.length) {
        return {
          top_n: Number(raw.top_n ?? families.length),
          implemented_count: Number(raw.implemented_count ?? families.filter((f) => f.coverage_tier === "live").length),
          stub_count: Number(raw.stub_count ?? families.filter((f) => f.coverage_tier !== "live").length),
          implemented_pct: Number(raw.implemented_pct ?? 0),
          logged_gap_count: Number(raw.logged_gap_count ?? 0),
          families,
        };
      }
    }
  } catch {
    /* fall through */
  }

  try {
    const familiesRes = await fetchDataApi("/fund-families");
    if (familiesRes.ok) {
      const families = parseFamilies(await familiesRes.json());
      if (families.length) {
        const live = families.filter((f) => f.coverage_tier === "live").length;
        return {
          top_n: families.length,
          implemented_count: live,
          stub_count: families.length - live,
          implemented_pct: families.length ? Math.round((1000 * live) / families.length) / 10 : 0,
          logged_gap_count: 0,
          families,
        };
      }
    }
  } catch {
    /* fall through */
  }

  const live = TOP_ADVISOR_FAMILIES.filter((f) => f.coverage_tier === "live").length;
  return {
    top_n: TOP_ADVISOR_FAMILIES.length,
    implemented_count: live,
    stub_count: TOP_ADVISOR_FAMILIES.length - live,
    implemented_pct: Math.round((1000 * live) / TOP_ADVISOR_FAMILIES.length) / 10,
    logged_gap_count: 0,
    families: TOP_ADVISOR_FAMILIES,
  };
}
