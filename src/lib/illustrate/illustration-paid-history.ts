import {
  chicagoTodayIso,
  isUpcomingFund,
  normalizePublicationStage,
} from "../../data/distribution-bucket.ts";
import { hideUpcomingAmounts, paidEventsForFund } from "../../data/hydrate-funds.ts";
import {
  currentPaidHistoryYear,
  illustrationPriorYearPaidEvents,
  paidHistoryYearOf,
  priorPaidHistoryYear,
} from "../../data/queries.ts";
import type { EstimateTypeLine, FundEstimate } from "../../data/types.ts";
import { pctOfNavForFund } from "./nav-math.ts";

export const ILLUSTRATION_PAID_LOOKBACK_YEARS = 5;

/** Data-named estimate_types the Paid History matrix and fund-card stack always list. */
export const PAID_HISTORY_ESTIMATE_TYPES = [
  "long_term_capital_gains",
  "short_term_capital_gains",
  "ordinary_income",
  "qualified_dividend",
  "special_dividend",
  "return_of_capital",
] as const;

export type PaidHistoryEstimateType = (typeof PAID_HISTORY_ESTIMATE_TYPES)[number];

export const PAID_HISTORY_TYPE_LABELS: Record<string, string> = {
  ordinary_income: "Ordinary",
  long_term_capital_gains: "LTCG",
  short_term_capital_gains: "STCG",
  qualified_dividend: "QDI",
  total_capital_gains: "Total capital gains",
  special_dividend: "Special",
  return_of_capital: "ROC",
};

export const FUND_CARD_TYPE_LABELS: Record<string, string> = {
  ordinary_income: "Ordinary income",
  long_term_capital_gains: "Long-term capital gains",
  short_term_capital_gains: "Short-term capital gains",
  qualified_dividend: "Qualified dividends",
  total_capital_gains: "Total capital gains",
  special_dividend: "Special dividend",
  return_of_capital: "Return of capital",
};

export function isRollupEstimateType(type: string | null | undefined): boolean {
  return (type ?? "").trim().toLowerCase() === "total";
}

export function paidHistoryTypeLabel(estimateType: string): string {
  return PAID_HISTORY_TYPE_LABELS[estimateType] ?? estimateType;
}

export function fundCardTypeLabel(estimateType: string): string {
  return FUND_CARD_TYPE_LABELS[estimateType] ?? estimateType;
}

/** Canonical rows first; extra Data-published types append. Never invent amounts. */
export function orderedPaidHistoryTypes(extra: Iterable<string> = []): string[] {
  const seen = new Set<string>(PAID_HISTORY_ESTIMATE_TYPES);
  const extras: string[] = [];
  for (const raw of extra) {
    const type = raw.trim();
    if (!type || isRollupEstimateType(type) || seen.has(type)) continue;
    seen.add(type);
    extras.push(type);
  }
  extras.sort((a, b) => a.localeCompare(b));
  return [...PAID_HISTORY_ESTIMATE_TYPES, ...extras];
}

export type IllustrationPaidTypeRow = {
  key: string;
  estimateType: string;
  perShare: number | null;
  pctOfNav: number | null;
  asOfDate: string | null;
  recordDate: string | null;
  exDate: string | null;
  stage: string | null;
};

/**
 * Prior-calendar-year finals/paid only, broken into published estimate_types.
 * Published $0 stays. Missing amounts stay null → UI "—".
 */
export function illustrationPaidTypeRows(
  fund: Parameters<typeof illustrationPriorYearPaidEvents>[0],
  now = new Date(),
): IllustrationPaidTypeRow[] {
  const rows: IllustrationPaidTypeRow[] = [];
  for (const event of illustrationPriorYearPaidEvents(fund, now)) {
    const lines = (event.estimateTypeLines ?? []).filter(
      (line) => !isRollupEstimateType(line.estimateType),
    );
    if (lines.length) {
      for (const line of lines) {
        const publishedPct =
          line.amountUnit === "percent_of_nav" ? line.amount : null;
        rows.push({
          key: `${event.asOfDate}:${event.exDate ?? ""}:${line.estimateType}:${line.amountUnit}`,
          estimateType: line.estimateType,
          perShare: line.amountUnit === "per_share" ? line.amount : null,
          pctOfNav:
            publishedPct ??
            pctOfNavForFund({
              estimatedDistributionAmount: line.amount,
              publishedPctOfNav: null,
              estimatedDistributionPctNav: null,
              navOnDistributionDay: event.navOnDistributionDay,
              publicationStage: event.publicationStage,
              exDate: event.exDate,
              payableDate: event.payableDate,
            }),
          asOfDate: event.asOfDate,
          recordDate: event.recordDate,
          exDate: event.exDate,
          stage: event.publicationStage,
        });
      }
      continue;
    }
    rows.push({
      key: `${event.asOfDate}:${event.exDate ?? ""}:event`,
      estimateType: "",
      perShare: event.estimatedDistributionAmount,
      pctOfNav: pctOfNavForFund(event),
      asOfDate: event.asOfDate,
      recordDate: event.recordDate,
      exDate: event.exDate,
      stage: event.publicationStage,
    });
  }
  return rows;
}

export function illustrationPaidHistoryYear(now = new Date()): number {
  return priorPaidHistoryYear(now);
}

/**
 * Last 5 completed Chicago calendar years plus the current year.
 * In 2026: 2021–2026. Current year is Awaiting / — until an unpaid
 * announced estimate arrives — never invent from prior-year history.
 */
export function illustrationPaidHistoryYears(now = new Date()): number[] {
  const current = currentPaidHistoryYear(now);
  const end = priorPaidHistoryYear(now);
  const completed = Array.from(
    { length: ILLUSTRATION_PAID_LOOKBACK_YEARS },
    (_, index) => end - (ILLUSTRATION_PAID_LOOKBACK_YEARS - 1 - index),
  );
  return [...completed, current];
}

export type IllustrationPaidMatrixCell = {
  perShare: number | null;
  pctOfNav: number | null;
  amountUnit: string | null;
  awaiting: boolean;
};

export type IllustrationPaidMatrixRow = {
  estimateType: string;
  cells: Record<number, IllustrationPaidMatrixCell>;
};

export type IllustrationPaidHistoryMatrix = {
  years: number[];
  rows: IllustrationPaidMatrixRow[];
  awaitingYears: number[];
};

export type IllustrationFundCardTypeRow = {
  estimateType: string;
  label: string;
  perShare: number | null;
  pctOfNav: number | null;
  amountUnit: string | null;
  awaiting: boolean;
};

type PaidMatrixFund = Parameters<typeof paidEventsForFund>[0] &
  Partial<
    Pick<
      FundEstimate,
      | "hasEstimate"
      | "asOfDate"
      | "recordDate"
      | "exDate"
      | "payableDate"
      | "publicationStage"
      | "estimatedDistributionAmount"
      | "estimatedDistributionPctNav"
      | "estimatedOrdinaryIncome"
      | "estimatedCapitalGains"
      | "estimateTypeLines"
    >
  >;

function lookbackPaidEvents(
  fund: Parameters<typeof paidEventsForFund>[0],
  now = new Date(),
): ReturnType<typeof paidEventsForFund> {
  const years = new Set(illustrationPaidHistoryYears(now));
  return paidEventsForFund(fund).filter((event) => {
    const stage = normalizePublicationStage(event.publicationStage);
    if (stage !== "final" && stage !== "paid") return false;
    return years.has(paidHistoryYearOf(event));
  });
}

function emptyCell(awaiting = false): IllustrationPaidMatrixCell {
  return { perShare: null, pctOfNav: null, amountUnit: null, awaiting };
}

function addLineToCell(
  cell: IllustrationPaidMatrixCell,
  line: { estimateType: string; amount: number; amountUnit: string },
  event: Parameters<typeof pctOfNavForFund>[0],
): IllustrationPaidMatrixCell {
  const next = { ...cell, awaiting: false };
  if (line.amountUnit === "per_share") {
    next.perShare = (next.perShare ?? 0) + line.amount;
    next.amountUnit = "per_share";
    if (next.pctOfNav == null) {
      next.pctOfNav = pctOfNavForFund({
        estimatedDistributionAmount: line.amount,
        publishedPctOfNav: null,
        estimatedDistributionPctNav: null,
        navOnDistributionDay: event.navOnDistributionDay,
        publicationStage: event.publicationStage,
        exDate: event.exDate,
        payableDate: event.payableDate,
      });
    }
  } else if (line.amountUnit === "percent_of_nav") {
    next.pctOfNav = (next.pctOfNav ?? 0) + line.amount;
    if (!next.amountUnit) next.amountUnit = "percent_of_nav";
  }
  return next;
}

/** Same year×type×ex republish (newer as_of) replaces; different ex-dates still add. */
function snapshotSlotKey(
  year: number,
  estimateType: string,
  exDate: string | null,
): string {
  return `${year}|${estimateType}|${exDate ?? ""}`;
}

function mergeCells(
  current: IllustrationPaidMatrixCell,
  incoming: IllustrationPaidMatrixCell,
): IllustrationPaidMatrixCell {
  return {
    perShare:
      current.perShare == null && incoming.perShare == null
        ? null
        : (current.perShare ?? 0) + (incoming.perShare ?? 0),
    pctOfNav:
      current.pctOfNav == null && incoming.pctOfNav == null
        ? null
        : (current.pctOfNav ?? 0) + (incoming.pctOfNav ?? 0),
    amountUnit: current.amountUnit ?? incoming.amountUnit,
    awaiting: false,
  };
}

function cellHasPublishedAmount(cell: IllustrationPaidMatrixCell | undefined): boolean {
  if (!cell) return false;
  return cell.perShare != null || cell.pctOfNav != null;
}

/**
 * Unpaid announced estimate for the current Chicago year.
 * Paid / final history never counts — that stays in the matrix, not Upcoming.
 */
export function hasCurrentYearUnpaidEstimate(
  fund: PaidMatrixFund,
  now = new Date(),
): boolean {
  return isUpcomingFund(
    {
      bucket: fund.bucket,
      hasEstimate: fund.hasEstimate,
      asOfDate: fund.asOfDate,
      recordDate: fund.recordDate,
      exDate: fund.exDate,
      payableDate: fund.payableDate,
      publicationStage: fund.publicationStage,
      estimatedDistributionAmount: fund.estimatedDistributionAmount,
      estimatedDistributionPctNav: fund.estimatedDistributionPctNav,
      estimatedOrdinaryIncome: fund.estimatedOrdinaryIncome,
      estimatedCapitalGains: fund.estimatedCapitalGains,
    },
    chicagoTodayIso(now),
  );
}

function upcomingTypeLines(fund: PaidMatrixFund): EstimateTypeLine[] {
  if (!hasCurrentYearUnpaidEstimate(fund)) return [];
  if (hideUpcomingAmounts(fund)) return [];
  return (fund.estimateTypeLines ?? []).filter(
    (line) => !isRollupEstimateType(line.estimateType),
  );
}

/**
 * Fund-header stack: every canonical estimate_type, plus extras Data published
 * on the unpaid snapshot. Awaiting → amounts stay null (UI "—"). Published $0
 * stays. Never invent. Never copy paid / finals onto the card.
 */
export function illustrationFundCardTypeRows(
  fund: PaidMatrixFund,
  now = new Date(),
): IllustrationFundCardTypeRow[] {
  const lines = upcomingTypeLines(fund);
  const awaiting = lines.length === 0 && !hasCurrentYearUnpaidEstimate(fund);
  const byType = new Map<string, EstimateTypeLine>();
  for (const line of lines) {
    if (!byType.has(line.estimateType)) byType.set(line.estimateType, line);
  }
  return orderedPaidHistoryTypes(byType.keys()).map((estimateType) => {
    const line = byType.get(estimateType);
    return {
      estimateType,
      label: fundCardTypeLabel(estimateType),
      perShare: line?.amountUnit === "per_share" ? line.amount : null,
      pctOfNav: line?.amountUnit === "percent_of_nav" ? line.amount : null,
      amountUnit: line?.amountUnit ?? null,
      awaiting,
    };
  });
}

/**
 * Calendar-year Paid History matrix. Rows are the full estimate_type set
 * (LTCG / STCG / Ordinary / QDI / Special / ROC + any other published types).
 * Current year with no unpaid announced estimate is Awaiting — never invent
 * from prior-year history. Unpaid prelims never enter Paid History cells.
 * Published $0 stays; missing stays null → UI "—".
 */
export function illustrationPaidHistoryMatrix(
  fund: PaidMatrixFund,
  now = new Date(),
): IllustrationPaidHistoryMatrix {
  const years = illustrationPaidHistoryYears(now);
  const currentYear = currentPaidHistoryYear(now);
  const awaitingCurrent = !hasCurrentYearUnpaidEstimate(fund, now);
  const slots = new Map<
    string,
    { asOf: string; estimateType: string; year: number; cell: IllustrationPaidMatrixCell }
  >();

  for (const event of lookbackPaidEvents(fund, now)) {
    const year = paidHistoryYearOf(event);
    const asOf = event.asOfDate ?? "";
    const lines = (event.estimateTypeLines ?? []).filter(
      (line) => !isRollupEstimateType(line.estimateType),
    );
    const typed = lines.length
      ? lines
      : [
          {
            estimateType: "",
            amount: event.estimatedDistributionAmount,
            amountUnit: "per_share",
          },
        ];
    for (const line of typed) {
      const key = snapshotSlotKey(year, line.estimateType, event.exDate);
      const existing = slots.get(key);
      if (existing && existing.asOf > asOf) continue;
      const base =
        existing && existing.asOf === asOf ? existing.cell : emptyCell();
      slots.set(key, {
        asOf,
        estimateType: line.estimateType,
        year,
        cell: addLineToCell(base, line, event),
      });
    }
  }

  const byType = new Map<string, Record<number, IllustrationPaidMatrixCell>>();
  for (const slot of slots.values()) {
    const cells = byType.get(slot.estimateType) ?? {};
    const current = cells[slot.year] ?? emptyCell();
    cells[slot.year] = mergeCells(current, slot.cell);
    byType.set(slot.estimateType, cells);
  }

  const types = orderedPaidHistoryTypes(byType.keys());
  const currentHasPaid = [...byType.values()].some((cells) =>
    cellHasPublishedAmount(cells[currentYear]),
  );
  const awaitingYear =
    awaitingCurrent && !currentHasPaid ? currentYear : null;

  return {
    years,
    awaitingYears: awaitingYear == null ? [] : [awaitingYear],
    rows: types.map((estimateType) => {
      const published = byType.get(estimateType) ?? {};
      const cells: Record<number, IllustrationPaidMatrixCell> = {};
      for (const year of years) {
        const found = published[year];
        if (cellHasPublishedAmount(found)) {
          cells[year] = { ...found, awaiting: false };
          continue;
        }
        cells[year] = emptyCell(year === awaitingYear);
      }
      return { estimateType, cells };
    }),
  };
}
