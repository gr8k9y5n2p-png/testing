import { parsePositiveNav } from "../lib/illustrate/nav-math.ts";
import {
  distributionBucket,
  isoDate,
  toPaidEvent,
} from "./distribution-bucket.ts";
import type { PaidDistributionEvent } from "./distribution-bucket.ts";
import type { EstimateTypeLine, FundEstimate } from "./types.ts";

export type DataDistribution = {
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
  record_date?: string | null;
  ex_date?: string | null;
  payable_date?: string | null;
  as_of: string | null;
  publication_stage: string | null;
  nav_on_distribution_day?: string | number | null;
  nav_on_distribution_day_as_of?: string | null;
  nav_on_distribution_day_source?: string | null;
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

type SnapshotTotals = {
  rows: DataDistribution[];
  asOf: string | null;
  recordDate: string | null;
  exDate: string | null;
  payableDate: string | null;
  publicationStage: string | null;
  pctNav: number;
  perShare: number;
  ordinary: number;
  capGains: number;
  publishedPct: number | null;
  navOnDistributionDay: number | null;
  navOnDistributionDayAsOf: string | null;
  navOnDistributionDaySource: string | null;
};

function snapshotKey(row: DataDistribution): string {
  return [
    isoDate(row.as_of) ?? "",
    (row.publication_stage ?? "").trim().toLowerCase(),
    isoDate(row.ex_date) ?? "",
  ].join("|");
}

function pickDate(
  rows: DataDistribution[],
  field: "as_of" | "record_date" | "ex_date" | "payable_date",
): string | null {
  const dates = rows
    .map((row) => isoDate(row[field]))
    .filter((value): value is string => Boolean(value));
  if (!dates.length) return null;
  return dates.sort().at(-1) ?? null;
}

function pickNavOnDistributionDay(rows: DataDistribution[]): {
  nav: number | null;
  asOf: string | null;
  source: string | null;
} {
  for (const row of rows) {
    const nav = parsePositiveNav(row.nav_on_distribution_day);
    if (nav == null) continue;
    return {
      nav,
      asOf: isoDate(row.nav_on_distribution_day_as_of),
      source: row.nav_on_distribution_day_source ?? null,
    };
  }
  return { nav: null, asOf: null, source: null };
}

function isRollupTotal(type: string | null | undefined): boolean {
  return (type ?? "").trim().toLowerCase() === "total";
}

function estimateTypeLinesFromRows(rows: DataDistribution[]): EstimateTypeLine[] {
  const lines: EstimateTypeLine[] = [];
  const seen = new Set<string>();
  for (const row of rows) {
    const estimateType = (row.estimate_type ?? "").trim();
    if (!estimateType || isRollupTotal(estimateType)) continue;
    const key = `${estimateType}|${row.amount_unit}`;
    if (seen.has(key)) continue;
    seen.add(key);
    lines.push({
      estimateType,
      amount: midpoint(row),
      amountUnit: row.amount_unit,
    });
  }
  return lines;
}

function summarizeSnapshot(rows: DataDistribution[]): SnapshotTotals {
  let pctNav = 0;
  let publishedPctChars = 0;
  let perShare = 0;
  let ordinary = 0;
  let capGains = 0;
  const hasTypedPerShare = rows.some(
    (row) => row.amount_unit === "per_share" && !isRollupTotal(row.estimate_type),
  );
  for (const row of rows) {
    if (hasTypedPerShare && isRollupTotal(row.estimate_type)) continue;
    const value = midpoint(row);
    if (row.amount_unit === "percent_of_nav") {
      pctNav += value;
      publishedPctChars += 1;
      if (CG_TYPES.has(row.estimate_type)) capGains += value;
      else ordinary += value;
    } else if (row.amount_unit === "per_share") {
      perShare += value;
      if (CG_TYPES.has(row.estimate_type)) capGains += value;
      else ordinary += value;
    }
  }
  const dayNav = pickNavOnDistributionDay(rows);
  return {
    rows,
    asOf: pickDate(rows, "as_of"),
    recordDate: pickDate(rows, "record_date"),
    exDate: pickDate(rows, "ex_date"),
    payableDate: pickDate(rows, "payable_date"),
    publicationStage: rows.find((row) => row.publication_stage)?.publication_stage ?? null,
    pctNav,
    perShare,
    ordinary,
    capGains,
    publishedPct: publishedPctChars > 0 ? pctNav : null,
    navOnDistributionDay: dayNav.nav,
    navOnDistributionDayAsOf: dayNav.asOf,
    navOnDistributionDaySource: dayNav.source,
  };
}

function snapshotRank(snapshot: SnapshotTotals): string {
  const asOf = snapshot.asOf ?? "0000-00-00";
  const event =
    snapshot.payableDate ?? snapshot.exDate ?? snapshot.recordDate ?? "";
  // Undated as_of-only rows (QD %, specials) must not outrank a dated YE event
  // on the same as_of — string `|` otherwise sorts above `2` in 2025-12-15.
  const hasEvent = event ? "1" : "0";
  return `${asOf}|${hasEvent}|${event}`;
}

function pickLatest(snapshots: SnapshotTotals[]): SnapshotTotals | null {
  if (!snapshots.length) return null;
  return snapshots.reduce((best, row) =>
    snapshotRank(row) > snapshotRank(best) ? row : best,
  );
}

function toFundEstimate(
  key: string,
  latest: DataDistribution,
  snapshot: SnapshotTotals,
  paidHistory: PaidDistributionEvent[],
  today?: string,
): FundEstimate {
  const asOf = snapshot.asOf ?? new Date().toISOString().slice(0, 10);
  const year = Number(asOf.slice(0, 4)) || new Date().getUTCFullYear();
  const dates = {
    asOfDate: asOf,
    recordDate: snapshot.recordDate,
    exDate: snapshot.exDate,
    payableDate: snapshot.payableDate,
    publicationStage: snapshot.publicationStage,
  };
  return {
    id: `api:${key}`,
    fundName: latest.fund_name,
    ticker: (latest.ticker || latest.fund_identifier || key).toUpperCase(),
    cusip: latest.cusip ?? "",
    family: latest.fund_family,
    category: "—",
    shareClass: latest.share_class ?? "",
    nav: 0,
    navOnDistributionDay: snapshot.navOnDistributionDay,
    navOnDistributionDayAsOf: snapshot.navOnDistributionDayAsOf,
    navOnDistributionDaySource: snapshot.navOnDistributionDaySource,
    publishedPctOfNav: snapshot.publishedPct,
    estimateTypeLines: estimateTypeLinesFromRows(snapshot.rows),
    estimatedDistributionAmount: snapshot.perShare,
    estimatedOrdinaryIncome: snapshot.ordinary,
    estimatedCapitalGains: snapshot.capGains,
    estimatedDistributionPctNav: snapshot.pctNav,
    publishedAt: asOf,
    asOfDate: asOf,
    recordDate: snapshot.recordDate,
    exDate: snapshot.exDate,
    payableDate: snapshot.payableDate,
    publicationStage: snapshot.publicationStage,
    bucket: distributionBucket(dates, today),
    paidHistory,
    distributionYear: year,
  };
}

export function aggregateDistributions(
  items: DataDistribution[],
  today?: string,
): FundEstimate[] {
  const grouped = new Map<string, DataDistribution[]>();
  for (const item of items) {
    const key = fundKey(item);
    const list = grouped.get(key) ?? [];
    list.push(item);
    grouped.set(key, list);
  }

  const funds: FundEstimate[] = [];
  for (const [key, rows] of grouped) {
    const bySnapshot = new Map<string, DataDistribution[]>();
    for (const row of rows) {
      const snapKey = snapshotKey(row);
      const list = bySnapshot.get(snapKey) ?? [];
      list.push(row);
      bySnapshot.set(snapKey, list);
    }

    const snapshots = [...bySnapshot.values()].map(summarizeSnapshot);
    const upcoming = snapshots.filter(
      (snapshot) =>
        distributionBucket(
          {
            asOfDate: snapshot.asOf,
            recordDate: snapshot.recordDate,
            exDate: snapshot.exDate,
            payableDate: snapshot.payableDate,
            publicationStage: snapshot.publicationStage,
          },
          today,
        ) === "upcoming",
    );
    const paid = snapshots.filter(
      (snapshot) =>
        distributionBucket(
          {
            asOfDate: snapshot.asOf,
            recordDate: snapshot.recordDate,
            exDate: snapshot.exDate,
            payableDate: snapshot.payableDate,
            publicationStage: snapshot.publicationStage,
          },
          today,
        ) === "paid",
    );

    const display = pickLatest(upcoming) ?? pickLatest(paid) ?? snapshots[0];
    if (!display) continue;

    const paidHistory = paid
      .filter((snapshot) => snapshot !== display)
      .sort((a, b) => snapshotRank(b).localeCompare(snapshotRank(a)))
      .map((snapshot) =>
        toPaidEvent({
          asOfDate: snapshot.asOf ?? display.asOf ?? new Date().toISOString().slice(0, 10),
          recordDate: snapshot.recordDate,
          exDate: snapshot.exDate,
          payableDate: snapshot.payableDate,
          publicationStage: snapshot.publicationStage,
          estimatedDistributionAmount: snapshot.perShare,
          estimatedOrdinaryIncome: snapshot.ordinary,
          estimatedCapitalGains: snapshot.capGains,
          estimatedDistributionPctNav: snapshot.pctNav,
          publishedPctOfNav: snapshot.publishedPct,
          navOnDistributionDay: snapshot.navOnDistributionDay,
          navOnDistributionDayAsOf: snapshot.navOnDistributionDayAsOf,
          navOnDistributionDaySource: snapshot.navOnDistributionDaySource,
          distributionYear:
            Number((snapshot.asOf ?? snapshot.exDate ?? "").slice(0, 4)) ||
            new Date().getUTCFullYear(),
        }),
      );

    funds.push(toFundEstimate(key, display.rows[0], display, paidHistory, today));
  }
  return funds;
}
