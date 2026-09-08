import { formatUsd } from "@/lib/format";
import type { PortfolioAllocationOut } from "@/lib/illustrate/portfolio-compare-types";

export {
  upcomingDistributionLine,
  upcomingEstimatedTaxLine,
} from "@/lib/illustrate/portfolio-compare-copy";

export type { DistributionBucket, UpcomingRow } from "@/lib/illustrate/publication-stage";
export {
  announcedDateOf,
  distributionHasPayable,
  eventDateOf,
  formatAsOfStage,
  formatStageLabel,
  isPaidHistoryPublicationStage,
  isUpcomingPublicationStage,
  normalizePublicationStage,
  PAID_HISTORY_CAP,
  paidHistoryDateOf,
  paidHistoryRowsForSide,
  publicationBucket,
  totalUpcomingTax,
  upcomingFromHolding,
  upcomingHoldingsForSide,
  upcomingRowsForSide,
  utcToday,
} from "@/lib/illustrate/publication-stage";

export type TaxPolarity = "more" | "less" | "even";

const EVEN_DOLLARS = 0.5;

export function polarityFromProposedMinusCurrent(
  delta: number,
  evenThreshold = EVEN_DOLLARS,
): TaxPolarity {
  if (Math.abs(delta) <= evenThreshold) return "even";
  return delta > 0 ? "more" : "less";
}

export function formatTaxDragPct(rate: number): string {
  return `${(rate * 100).toFixed(2)}%`;
}

export function formatMoreLessTax(delta: number): {
  headline: string;
  polarity: TaxPolarity;
} {
  const polarity = polarityFromProposedMinusCurrent(delta);
  if (polarity === "even") {
    return { headline: "About even tax", polarity };
  }
  const dollars = formatUsd(Math.abs(Math.round(delta)), 0);
  return { headline: `${dollars} ${polarity} tax`, polarity };
}

export function heatBackground(heat: number): string {
  if (heat >= 0.85) return "bg-[#e8a598] text-[#6b1d16]";
  if (heat >= 0.65) return "bg-[#f0c49a] text-[#6b3a12]";
  if (heat >= 0.4) return "bg-[#f3e3a3] text-[#5c4d12]";
  if (heat >= 0.2) return "bg-[#d7e6f0] text-[#3d4f5c]";
  return "bg-[#eef4f8] text-[#5c6b5e]";
}

export function compactBookLabel(bookDollars: number): string {
  if (bookDollars >= 1_000_000 && Math.abs(bookDollars / 1_000_000 - Math.round(bookDollars / 1_000_000)) < 0.05) {
    const millions = bookDollars / 1_000_000;
    const label = Number.isInteger(millions) ? String(millions) : millions.toFixed(1);
    return `$${label}M`;
  }
  return formatUsd(bookDollars, 0);
}

export function allocationBook(allocation: PortfolioAllocationOut, fallback: number): number {
  return allocation.coverage.dollars_total > 0
    ? allocation.coverage.dollars_total
    : fallback;
}
