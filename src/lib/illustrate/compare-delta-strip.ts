import { formatUsd } from "../format.ts";
import type { CompareUpcomingDistribution } from "./compare-types.ts";
import {
  upcomingEmptyLabel,
  UPCOMING_AWAITING_ESTIMATE,
} from "./portfolio-compare-copy.ts";

export const COMPARE_DELTA_STRIP_HOLDING_DOLLARS = 10_000;

/**
 * Pair summaries stay normalized to `normalized_holding_dollars` ($10k).
 * Compare rescales $ deltas to the shared dollars-invested holding.
 */
export function scaleNormalizedHoldingDollars(
  dollars: number,
  holdingDollars: number,
  normalizedHoldingDollars = COMPARE_DELTA_STRIP_HOLDING_DOLLARS,
): number {
  if (!(normalizedHoldingDollars > 0)) return dollars;
  return dollars * (holdingDollars / normalizedHoldingDollars);
}

export function scaleUpcomingToHolding(
  upcoming: CompareUpcomingDistribution | null | undefined,
  holdingDollars: number,
  normalizedHoldingDollars = COMPARE_DELTA_STRIP_HOLDING_DOLLARS,
): CompareUpcomingDistribution | null | undefined {
  if (!upcoming) return upcoming;
  const scale = (value: number | null | undefined) =>
    value == null
      ? value
      : scaleNormalizedHoldingDollars(value, holdingDollars, normalizedHoldingDollars);
  return {
    ...upcoming,
    left_dollars: scale(upcoming.left_dollars) ?? null,
    right_dollars: scale(upcoming.right_dollars) ?? null,
    delta_dollars: scale(upcoming.delta_dollars) ?? null,
  };
}

export type CompareDeltaStripKey =
  | "tax_difference"
  | "tax_drag"
  | "distributions"
  | "upcoming_tax";

export type CompareDeltaStripItem = {
  key: CompareDeltaStripKey;
  label: string;
  /** Null / reserved → em dash. Never invent $0. */
  headline: string | null;
  detail: string;
  polarity?: "more" | "less" | "even";
  reserved: boolean;
};

export const COMPARE_DELTA_STRIP_LABELS: Record<CompareDeltaStripKey, string> = {
  tax_difference: "Total tax $ Δ",
  tax_drag: "Annualized tax-drag Δ",
  distributions: "Distribution $ Δ",
  upcoming_tax: "Upcoming taxable",
};

/**
 * Pair-Δ strip is only meaningful for ≤2 filled tickers.
 * Empty slots do not count. Hide entirely when more than two funds are compared.
 */
export function showCompareDeltaStrip(filledTickerCount: number): boolean {
  return filledTickerCount <= 2;
}

/**
 * Reserved Modules strip. Always four cells so Compare can mount it
 * without blocking Growth / history / Upcoming.
 */
export function reservedDeltaStrip(
  holdingDollars = COMPARE_DELTA_STRIP_HOLDING_DOLLARS,
): CompareDeltaStripItem[] {
  const holding = `on ${formatUsd(holdingDollars, 0)}`;
  return [
    {
      key: "tax_difference",
      label: COMPARE_DELTA_STRIP_LABELS.tax_difference,
      headline: null,
      detail: holding,
      reserved: true,
    },
    {
      key: "tax_drag",
      label: COMPARE_DELTA_STRIP_LABELS.tax_drag,
      headline: null,
      detail: "%",
      reserved: true,
    },
    {
      key: "distributions",
      label: COMPARE_DELTA_STRIP_LABELS.distributions,
      headline: null,
      detail: "on window",
      reserved: true,
    },
    {
      key: "upcoming_tax",
      label: COMPARE_DELTA_STRIP_LABELS.upcoming_tax,
      headline: UPCOMING_AWAITING_ESTIMATE,
      detail: "unpaid announced",
      reserved: true,
    },
  ];
}

/** Single fund: pair Δ stays reserved. Upcoming is unpaid announced or Awaiting / Add. */
export function deltaStripFromSingleUpcoming(
  upcoming: { announced: boolean; dollars: number | null } | null | undefined,
  holdingDollars = COMPARE_DELTA_STRIP_HOLDING_DOLLARS,
  inUniverse = true,
): CompareDeltaStripItem[] {
  const items = reservedDeltaStrip(holdingDollars);
  const announced = Boolean(upcoming?.announced);
  const dollars = announced ? upcoming?.dollars ?? null : null;
  return items.map((item) => {
    if (item.key !== "upcoming_tax") return item;
    return {
      ...item,
      headline:
        announced && dollars != null
          ? formatUsd(Math.round(dollars), 0)
          : upcomingEmptyLabel(inUniverse),
      reserved: !(announced && dollars != null),
    };
  });
}

export function deltaStripFromPairMetrics(
  metrics: Array<{
    key: CompareDeltaStripKey;
    headline: string;
    detail: string;
    polarity?: "more" | "less" | "even";
  }>,
  holdingDollars = COMPARE_DELTA_STRIP_HOLDING_DOLLARS,
): CompareDeltaStripItem[] {
  const reserved = reservedDeltaStrip(holdingDollars);
  const byKey = new Map(metrics.map((metric) => [metric.key, metric]));
  return reserved.map((item) => {
    const live = byKey.get(item.key);
    if (!live?.headline) return item;
    return {
      ...item,
      headline: live.headline,
      detail: live.detail,
      polarity: live.polarity,
      reserved: false,
    };
  });
}
