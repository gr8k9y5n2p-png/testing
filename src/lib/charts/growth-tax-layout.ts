import { formatCompactUsd } from "./money-axis.ts";
import {
  SHARED_CHART_PAD,
  SHARED_CHART_WIDTH,
  yearLayout,
  type ChartPad,
  type YearLayout,
} from "./shared-axis.ts";

/** 12px stub ("Ordinary" + swatch) is wider than the $10k axis gutter. */
export const GROWTH_TAX_STUB_MIN_PX = 90;
/** Room for under-bar tickers on one line and the calendar year below. */
export const GROWTH_TAX_YEAR_AXIS_PX = 58;
export const AXIS_LABEL_GAP_PX = 8;
/** 9px ui-monospace advance — used only to size the left gutter. */
export const AXIS_CHAR_PX = 5.6;

/**
 * Drawn bar width. Slots stay full-width so the type table can still
 * fit dollar cells; the inverted stacks themselves stay slim.
 */
export const GROWTH_TAX_MAX_BAR_W = 18;

export function growthTaxBarWidth(barW: number): number {
  return Math.max(1, Math.min(barW, GROWTH_TAX_MAX_BAR_W));
}

/** Left edge of the slim bar, centered inside the full slot. */
export function growthTaxBarX(barX: number, barW: number): number {
  return barX + (barW - growthTaxBarWidth(barW)) / 2;
}

export function growthTaxBarCenter(barX: number, barW: number): number {
  return barX + barW / 2;
}

/** Centered under-bar ticker. Truncates only when the bar is too narrow (4–6 funds). */
export function underBarTickerLabel(
  ticker: string,
  barW: number,
  fontSize: number,
): string {
  const key = ticker.trim().toUpperCase();
  const advance = Math.max(fontSize * 0.6, 1);
  const maxChars = Math.max(3, Math.floor((barW + 3) / advance));
  return key.length <= maxChars ? key : key.slice(0, maxChars);
}

export function underBarTickerFontSize(fundCount: number): number {
  if (fundCount >= 6) return 5.5;
  if (fundCount >= 5) return 6;
  if (fundCount >= 3) return 8;
  return 9;
}

export function estimateAxisLabelWidth(text: string): number {
  return Math.ceil(Math.max(text.length, 1) * AXIS_CHAR_PX);
}

export function startAmountLabel(startDollars: number): string {
  return formatCompactUsd(startDollars);
}

/** End-anchored x for the starting invested $ label — always left of the plot. */
export function startAmountLabelX(padLeft: number): number {
  return padLeft - AXIS_LABEL_GAP_PX;
}

/**
 * Left gutter grows with the formatted start amount and table stub
 * so "$10k", "$1.0M", and any other principal stay off the plot.
 */
export function growthTaxChartPad(
  startDollars: number,
  extraLabels: string[] = [],
  base: ChartPad = SHARED_CHART_PAD,
): ChartPad {
  const candidates = [
    startAmountLabel(startDollars),
    formatCompactUsd(-Math.max(Math.abs(startDollars), 1)),
    ...extraLabels,
  ];
  const widestAxis = Math.max(...candidates.map(estimateAxisLabelWidth));
  const left = Math.max(
    base.left,
    GROWTH_TAX_STUB_MIN_PX,
    widestAxis + AXIS_LABEL_GAP_PX + 4,
  );
  return {
    ...base,
    left,
    bottom: Math.max(base.bottom, GROWTH_TAX_YEAR_AXIS_PX),
  };
}

/** True when an end-anchored label sits entirely left of x = padLeft. */
export function labelSitsOffPlot(
  text: string,
  padLeft: number,
  x = startAmountLabelX(padLeft),
): boolean {
  const leftEdge = x - estimateAxisLabelWidth(text);
  return leftEdge >= 1 && x <= padLeft - 1;
}

export type GrowthTaxTableColumn =
  | { kind: "stub" }
  | { kind: "lead"; yearIndex: number }
  | { kind: "ticker"; yearIndex: number; seriesIndex: number }
  | { kind: "gap"; yearIndex: number; afterSeriesIndex: number }
  | { kind: "trail"; yearIndex: number }
  | { kind: "right" };

export type GrowthTaxTableLayout = {
  columns: GrowthTaxTableColumn[];
  /** CSS grid-template-columns using the same units as the SVG viewBox. */
  template: string;
  /** ViewBox widths per column — sum equals `width`. */
  fr: number[];
  /** Left edge of each ticker cell. Must equal `axis.barX`. */
  tickerLeft: number[][];
  tickerCenters: number[][];
};

/**
 * Flattened year-slot grid that mirrors `yearLayout` bar geometry.
 * Fund count is `seriesCount` (1–6), never a hardcoded 2 or 3.
 */
export function growthTaxTableLayout(
  years: number[],
  seriesCount: number,
  width = SHARED_CHART_WIDTH,
  pad: ChartPad = SHARED_CHART_PAD,
  axis?: YearLayout,
): GrowthTaxTableLayout {
  const count = Math.max(seriesCount, 1);
  const nYears = Math.max(years.length, 1);
  const layout = axis ?? yearLayout(years, count, width, pad);
  const inset = Math.max(0, (layout.groupW - layout.used) / 2);
  const lead = layout.gutter / 2 + inset;
  const trail = Math.max(0, layout.slot - lead - layout.used);

  const columns: GrowthTaxTableColumn[] = [{ kind: "stub" }];
  const fr: number[] = [pad.left];
  const tickerLeft: number[][] = [];
  const tickerCenters: number[][] = [];

  for (let yearIndex = 0; yearIndex < nYears; yearIndex += 1) {
    columns.push({ kind: "lead", yearIndex });
    fr.push(lead);
    const yearLeft: number[] = [];
    const yearCenters: number[] = [];
    for (let seriesIndex = 0; seriesIndex < count; seriesIndex += 1) {
      if (seriesIndex > 0) {
        columns.push({
          kind: "gap",
          yearIndex,
          afterSeriesIndex: seriesIndex - 1,
        });
        fr.push(layout.gap);
      }
      columns.push({ kind: "ticker", yearIndex, seriesIndex });
      fr.push(layout.barW);
      const left = layout.barX(yearIndex, seriesIndex);
      yearLeft.push(left);
      yearCenters.push(left + layout.barW / 2);
    }
    columns.push({ kind: "trail", yearIndex });
    fr.push(trail);
    tickerLeft.push(yearLeft);
    tickerCenters.push(yearCenters);
  }
  columns.push({ kind: "right" });
  fr.push(pad.right);

  return {
    columns,
    template: fr
      .map((value) => `minmax(0, ${Math.max(value, 0.0001)}fr)`)
      .join(" "),
    fr,
    tickerLeft,
    tickerCenters,
  };
}

/** Running x of each column from the shared fr widths (viewBox units). */
export function columnLeftEdges(fr: number[]): number[] {
  const edges: number[] = [];
  let x = 0;
  for (const value of fr) {
    edges.push(x);
    x += value;
  }
  return edges;
}
