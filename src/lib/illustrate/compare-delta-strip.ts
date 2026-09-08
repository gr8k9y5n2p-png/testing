import { formatUsd } from "../format.ts";
import { UPCOMING_UNAVAILABLE_HEADLINE } from "./portfolio-compare-copy.ts";

export const COMPARE_DELTA_STRIP_HOLDING_DOLLARS = 10_000;

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
      headline: UPCOMING_UNAVAILABLE_HEADLINE,
      detail: "unpaid announced",
      reserved: true,
    },
  ];
}

/** Single fund: pair Δ stays reserved. Upcoming is unpaid announced or Undisclosed. */
export function deltaStripFromSingleUpcoming(
  upcoming: { announced: boolean; dollars: number | null } | null | undefined,
  holdingDollars = COMPARE_DELTA_STRIP_HOLDING_DOLLARS,
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
          : UPCOMING_UNAVAILABLE_HEADLINE,
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
