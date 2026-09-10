import {
  illustrationPriorYearPaidEvents,
  priorPaidHistoryYear,
} from "../../data/queries.ts";
import { pctOfNavForFund } from "./nav-math.ts";

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
