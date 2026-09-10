import { normalizePublicationStage } from "../../data/distribution-bucket.ts";
import { paidEventsForFund } from "../../data/hydrate-funds.ts";
import {
  illustrationPriorYearPaidEvents,
  paidHistoryYearOf,
  priorPaidHistoryYear,
} from "../../data/queries.ts";
import { pctOfNavForFund } from "./nav-math.ts";

export const ILLUSTRATION_PAID_LOOKBACK_YEARS = 5;

const TYPE_ORDER = [
  "long_term_capital_gains",
  "short_term_capital_gains",
  "ordinary_income",
  "qualified_dividend",
];

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
 * Published $0 stays. Missing amounts stay null → UI "—". Never invent types.
 */
export function illustrationPaidTypeRows(
  fund: Parameters<typeof illustrationPriorYearPaidEvents>[0],
  now = new Date(),
): IllustrationPaidTypeRow[] {
  const rows: IllustrationPaidTypeRow[] = [];
  for (const event of illustrationPriorYearPaidEvents(fund, now)) {
    const lines = (event.estimateTypeLines ?? []).filter(
      (line) => line.estimateType !== "total",
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

/** Last 5 completed Chicago calendar years, oldest first. In 2026: 2021–2025. */
export function illustrationPaidHistoryYears(now = new Date()): number[] {
  const end = priorPaidHistoryYear(now);
  return Array.from(
    { length: ILLUSTRATION_PAID_LOOKBACK_YEARS },
    (_, index) => end - (ILLUSTRATION_PAID_LOOKBACK_YEARS - 1 - index),
  );
}

export type IllustrationPaidMatrixCell = {
  perShare: number | null;
  pctOfNav: number | null;
  amountUnit: string | null;
};

export type IllustrationPaidMatrixRow = {
  estimateType: string;
  cells: Record<number, IllustrationPaidMatrixCell>;
};

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

function emptyCell(): IllustrationPaidMatrixCell {
  return { perShare: null, pctOfNav: null, amountUnit: null };
}

function addLineToCell(
  cell: IllustrationPaidMatrixCell,
  line: { estimateType: string; amount: number; amountUnit: string },
  event: Parameters<typeof pctOfNavForFund>[0],
): IllustrationPaidMatrixCell {
  const next = { ...cell };
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

/**
 * 5-year Paid History matrix. Rows are published estimate_types only —
 * never invent Ordinary / QDI. Cells stay null → UI "—"; published $0 stays.
 */
export function illustrationPaidHistoryMatrix(
  fund: Parameters<typeof paidEventsForFund>[0],
  now = new Date(),
): { years: number[]; rows: IllustrationPaidMatrixRow[] } {
  const years = illustrationPaidHistoryYears(now);
  const byType = new Map<string, Record<number, IllustrationPaidMatrixCell>>();

  for (const event of lookbackPaidEvents(fund, now)) {
    const year = paidHistoryYearOf(event);
    const lines = (event.estimateTypeLines ?? []).filter(
      (line) => line.estimateType !== "total",
    );
    if (lines.length) {
      for (const line of lines) {
        const cells = byType.get(line.estimateType) ?? {};
        cells[year] = addLineToCell(cells[year] ?? emptyCell(), line, event);
        byType.set(line.estimateType, cells);
      }
      continue;
    }
    const cells = byType.get("") ?? {};
    const existing = cells[year] ?? emptyCell();
    cells[year] = {
      perShare: (existing.perShare ?? 0) + event.estimatedDistributionAmount,
      pctOfNav: existing.pctOfNav ?? pctOfNavForFund(event),
      amountUnit: existing.amountUnit ?? "per_share",
    };
    byType.set("", cells);
  }

  const types = [...byType.keys()].sort((a, b) => {
    const ai = TYPE_ORDER.indexOf(a);
    const bi = TYPE_ORDER.indexOf(b);
    if (ai === -1 && bi === -1) return a.localeCompare(b);
    if (ai === -1) return 1;
    if (bi === -1) return -1;
    return ai - bi;
  });

  return {
    years,
    rows: types.map((estimateType) => {
      const published = byType.get(estimateType) ?? {};
      const cells: Record<number, IllustrationPaidMatrixCell> = {};
      for (const year of years) {
        cells[year] = published[year] ?? emptyCell();
      }
      return { estimateType, cells };
    }),
  };
}
