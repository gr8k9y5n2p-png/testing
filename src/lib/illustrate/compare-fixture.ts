import {
  COMPARE_SUMMARY_HOLDING_DOLLARS,
  type ComparePeriodOut,
  type CompareRequest,
  type CompareResponse,
  type CompareSideIn,
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

/** Calendar-year tax $ on the $10k summary holding. `null` = gap / unmatched. */
export const YOY_SKETCH_YEARS: { year: number; tax: number | null }[] = [
  { year: 2021, tax: 120 },
  { year: 2022, tax: 95 },
  { year: 2023, tax: null },
  { year: 2024, tax: 110 },
  { year: 2025, tax: 85 },
];

/**
 * Hypothetical annual tax drag as a decimal of value (0.018 = 1.8%).
 * Used by Growth + tax-drag when compare is in `mode: "yoy"`.
 */
const TAX_DRAG_BY_TICKER: Record<string, Record<number, number>> = {
  AGTHX: {
    2016: 0.021, 2017: 0.018, 2018: 0.027, 2019: 0.015, 2020: 0.024,
    2021: 0.019, 2022: 0.011, 2023: 0.016, 2024: 0.02, 2025: 0.014,
  },
  AMCPX: {
    2016: 0.017, 2017: 0.015, 2018: 0.022, 2019: 0.013, 2020: 0.019,
    2021: 0.016, 2022: 0.009, 2023: 0.014, 2024: 0.017, 2025: 0.012,
  },
  FBGRX: {
    2016: 0.032, 2017: 0.028, 2018: 0.041, 2019: 0.024, 2020: 0.038,
    2021: 0.045, 2022: 0.018, 2023: 0.029, 2024: 0.036, 2025: 0.031,
  },
  VFIAX: {
    2016: 0.006, 2017: 0.005, 2018: 0.008, 2019: 0.004, 2020: 0.007,
    2021: 0.005, 2022: 0.003, 2023: 0.004, 2024: 0.006, 2025: 0.005,
  },
  DODIX: {
    2016: 0.019, 2017: 0.017, 2018: 0.021, 2019: 0.016, 2020: 0.018,
    2021: 0.015, 2022: 0.014, 2023: 0.017, 2024: 0.02, 2025: 0.016,
  },
  VTIAX: {
    2016: 0.008, 2017: 0.007, 2018: 0.01, 2019: 0.006, 2020: 0.009,
    2021: 0.007, 2022: 0.005, 2023: 0.006, 2024: 0.008, 2025: 0.007,
  },
};

function tickerFromSide(side?: CompareSideIn | null, selectorsTicker?: string | null): string {
  const raw =
    side?.selectors?.ticker ||
    side?.selectors?.fund_identifier ||
    selectorsTicker ||
    "";
  return raw.trim().toUpperCase();
}

function taxRateFor(ticker: string, year: number): number | null {
  const table = TAX_DRAG_BY_TICKER[ticker];
  if (table && year in table) return table[year];
  const sketch = YOY_SKETCH_YEARS.find((row) => row.year === year);
  if (!sketch) return null;
  return sketch.tax == null ? null : sketch.tax / COMPARE_SUMMARY_HOLDING_DOLLARS;
}

function taxIllustration(
  label: string,
  rate: number | null,
): ComparePeriodOut["left"] {
  const matched = rate != null;
  const dollars = rate == null ? 0 : rate * COMPARE_SUMMARY_HOLDING_DOLLARS;
  return {
    label,
    matched,
    holding_dollars: COMPARE_SUMMARY_HOLDING_DOLLARS,
    components: [],
    totals: {
      distribution_dollars: dollars,
      estimated_tax: dollars,
      estimated_tax_dollars: dollars,
      effective_tax_on_holding: rate ?? 0,
    },
    notes: matched ? [] : ["No distribution estimates matched the selector"],
  };
}

function mockYoyResponse(request: CompareRequest): CompareResponse {
  const ticker = tickerFromSide(request.left, request.selectors?.ticker);
  const fundLabel =
    request.left?.label?.trim() ||
    request.selectors?.fund_name?.trim() ||
    request.selectors?.ticker?.trim() ||
    ticker ||
    "AMCAP Fund";
  const years =
    request.periods && request.periods.length > 0
      ? request.periods.map((period) => period.year)
      : YOY_SKETCH_YEARS.map((row) => row.year);

  const pairs: ComparePeriodOut[] = [];
  for (let index = 0; index < Math.max(0, years.length - 1); index += 1) {
    const older = years[index];
    const newer = years[index + 1];
    pairs.push({
      year: newer,
      as_of: `${newer}-12-15`,
      left: taxIllustration(String(older), taxRateFor(ticker, older)),
      right: taxIllustration(String(newer), taxRateFor(ticker, newer)),
      deltas: {
        distribution_dollars: 0,
        estimated_tax: 0,
        effective_tax_on_holding: 0,
      },
    });
  }

  const fromYear = years[0] ?? 2021;
  const toYear = years[years.length - 1] ?? 2025;
  const latestRate = taxRateFor(ticker, toYear);
  const latestTax = latestRate == null ? null : latestRate * COMPARE_SUMMARY_HOLDING_DOLLARS;

  return {
    mode: "yoy",
    source: "mock",
    left: pairs[0]?.left ?? taxIllustration(fundLabel, taxRateFor(ticker, fromYear)),
    right: pairs[pairs.length - 1]?.right ?? taxIllustration(fundLabel, latestRate),
    deltas: pairs[pairs.length - 1]?.deltas ?? null,
    periods: pairs,
    summary: {
      normalized_holding_dollars: COMPARE_SUMMARY_HOLDING_DOLLARS,
      total_tax_difference: 0,
      annualized_tax_drag_delta: 0,
      distribution_dollars_difference: 0,
      periods_compared: pairs.length,
      common_inception: {
        from_year: fromYear,
        to_year: toYear,
        from_as_of: `${fromYear}-12-15`,
        to_as_of: `${toYear}-12-15`,
      },
      upcoming_taxable_distribution: {
        left_dollars: latestTax,
        right_dollars: latestTax,
        delta_dollars: 0,
        left_publication_stage: latestTax == null ? null : "preliminary_estimate",
        right_publication_stage: latestTax == null ? null : "preliminary_estimate",
      },
    },
    notes: [
      "MOCK /illustrate/compare mode=yoy — calendar-year tax drag for GrowthAndTaxDragModule.",
      "Unmatched years stay null; the chart must not invent tax-drag rows.",
    ],
  };
}

export function mockCompareResponse(request: CompareRequest): CompareResponse {
  if (request.mode === "yoy") {
    return mockYoyResponse(request);
  }
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

function sideHasLookup(side?: CompareSideIn | null): boolean {
  return Boolean(
    side?.distribution_ids?.length ||
      side?.selectors?.fund_identifier ||
      side?.selectors?.ticker ||
      side?.selectors?.fund_name ||
      side?.selectors?.fund_family,
  );
}

export function isCompareRequestValid(body: CompareRequest): string | null {
  if (!(body.holding_dollars > 0)) return "holding_dollars must be greater than 0";
  const leftOk = sideHasLookup(body.left);
  const rightOk = sideHasLookup(body.right);
  const selectorsOk = Boolean(
    body.selectors?.fund_identifier ||
      body.selectors?.ticker ||
      body.selectors?.fund_name ||
      body.selectors?.fund_family,
  );
  if (body.mode === "yoy") {
    if (!(selectorsOk || leftOk)) return "yoy requires selectors or left.selectors";
    if ((body.periods?.length ?? 0) < 2 && !(leftOk && rightOk)) {
      return "yoy requires at least two periods";
    }
    return null;
  }
  if (body.mode === "fund_vs_fund" || body.mode == null) {
    if (!leftOk) return "fund_vs_fund requires left.selectors or left.distribution_ids";
    if (!rightOk) return "fund_vs_fund requires right.selectors or right.distribution_ids";
  }
  return null;
}
