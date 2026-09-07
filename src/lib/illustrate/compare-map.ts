import { formatUsd } from "@/lib/format";
import type {
  ComparePeriodOut,
  CompareResponse,
  CompareSummary,
} from "@/lib/illustrate/compare-types";

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
  apiDelta: number;
  /** apiDelta × 100, for ±0.8% labels. */
  displayPct: number;
  polarity: TaxPolarity;
};

export type TaxDeltaMetric = {
  key: "tax_difference" | "tax_drag" | "distributions" | "upcoming_tax";
  label: string;
  headline: string;
  detail: string;
  polarity: TaxPolarity;
};

export type TaxDeltaCardModel = {
  leftLabel: string;
  rightLabel: string;
  sample: boolean;
  bars: TaxDeltaBar[];
  metrics: TaxDeltaMetric[];
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
  const apiDelta = Number(period.deltas.effective_tax_on_holding ?? 0);
  const { polarity } = fundACost(apiDelta, EVEN_RATE);
  return {
    year: period.year,
    apiDelta,
    displayPct: apiDelta * 100,
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
): TaxDeltaCardModel {
  const sample =
    response.source === "mock" ||
    response.notes.some((note) => /mock|demo|illustrative/i.test(note));

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
  const tax = fundACost(Number(summary.total_tax_difference ?? 0), EVEN_DOLLARS);
  const drag = fundACost(
    Number(summary.annualized_tax_drag_delta ?? 0),
    EVEN_RATE,
  );
  const dist = fundACost(
    Number(summary.distribution_dollars_difference ?? 0),
    EVEN_DOLLARS,
  );
  const upcomingDelta = summary.upcoming_taxable_distribution?.delta_dollars;
  const upcoming =
    upcomingDelta == null
      ? null
      : fundACost(Number(upcomingDelta), EVEN_DOLLARS);

  const window = inceptionLabel(summary);
  const demo = sample ? " · demo" : "";

  const metrics: TaxDeltaMetric[] = [
    {
      key: "tax_difference",
      label: "Tax difference",
      headline: moreLessTaxHeadline(tax.costToA),
      detail: `on $10k · ${window}${demo}`,
      polarity: tax.polarity,
    },
    {
      key: "tax_drag",
      label: "Tax drag Δ",
      headline: dragHeadline(drag.costToA),
      detail: `annualized${demo}`,
      polarity: drag.polarity,
    },
    {
      key: "distributions",
      label: "Distributions Δ",
      headline: moreLessTaxHeadline(dist.costToA),
      detail: `from distributions · on $10k · window${demo}`,
      polarity: dist.polarity,
    },
    {
      key: "upcoming_tax",
      label: "Upcoming tax",
      headline:
        upcoming == null ? "No estimate this year" : moreLessTaxHeadline(upcoming.costToA),
      detail: `this year · on $10k · vs peer${demo}`,
      polarity: upcoming?.polarity ?? "even",
    },
  ];

  return {
    leftLabel,
    rightLabel,
    sample,
    bars,
    metrics,
    inceptionLabel: window,
    notes: response.notes,
  };
}

export function chartScalePct(bars: TaxDeltaBar[], floor = 2): number {
  const peak = bars.reduce((max, bar) => Math.max(max, Math.abs(bar.displayPct)), 0);
  return Math.max(floor, Math.ceil(peak));
}
