import { formatUsd } from "@/lib/format";
import type {
  PortfolioAllocationOut,
  PortfolioHoldingOut,
} from "@/lib/illustrate/portfolio-compare-types";
import { upcomingFromHolding } from "@/lib/illustrate/publication-stage";

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
  paidHistoryRowsForSide,
  publicationBucket,
  totalUpcomingTax,
  upcomingFromHolding,
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

function num(value: unknown): number | null {
  if (value == null || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export type TaxImpactBar = {
  ticker: string;
  fundName: string;
  taxDollars: number;
  color: string;
  /** 0–1 vs the largest tax in this book. */
  share: number;
};

/** Distinct, Ledger-adjacent fills. Same ticker hashes to the same preferred slot. */
const TICKER_PALETTE = [
  "#1a4d3a",
  "#3d5a80",
  "#b4532a",
  "#6b5348",
  "#2a6f6f",
  "#8b6914",
  "#4a5568",
  "#7c3a2d",
  "#0f7a4b",
  "#5c6b5e",
  "#1a1d1a",
  "#8a4f6b",
] as const;

export function colorForTicker(ticker: string, used = new Set<string>()): string {
  const key = ticker.trim().toUpperCase();
  let hash = 0;
  for (let i = 0; i < key.length; i += 1) {
    hash = (hash * 33 + key.charCodeAt(i)) >>> 0;
  }
  for (let offset = 0; offset < TICKER_PALETTE.length; offset += 1) {
    const color = TICKER_PALETTE[(hash + offset) % TICKER_PALETTE.length];
    if (!used.has(color)) {
      used.add(color);
      return color;
    }
  }
  return TICKER_PALETTE[hash % TICKER_PALETTE.length];
}

function taxImpactDollars(holding: PortfolioHoldingOut): number {
  return num(upcomingFromHolding(holding)?.estimated_tax) ?? 0;
}

/** One bar per holding; scale is relative to peers in this allocation only. */
export function taxImpactBarsForSide(allocation: PortfolioAllocationOut): TaxImpactBar[] {
  const used = new Set<string>();
  const items = allocation.holdings
    .map((holding) => {
      const ticker = (holding.ticker || holding.fund_identifier || "").trim().toUpperCase();
      if (!ticker) return null;
      return {
        ticker,
        fundName: holding.fund_name || ticker,
        taxDollars: taxImpactDollars(holding),
        color: colorForTicker(ticker, used),
      };
    })
    .filter((item): item is NonNullable<typeof item> => item != null);

  const max = items.reduce((peak, item) => Math.max(peak, item.taxDollars), 0);
  return items.map((item) => ({
    ...item,
    share: max > 0 ? item.taxDollars / max : 0,
  }));
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
