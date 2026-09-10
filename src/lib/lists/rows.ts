/**
 * Lists table rows: unpaid announced estimates + live NAV only.
 * Paid / final history never becomes Upcoming. Missing stays null → UI "—".
 */

import type { DataDistribution } from "../../data/aggregate-distributions.ts";
import {
  distributionBucket,
  isoDate,
  isUpcomingFund,
} from "../../data/distribution-bucket.ts";
import { hideUpcomingAmounts } from "../../data/hydrate-funds.ts";
import type { FundEstimateView } from "../../data/types.ts";
import { GROWTH_TAX_TYPE_LABELS } from "../illustrate/growth-tax-by-type.ts";
import {
  parsePositiveNav,
  resolvePctOfNav,
} from "../illustrate/nav-math.ts";

/** Data API component types the Lists table shows as their own columns. */
export const LIST_ESTIMATE_TYPES = [
  "long_term_capital_gains",
  "short_term_capital_gains",
  "ordinary_income",
  "qualified_dividend",
] as const;

export type ListEstimateType = (typeof LIST_ESTIMATE_TYPES)[number];

export const LIST_ESTIMATE_TYPE_LABELS: Record<ListEstimateType, string> = {
  long_term_capital_gains: GROWTH_TAX_TYPE_LABELS.long_term_capital_gains,
  short_term_capital_gains: GROWTH_TAX_TYPE_LABELS.short_term_capital_gains,
  ordinary_income: GROWTH_TAX_TYPE_LABELS.ordinary_income,
  qualified_dividend: GROWTH_TAX_TYPE_LABELS.qualified_dividend,
};

const TYPE_ALIASES: Record<string, ListEstimateType> = {
  long_term_capital_gains: "long_term_capital_gains",
  ltcg: "long_term_capital_gains",
  short_term_capital_gains: "short_term_capital_gains",
  qualified_short_term_gains: "short_term_capital_gains",
  stcg: "short_term_capital_gains",
  ordinary_income: "ordinary_income",
  special_dividend: "ordinary_income",
  qualified_dividend: "qualified_dividend",
  qdi: "qualified_dividend",
};

export type ListRowStatus = "loading" | "upcoming" | "undisclosed" | "not_found";

export type ListRow = {
  ticker: string;
  fundName: string | null;
  family: string | null;
  found: boolean;
  status: ListRowStatus;
  nav: number | null;
  navAsOf: string | null;
  distPerShare: number | null;
  pctOfNav: number | null;
  estimateTypes: Record<ListEstimateType, number | null>;
  asOfDate: string | null;
  recordDate: string | null;
  exDate: string | null;
};

export function emptyEstimateTypes(): Record<ListEstimateType, number | null> {
  return {
    long_term_capital_gains: null,
    short_term_capital_gains: null,
    ordinary_income: null,
    qualified_dividend: null,
  };
}

export function emptyListRow(ticker: string, status: ListRowStatus = "loading"): ListRow {
  return {
    ticker,
    fundName: null,
    family: null,
    found: false,
    status,
    nav: null,
    navAsOf: null,
    distPerShare: null,
    pctOfNav: null,
    estimateTypes: emptyEstimateTypes(),
    asOfDate: null,
    recordDate: null,
    exDate: null,
  };
}

function num(value: string | number | null | undefined): number | null {
  if (value == null || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function midpoint(row: DataDistribution): number | null {
  const amount = num(row.amount);
  if (amount != null) return amount;
  const min = num(row.amount_min);
  const max = num(row.amount_max);
  if (min != null && max != null) return (min + max) / 2;
  return min ?? max;
}

function isRollupTotal(type: string | null | undefined): boolean {
  return (type ?? "").trim().toLowerCase() === "total";
}

function canonicalizeListEstimateType(
  raw: string | null | undefined,
): ListEstimateType | "skip" | "total_capital_gains" {
  const key = (raw ?? "").trim().toLowerCase().replace(/[\s-]+/g, "_");
  if (key === "total_capital_gains") return "total_capital_gains";
  return TYPE_ALIASES[key] ?? "skip";
}

function snapshotKey(row: DataDistribution): string {
  return [
    isoDate(row.as_of) ?? "",
    (row.publication_stage ?? "").trim().toLowerCase(),
    isoDate(row.ex_date) ?? "",
  ].join("|");
}

function snapshotRank(rows: DataDistribution[]): string {
  const asOf =
    rows
      .map((row) => isoDate(row.as_of))
      .filter((value): value is string => Boolean(value))
      .sort()
      .at(-1) ?? "0000-00-00";
  const event =
    rows
      .map((row) => isoDate(row.payable_date) ?? isoDate(row.ex_date) ?? isoDate(row.record_date))
      .filter((value): value is string => Boolean(value))
      .sort()
      .at(-1) ?? "";
  return `${asOf}|${event ? "1" : "0"}|${event}`;
}

function isUpcomingSnapshot(rows: DataDistribution[], today?: string): boolean {
  return rows.some(
    (row) =>
      distributionBucket(
        {
          asOfDate: isoDate(row.as_of),
          recordDate: isoDate(row.record_date),
          exDate: isoDate(row.ex_date),
          payableDate: isoDate(row.payable_date),
          publicationStage: row.publication_stage,
        },
        today,
      ) === "upcoming",
  );
}

function latestUpcomingSnapshot(
  rows: DataDistribution[],
  today?: string,
): DataDistribution[] {
  const bySnapshot = new Map<string, DataDistribution[]>();
  for (const row of rows) {
    const key = snapshotKey(row);
    const list = bySnapshot.get(key) ?? [];
    list.push(row);
    bySnapshot.set(key, list);
  }
  let best: DataDistribution[] | null = null;
  let bestRank = "";
  for (const snapshot of bySnapshot.values()) {
    if (!isUpcomingSnapshot(snapshot, today)) continue;
    const rank = snapshotRank(snapshot);
    if (!best || rank > bestRank) {
      best = snapshot;
      bestRank = rank;
    }
  }
  return best ?? [];
}

/**
 * Per-share estimate_type amounts from the latest unpaid announced snapshot.
 * Skips rollup `total`. percent_of_nav characters are not $ / share.
 * Published $0 stays 0; missing types stay null (never invent).
 */
export function upcomingEstimateTypeAmounts(
  rows: DataDistribution[],
  today?: string,
): Record<ListEstimateType, number | null> {
  const amounts = emptyEstimateTypes();
  const snapshot = latestUpcomingSnapshot(rows, today);
  if (!snapshot.length) return amounts;

  const hasTypedPerShare = snapshot.some(
    (row) =>
      row.amount_unit === "per_share" && !isRollupTotal(row.estimate_type),
  );
  let totalCapitalGains: number | null = null;

  for (const row of snapshot) {
    if (hasTypedPerShare && isRollupTotal(row.estimate_type)) continue;
    if ((row.amount_unit ?? "").trim().toLowerCase() !== "per_share") continue;
    const value = midpoint(row);
    if (value == null) continue;
    const kind = canonicalizeListEstimateType(row.estimate_type);
    if (kind === "skip") continue;
    if (kind === "total_capital_gains") {
      totalCapitalGains = (totalCapitalGains ?? 0) + value;
      continue;
    }
    amounts[kind] = (amounts[kind] ?? 0) + value;
  }

  if (
    totalCapitalGains != null &&
    amounts.long_term_capital_gains == null &&
    amounts.short_term_capital_gains == null
  ) {
    amounts.long_term_capital_gains = totalCapitalGains;
  }
  return amounts;
}

function snapshotField(
  rows: DataDistribution[],
  field: "as_of" | "record_date" | "ex_date" | "payable_date",
): string | null {
  const dates = rows
    .map((row) => isoDate(row[field]))
    .filter((value): value is string => Boolean(value))
    .sort();
  return dates.at(-1) ?? null;
}

function snapshotNav(rows: DataDistribution[]): number | null {
  for (const row of rows) {
    const nav = parsePositiveNav(row.nav_on_distribution_day);
    if (nav != null) return nav;
  }
  return null;
}

function snapshotStage(rows: DataDistribution[]): string | null {
  for (const row of rows) {
    const stage = (row.publication_stage ?? "").trim();
    if (stage) return stage;
  }
  return null;
}

function snapshotFundName(rows: DataDistribution[]): string | null {
  for (const row of rows) {
    const name = (row.fund_name ?? "").trim();
    if (name && name !== "—") return name;
  }
  return null;
}

function snapshotFamily(rows: DataDistribution[]): string | null {
  for (const row of rows) {
    const family = (row.fund_family ?? "").trim();
    if (family && family !== "—") return family;
  }
  return null;
}

function distTotalFromTypes(
  amounts: Record<ListEstimateType, number | null>,
): number | null {
  let sum = 0;
  let any = false;
  for (const type of LIST_ESTIMATE_TYPES) {
    const value = amounts[type];
    if (value == null) continue;
    any = true;
    sum += value;
  }
  return any ? sum : null;
}

/**
 * Unpaid /distributions snapshots win even when catalog identity is
 * `has_estimate: false` / paid (merge miss). Do not invent from paid/finals.
 */
function hasUpcomingEstimate(
  fund: FundEstimateView | null | undefined,
  distributionRows: DataDistribution[],
  today?: string,
): boolean {
  if (latestUpcomingSnapshot(distributionRows, today).length) {
    return true;
  }
  if (!fund) return false;
  return isUpcomingFund(fund, today) && !hideUpcomingAmounts(fund);
}

export function listRowFromFund(input: {
  ticker: string;
  fund?: FundEstimateView | null;
  distributionRows?: DataDistribution[];
  found?: boolean;
  today?: string;
}): ListRow {
  const ticker = input.ticker.trim().toUpperCase();
  const fund = input.fund ?? null;
  const distributionRows = input.distributionRows ?? [];
  const snapshot = latestUpcomingSnapshot(distributionRows, input.today);
  const found =
    input.found ??
    Boolean(
      snapshot.length ||
        (fund &&
          (fund.ticker === ticker || fund.nav > 0 || fund.fundName !== "—")),
    );
  if (!found && !fund && !snapshot.length) {
    return emptyListRow(ticker, "not_found");
  }
  if (!fund && !snapshot.length) {
    return emptyListRow(ticker, found ? "undisclosed" : "not_found");
  }

  const upcoming = hasUpcomingEstimate(fund, distributionRows, input.today);
  const estimateTypes = upcoming
    ? upcomingEstimateTypeAmounts(distributionRows, input.today)
    : emptyEstimateTypes();
  const distFromTypes = distTotalFromTypes(estimateTypes);
  const distFromFund =
    upcoming && fund && Number.isFinite(fund.estimatedDistributionAmount)
      ? fund.estimatedDistributionAmount
      : null;
  const distPerShare = upcoming
    ? distFromTypes ?? (distFromFund != null && distFromFund > 0 ? distFromFund : null)
    : null;
  const nav =
    (fund && fund.nav > 0 ? fund.nav : null) ?? snapshotNav(snapshot);
  const pctOfNav = upcoming
    ? resolvePctOfNav({
        publishedPctNav: fund?.publishedPctOfNav ?? null,
        perShare: distPerShare,
        weeklyNav: nav,
        navOnDistributionDay:
          fund?.navOnDistributionDay ?? snapshotNav(snapshot),
        publicationStage: fund?.publicationStage ?? snapshotStage(snapshot),
        exDate: snapshotField(snapshot, "ex_date") ?? fund?.exDate ?? null,
        payableDate:
          snapshotField(snapshot, "payable_date") ?? fund?.payableDate ?? null,
        today: input.today,
      })
    : null;
  const fundName =
    (fund?.fundName && fund.fundName !== "—" ? fund.fundName : null) ??
    snapshotFundName(snapshot);
  const family =
    (fund?.family && fund.family !== "—" ? fund.family : null) ??
    snapshotFamily(snapshot);

  return {
    ticker,
    fundName,
    family,
    found: true,
    status: upcoming ? "upcoming" : "undisclosed",
    nav,
    navAsOf: fund?.navAsOf ?? null,
    distPerShare,
    pctOfNav,
    estimateTypes,
    asOfDate: upcoming
      ? snapshotField(snapshot, "as_of") ?? isoDate(fund?.asOfDate)
      : null,
    recordDate: upcoming
      ? snapshotField(snapshot, "record_date") ?? isoDate(fund?.recordDate)
      : null,
    exDate: upcoming
      ? snapshotField(snapshot, "ex_date") ?? isoDate(fund?.exDate)
      : null,
  };
}

export function orderListRows(
  tickers: readonly string[],
  rows: Iterable<ListRow>,
): ListRow[] {
  const byTicker = new Map<string, ListRow>();
  for (const row of rows) {
    byTicker.set(row.ticker.toUpperCase(), row);
  }
  return tickers.map((ticker) => {
    const key = ticker.trim().toUpperCase();
    return byTicker.get(key) ?? emptyListRow(key, "not_found");
  });
}
