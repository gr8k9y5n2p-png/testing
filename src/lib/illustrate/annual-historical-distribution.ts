import { isUpcomingFund } from "../../data/distribution-bucket.ts";
import { paidEventsForFund } from "../../data/hydrate-funds.ts";
import type { FundEstimate } from "../../data/types.ts";
import type { YoYTaxChartPoint } from "./yoy-tax-chart.ts";

export type AnnualHistoricalFund = Pick<
  FundEstimate,
  | "hasEstimate"
  | "bucket"
  | "estimatedDistributionAmount"
  | "estimatedOrdinaryIncome"
  | "estimatedCapitalGains"
  | "estimatedDistributionPctNav"
  | "asOfDate"
  | "recordDate"
  | "exDate"
  | "payableDate"
  | "publicationStage"
  | "distributionYear"
  | "paidHistory"
>;

export type AnnualHistoricalBar = YoYTaxChartPoint & {
  tone: "paid" | "estimate";
  value: number;
};

function yearOf(event: { distributionYear: number; asOfDate?: string | null }): number {
  if (Number.isFinite(event.distributionYear) && event.distributionYear > 0) {
    return event.distributionYear;
  }
  const asOfYear = Number((event.asOfDate ?? "").slice(0, 4));
  return Number.isFinite(asOfYear) && asOfYear > 0 ? asOfYear : 0;
}

/**
 * One bar per distribution year from live `GET /distributions`.
 *
 * Green (`paid`) = past / paid / final only. Red (`estimate`) = unpaid
 * preliminary_estimate / updated_estimate (`isUpcomingFund`) for that year.
 * `has_estimate: false` and paid/final YE never invent a red bar.
 */
export function annualHistoricalDistributionBars(
  fund?: AnnualHistoricalFund | null,
): AnnualHistoricalBar[] {
  if (!fund) return [];

  const paidByYear = new Map<number, number>();
  for (const event of paidEventsForFund(fund)) {
    const year = yearOf(event);
    const amount = event.estimatedDistributionAmount;
    if (year <= 0 || !(amount > 0)) continue;
    paidByYear.set(year, (paidByYear.get(year) ?? 0) + amount);
  }

  const estimateYear = yearOf(fund);
  const estimateAmount = fund.estimatedDistributionAmount;
  const showEstimate =
    isUpcomingFund(fund) && estimateYear > 0 && estimateAmount > 0;

  if (showEstimate) paidByYear.delete(estimateYear);

  const bars: AnnualHistoricalBar[] = [...paidByYear.entries()]
    .filter(([, value]) => value > 0)
    .map(([year, value]) => ({
      year,
      value,
      tone: "paid" as const,
    }));

  if (showEstimate) {
    bars.push({
      year: estimateYear,
      value: estimateAmount,
      tone: "estimate",
    });
  }

  return bars.sort((a, b) => a.year - b.year);
}

export function formatAnnualHistoricalBar(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 4,
    maximumFractionDigits: 4,
  }).format(value);
}
