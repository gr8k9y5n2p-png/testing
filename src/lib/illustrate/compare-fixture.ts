import {
  COMPARE_SUMMARY_HOLDING_DOLLARS,
  type ComparePeriodOut,
  type CompareRequest,
  type CompareResponse,
} from "@/lib/illustrate/compare-types";

/**
 * Sketch-locked localhost fixture (Aftertax sample card).
 * API signs are right − left so the chart/footer mapping matches the PNG:
 *   2021/2023 A is costlier (negative API delta → red / more tax)
 *   2022/2024/2025 A is cheaper (positive API delta → green / less tax)
 *   Footer aggregates A paying more tax overall.
 */
const SKETCH_BARS: { year: number; apiDelta: number }[] = [
  { year: 2021, apiDelta: -0.008 },
  { year: 2022, apiDelta: 0.012 },
  { year: 2023, apiDelta: -0.003 },
  { year: 2024, apiDelta: 0.009 },
  { year: 2025, apiDelta: 0.004 },
];

function emptyIllustration(label: string, matched: boolean): ComparePeriodOut["left"] {
  return {
    label,
    matched,
    holding_dollars: COMPARE_SUMMARY_HOLDING_DOLLARS,
    components: [],
    totals: {
      distribution_dollars: 0,
      estimated_tax: 0,
      effective_tax_on_holding: 0,
    },
    notes: matched ? [] : ["No distribution estimates matched the selector"],
  };
}

export const SKETCH_COMPARE_DEFAULTS = {
  leftLabel: "Vanguard Total Stock",
  rightLabel: "Active Growth Fund",
} as const;

export function mockCompareResponse(request: CompareRequest): CompareResponse {
  const leftLabel = request.left?.label?.trim() || SKETCH_COMPARE_DEFAULTS.leftLabel;
  const rightLabel = request.right?.label?.trim() || SKETCH_COMPARE_DEFAULTS.rightLabel;
  const years =
    request.periods && request.periods.length > 0
      ? request.periods.map((period) => period.year)
      : SKETCH_BARS.map((bar) => bar.year);

  const bars = years.map((year) => {
    const sketch = SKETCH_BARS.find((bar) => bar.year === year);
    return { year, apiDelta: sketch?.apiDelta ?? 0 };
  });

  const periods: ComparePeriodOut[] = bars.map(({ year, apiDelta }) => ({
    year,
    as_of: `${year}-12-15`,
    left: emptyIllustration(leftLabel, true),
    right: emptyIllustration(rightLabel, true),
    deltas: {
      distribution_dollars: 0,
      estimated_tax: 0,
      effective_tax_on_holding: apiDelta,
    },
  }));

  const fromYear = periods[0]?.year ?? 2021;
  const toYear = periods[periods.length - 1]?.year ?? 2025;

  return {
    mode: "fund_vs_fund",
    source: "mock",
    left: emptyIllustration(leftLabel, true),
    right: emptyIllustration(rightLabel, true),
    deltas: periods[periods.length - 1]?.deltas ?? null,
    periods,
    summary: {
      // Negatives so Fund A framing reads “more tax”, matching the sketch footer.
      normalized_holding_dollars: COMPARE_SUMMARY_HOLDING_DOLLARS,
      total_tax_difference: -142,
      annualized_tax_drag_delta: -0.0028,
      distribution_dollars_difference: -95,
      periods_compared: periods.length,
      common_inception: {
        from_year: fromYear,
        to_year: toYear,
        from_as_of: `${fromYear}-12-15`,
        to_as_of: `${toYear}-12-15`,
      },
      upcoming_taxable_distribution: {
        left_dollars: 185,
        right_dollars: 100,
        delta_dollars: -85,
        left_publication_stage: "updated_estimate",
        right_publication_stage: "preliminary_estimate",
      },
    },
    notes: [
      "Deltas are right − left (B − A). Interactive Modules charts deltas.effective_tax_on_holding.",
      "summary dollar fields are scaled linearly to $10,000 (value × 10000 / holding_dollars).",
      "MOCK /illustrate/compare — sketch fixture so localhost still demos when the Data API is down.",
    ],
  };
}

export function isCompareRequestValid(body: CompareRequest): string | null {
  if (!(body.holding_dollars > 0)) return "holding_dollars must be greater than 0";
  const leftOk = Boolean(
    body.left?.distribution_ids?.length ||
      body.left?.selectors?.fund_identifier ||
      body.left?.selectors?.ticker ||
      body.left?.selectors?.fund_name ||
      body.left?.selectors?.fund_family,
  );
  const rightOk = Boolean(
    body.right?.distribution_ids?.length ||
      body.right?.selectors?.fund_identifier ||
      body.right?.selectors?.ticker ||
      body.right?.selectors?.fund_name ||
      body.right?.selectors?.fund_family,
  );
  if (body.mode === "fund_vs_fund" || body.mode == null) {
    if (!leftOk) return "fund_vs_fund requires left.selectors or left.distribution_ids";
    if (!rightOk) return "fund_vs_fund requires right.selectors or right.distribution_ids";
  }
  return null;
}
