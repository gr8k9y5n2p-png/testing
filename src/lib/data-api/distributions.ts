import { withPeerContext } from "@/data/queries";
import type { FundEstimate, FundEstimateView } from "@/data/types";
import { fetchDataApi } from "@/lib/data-api/fetch";

type DataDistribution = {
  id: string;
  fund_family: string;
  fund_name: string;
  fund_identifier: string;
  ticker: string | null;
  cusip: string | null;
  share_class: string | null;
  estimate_type: string;
  amount: string | number | null;
  amount_min: string | number | null;
  amount_max: string | number | null;
  amount_unit: string;
  as_of: string | null;
  publication_stage: string | null;
};

function num(value: string | number | null | undefined): number | null {
  if (value == null || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function midpoint(row: DataDistribution): number {
  const amount = num(row.amount);
  if (amount != null) return amount;
  const min = num(row.amount_min);
  const max = num(row.amount_max);
  if (min != null && max != null) return (min + max) / 2;
  return min ?? max ?? 0;
}

function fundKey(row: DataDistribution): string {
  return (row.ticker || row.fund_identifier || row.id).toUpperCase();
}

const CG_TYPES = new Set([
  "long_term_capital_gains",
  "short_term_capital_gains",
  "total_capital_gains",
  "qualified_short_term_gains",
]);

export function aggregateDistributions(items: DataDistribution[]): FundEstimate[] {
  const grouped = new Map<string, DataDistribution[]>();
  for (const item of items) {
    const key = fundKey(item);
    const list = grouped.get(key) ?? [];
    list.push(item);
    grouped.set(key, list);
  }

  const funds: FundEstimate[] = [];
  for (const [key, rows] of grouped) {
    const dated = rows.filter((row) => row.as_of);
    const latest = dated.length
      ? dated.reduce((best, row) => ((row.as_of ?? "") > (best.as_of ?? "") ? row : best))
      : rows[0];
    const snapshot = latest.as_of
      ? rows.filter((row) => row.as_of === latest.as_of)
      : rows;

    let pctNav = 0;
    let perShare = 0;
    let ordinary = 0;
    let capGains = 0;
    for (const row of snapshot) {
      const value = midpoint(row);
      if (row.amount_unit === "percent_of_nav") {
        pctNav += value;
        if (CG_TYPES.has(row.estimate_type)) capGains += value;
        else ordinary += value;
      } else if (row.amount_unit === "per_share") {
        perShare += value;
        if (CG_TYPES.has(row.estimate_type)) capGains += value;
        else ordinary += value;
      }
    }

    const asOf = latest.as_of ?? new Date().toISOString().slice(0, 10);
    const year = Number(asOf.slice(0, 4)) || new Date().getUTCFullYear();
    funds.push({
      id: `api:${key}`,
      fundName: latest.fund_name,
      ticker: (latest.ticker || latest.fund_identifier || key).toUpperCase(),
      cusip: latest.cusip ?? "",
      family: latest.fund_family,
      category: "—",
      shareClass: latest.share_class ?? "",
      nav: 0,
      estimatedDistributionAmount: perShare,
      estimatedOrdinaryIncome: ordinary,
      estimatedCapitalGains: capGains,
      estimatedDistributionPctNav: pctNav,
      publishedAt: asOf,
      asOfDate: asOf,
      distributionYear: year,
    });
  }
  return funds;
}

export async function loadFundsFromDataApi(): Promise<FundEstimateView[] | null> {
  try {
    const response = await fetchDataApi("/distributions?page_size=200");
    if (!response.ok) return null;
    const payload = (await response.json()) as { items?: DataDistribution[] };
    const items = Array.isArray(payload.items) ? payload.items : [];
    if (!items.length) return null;
    return withPeerContext(aggregateDistributions(items));
  } catch {
    return null;
  }
}
