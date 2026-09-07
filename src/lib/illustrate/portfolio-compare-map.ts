import { formatUsd } from "@/lib/format";
import type {
  PortfolioAllocationOut,
  PortfolioHoldingOut,
  PortfolioUpcoming,
} from "@/lib/illustrate/portfolio-compare-types";

export type TaxPolarity = "more" | "less" | "even";

export type UpcomingRow = {
  key: string;
  ticker: string;
  fundName: string;
  side: "current" | "proposed";
  sideLabel: string;
  distributionDollars: number;
  estimatedTax: number | null;
  asOf: string | null;
  stage: string | null;
  heat: number;
};

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

export function upcomingFromHolding(holding: PortfolioHoldingOut): PortfolioUpcoming | null {
  const direct = holding.upcoming;
  if (direct) {
    const dist = num(direct.distribution_dollars);
    const tax = num(direct.estimated_tax);
    if (dist != null || tax != null || direct.as_of || direct.stage) {
      return {
        distribution_dollars: dist,
        estimated_tax: tax,
        as_of: direct.as_of ?? null,
        stage: direct.stage ?? holding.publication_stage_used ?? null,
      };
    }
  }

  const illustration = holding.illustration;
  if (!illustration) return null;

  const totals = illustration.totals;
  const components = illustration.components ?? [];
  const first = components[0];
  const dist =
    num(totals?.distribution_dollars) ??
    components.reduce((sum, row) => sum + (num(row.distribution_dollars) ?? 0), 0);
  const tax =
    num(totals?.estimated_tax) ??
    num(totals?.estimated_tax_dollars) ??
    num(first?.estimated_tax) ??
    num(first?.estimated_tax_dollars);

  const asOf = first?.as_of ?? first?.ex_date ?? null;
  const stage =
    holding.publication_stage_used ?? first?.publication_stage ?? null;

  if (dist == null && tax == null && !asOf && !stage) return null;
  return {
    distribution_dollars: dist,
    estimated_tax: tax,
    as_of: asOf,
    stage,
  };
}

const STAGE_LABELS: Record<string, string> = {
  announced: "announced",
  monthly: "next",
  preliminary: "announced",
  preliminary_estimate: "announced",
  updated_estimate: "updated",
  updated: "updated",
  final: "final",
  paid: "paid",
};

export function formatAsOfStage(asOf: string | null, stage: string | null): string {
  const stageKey = (stage ?? "").trim().toLowerCase();
  const stageLabel = STAGE_LABELS[stageKey] ?? (stageKey ? stageKey.replace(/_/g, " ") : "");

  if (stageKey === "monthly") {
    return "Est. monthly · next";
  }

  let month = "";
  if (asOf) {
    const date = new Date(`${asOf}T00:00:00Z`);
    if (!Number.isNaN(date.getTime())) {
      month = date.toLocaleString("en-US", { month: "short", timeZone: "UTC" });
    }
  }

  if (month && stageLabel) return `Est. ${month} · ${stageLabel}`;
  if (month) return `Est. ${month}`;
  if (stageLabel) return stageLabel;
  return "—";
}

function rowsForSide(
  allocation: PortfolioAllocationOut,
  side: "current" | "proposed",
): UpcomingRow[] {
  return allocation.holdings.flatMap((holding, index) => {
    const upcoming = upcomingFromHolding(holding);
    if (!upcoming) return [];
    const dist = num(upcoming.distribution_dollars);
    if (dist == null) return [];
    const ticker = (holding.ticker || holding.fund_identifier || "—").toUpperCase();
    return [
      {
        key: `${side}-${holding.holding_index}-${ticker}-${index}`,
        ticker,
        fundName: holding.fund_name || ticker,
        side,
        sideLabel: side === "current" ? "Current" : "Proposed",
        distributionDollars: dist,
        estimatedTax: num(upcoming.estimated_tax),
        asOf: upcoming.as_of ?? null,
        stage: upcoming.stage ?? holding.publication_stage_used ?? null,
        heat: 0,
      },
    ];
  });
}

/** Sort + heat within one allocation so Current and Proposed tables stay independent. */
export function upcomingRowsForSide(
  allocation: PortfolioAllocationOut,
  side: "current" | "proposed",
): UpcomingRow[] {
  const rows = rowsForSide(allocation, side).sort(
    (a, b) => b.distributionDollars - a.distributionDollars,
  );
  const max = rows[0]?.distributionDollars ?? 0;
  return rows.map((row) => ({
    ...row,
    heat: max > 0 ? row.distributionDollars / max : 0,
  }));
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
  const upcoming = upcomingFromHolding(holding);
  const fromUpcoming = num(upcoming?.estimated_tax);
  if (fromUpcoming != null) return fromUpcoming;
  return (
    num(holding.illustration?.totals?.estimated_tax) ??
    num(holding.illustration?.totals?.estimated_tax_dollars) ??
    0
  );
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
