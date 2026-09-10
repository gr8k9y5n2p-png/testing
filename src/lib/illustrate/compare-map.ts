import { formatUsd } from "@/lib/format";
import { userFacingNotes } from "@/lib/illustrate/user-facing-notes";
import {
  scaleNormalizedHoldingDollars,
  scaleUpcomingToHolding,
} from "@/lib/illustrate/compare-delta-strip";
import type {
  ComparePeriodOut,
  CompareResponse,
  CompareSummary,
  CompareUpcomingDistribution,
} from "@/lib/illustrate/compare-types";
import { gateCompareUpcoming, sideIsAnnounced } from "@/lib/illustrate/upcoming-compare";
import {
  comparePeriodIsCovered,
  toCompareTaxDragSeries,
  type TaxDragFundSeries,
} from "@/lib/illustrate/tax-drag-map";

/**
 * API deltas are **right − left** (Fund B − Fund A).
 *
 * Chart: keep the API sign. The locked sketch puts “more tax” on the left
 * (negative) and “less tax” on the right (positive):
 *   - delta > 0 → B has higher tax than A → A is cheaper → bar right / green
 *   - delta < 0 → B has lower tax than A → A is costlier → bar left / red
 *
 * Footer prose: negate to Fund A’s cost-to-holder (`costToA = −delta`).
 * Positive costToA → “more tax” / “more drag” (red).
 * Negative costToA → “less tax” / “less drag” (green).
 * Green only when Fund A (left) is cheaper on tax than the peer.
 */
export type TaxPolarity = "more" | "less" | "even";

export type FundACost = {
  /** −(right − left). Positive means Fund A costs the holder more tax. */
  costToA: number;
  polarity: TaxPolarity;
};

export type TaxDeltaBar = {
  year: number;
  /** API `periods[].deltas.effective_tax_on_holding` (decimal rate). */
  apiDelta: number | null;
  /** apiDelta × 100, for ±0.8% labels. */
  displayPct: number | null;
  polarity: TaxPolarity;
  /** Either side `matched: false` — N/A, not a 0.0% bar. */
  missing?: boolean;
};

export type TaxDeltaMetric = {
  key: "tax_difference" | "tax_drag" | "distributions" | "upcoming_tax";
  label: string;
  headline: string;
  detail: string;
  polarity: TaxPolarity;
};

export type UpcomingSideStatus = {
  dollars: number | null;
  display: string;
  statusLabel: string;
  announced: boolean;
};

export type UpcomingSides = {
  left: UpcomingSideStatus;
  right: UpcomingSideStatus;
};

export type TaxDeltaCardModel = {
  leftLabel: string;
  rightLabel: string;
  sample: boolean;
  bars: TaxDeltaBar[];
  /** Each fund’s individual tax drag (not the delta series). */
  taxSeries: TaxDragFundSeries[];
  metrics: TaxDeltaMetric[];
  upcoming: UpcomingSides;
  inceptionLabel: string;
  notes: string[];
};

const EVEN_DOLLARS = 0.5;
const EVEN_RATE = 0.00005; // 0.005 pp

export function costToFundA(apiDelta: number): number {
  return -apiDelta;
}

export function polarityFromCostToA(
  costToA: number,
  evenThreshold: number,
): TaxPolarity {
  if (Math.abs(costToA) <= evenThreshold) return "even";
  return costToA > 0 ? "more" : "less";
}

export function fundACost(apiDelta: number, evenThreshold: number): FundACost {
  const costToA = costToFundA(apiDelta);
  return { costToA, polarity: polarityFromCostToA(costToA, evenThreshold) };
}

function wholeUsd(value: number): string {
  return formatUsd(Math.abs(Math.round(value)), 0);
}

function moreLessTaxHeadline(costToA: number): string {
  const tone = polarityFromCostToA(costToA, EVEN_DOLLARS);
  if (tone === "even") return "About even";
  return `${wholeUsd(costToA)} ${tone} tax`;
}

function dragHeadline(costToARate: number): string {
  const tone = polarityFromCostToA(costToARate, EVEN_RATE);
  if (tone === "even") return "About even drag";
  const pp = (Math.abs(costToARate) * 100).toFixed(2);
  return `${pp} pp/yr ${tone} drag`;
}

export function barFromPeriod(period: ComparePeriodOut): TaxDeltaBar {
  const apiDelta = period.deltas.effective_tax_on_holding;
  if (!comparePeriodIsCovered(period) || apiDelta == null) {
    return {
      year: period.year,
      apiDelta: null,
      displayPct: null,
      polarity: "even",
      missing: true,
    };
  }
  const numericDelta = Number(apiDelta);
  const { polarity } = fundACost(numericDelta, EVEN_RATE);
  return {
    year: period.year,
    apiDelta: numericDelta,
    displayPct: numericDelta * 100,
    polarity,
  };
}

function inceptionLabel(summary: CompareSummary): string {
  const from = summary.common_inception?.from_year;
  const to = summary.common_inception?.to_year;
  if (from && to && from !== to) return `${from}–${to}`;
  if (from) return String(from);
  return "common inception";
}

export function upcomingSideStatus(
  dollars: number | null | undefined,
  stage?: string | null,
): UpcomingSideStatus {
  if (!sideIsAnnounced(dollars, stage)) {
    return {
      dollars: null,
      display: "—",
      statusLabel: "Not announced",
      announced: false,
    };
  }
  const stageKey = (stage ?? "").trim().toLowerCase();
  const statusLabel = stageKey
    ? stageKey.replace(/_/g, " ")
    : "announced";
  return {
    dollars: dollars ?? null,
    display: dollars != null ? formatUsd(Math.round(dollars), 0) : "—",
    statusLabel,
    announced: true,
  };
}

export function upcomingSidesFromSummary(
  upcoming: CompareUpcomingDistribution | null | undefined,
): UpcomingSides {
  return {
    left: upcomingSideStatus(upcoming?.left_dollars, upcoming?.left_publication_stage),
    right: upcomingSideStatus(upcoming?.right_dollars, upcoming?.right_publication_stage),
  };
}

function holdingPhrase(holdingDollars: number | undefined): string {
  return holdingDollars != null ? `on ${formatUsd(holdingDollars, 0)}` : "on $10k";
}

function upcomingMetric(
  sides: UpcomingSides,
  deltaDollars: number | null | undefined,
  holdingLabel: string,
): TaxDeltaMetric {
  const both = sides.left.announced && sides.right.announced;
  const neither = !sides.left.announced && !sides.right.announced;
  const upcoming =
    both && deltaDollars != null
      ? fundACost(Number(deltaDollars), EVEN_DOLLARS)
      : null;

  return {
    key: "upcoming_tax",
    label: "Upcoming tax",
    headline: both && upcoming
      ? moreLessTaxHeadline(upcoming.costToA)
      : `${sides.left.display} · ${sides.right.display}`,
    detail: neither
      ? `Not announced · this year · ${holdingLabel}`
      : `A ${sides.left.statusLabel} · B ${sides.right.statusLabel} · ${holdingLabel}`,
    polarity: upcoming?.polarity ?? "even",
  };
}

function pickLabel(
  side: { label?: string } | null | undefined,
  fallback: string,
): string {
  const label = side?.label?.trim();
  return label || fallback;
}

export function toTaxDeltaCardModel(
  response: CompareResponse,
  fallbacks?: { left?: string; right?: string },
  options?: { holdingDollars?: number },
): TaxDeltaCardModel {
  const sample = response.source === "mock";

  const first = response.periods[0];
  const leftLabel = pickLabel(
    response.left ?? first?.left,
    fallbacks?.left ?? "Fund A",
  );
  const rightLabel = pickLabel(
    response.right ?? first?.right,
    fallbacks?.right ?? "Fund B",
  );

  const bars = [...response.periods]
    .sort((a, b) => a.year - b.year)
    .map(barFromPeriod);

  const summary = response.summary;
  const displayHolding = options?.holdingDollars;
  const normalized =
    summary.normalized_holding_dollars > 0
      ? summary.normalized_holding_dollars
      : 10_000;
  const scaleDollars = (value: number) =>
    displayHolding != null
      ? scaleNormalizedHoldingDollars(value, displayHolding, normalized)
      : value;
  const gatedUpcoming = gateCompareUpcoming(
    summary.upcoming_taxable_distribution,
    response.periods,
  );
  const upcoming =
    displayHolding != null
      ? scaleUpcomingToHolding(gatedUpcoming, displayHolding, normalized)
      : gatedUpcoming;
  const tax = fundACost(scaleDollars(Number(summary.total_tax_difference ?? 0)), EVEN_DOLLARS);
  const drag = fundACost(
    Number(summary.annualized_tax_drag_delta ?? 0),
    EVEN_RATE,
  );
  const dist = fundACost(
    scaleDollars(Number(summary.distribution_dollars_difference ?? 0)),
    EVEN_DOLLARS,
  );
  const upcomingSides = upcomingSidesFromSummary(upcoming);
  const onHolding = holdingPhrase(displayHolding);

  const window = inceptionLabel(summary);

  const metrics: TaxDeltaMetric[] = [
    {
      key: "tax_difference",
      label: "Tax difference",
      headline: moreLessTaxHeadline(tax.costToA),
      detail: `${onHolding} · ${window}`,
      polarity: tax.polarity,
    },
    {
      key: "tax_drag",
      label: "Tax drag Δ",
      headline: dragHeadline(drag.costToA),
      detail: "annualized",
      polarity: drag.polarity,
    },
    {
      key: "distributions",
      label: "Distributions Δ",
      headline: moreLessTaxHeadline(dist.costToA),
      detail: `from distributions · ${onHolding} · window`,
      polarity: dist.polarity,
    },
    upcomingMetric(upcomingSides, upcoming?.delta_dollars, onHolding),
  ];

  return {
    leftLabel,
    rightLabel,
    sample,
    bars,
    taxSeries: toCompareTaxDragSeries(response, "effective_tax"),
    metrics,
    upcoming: upcomingSides,
    inceptionLabel: window,
    notes: userFacingNotes(response.notes),
  };
}

export function chartScalePct(bars: TaxDeltaBar[], floor = 2): number {
  const peak = bars.reduce((max, bar) => {
    if (bar.missing || bar.displayPct == null) return max;
    return Math.max(max, Math.abs(bar.displayPct));
  }, 0);
  return Math.max(floor, Math.ceil(peak));
}
