import {
  COMPARE_SUMMARY_HOLDING_DOLLARS,
  type ComparePeriodOut,
  type CompareRequest,
  type CompareResponse,
  type CompareSideIn,
} from "@/lib/illustrate/compare-types";
import { demoEngineNotes } from "@/lib/illustrate/user-facing-notes";

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
    2016: 0.009, 2017: 0.008, 2018: 0.011, 2019: 0.007, 2020: 0.01,
    2021: 0.0082, 2022: 0.0071, 2023: 0.0118, 2024: 0.0096, 2025: 0.0088,
  },
  FCNTX: {
    2016: 0.006, 2017: 0.005, 2018: 0.007, 2019: 0.004, 2020: 0.006,
    2021: 0.0048, 2022: 0.0041, 2023: 0.0062, 2024: 0.0054, 2025: 0.0049,
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
  // 2022 is a genuine no-distribution zero; 2023 is omitted → matched:false / N/A.
  VTSAX: {
    2016: 0.01, 2017: 0.009, 2018: 0.012, 2019: 0.008, 2020: 0.011,
    2021: 0.012, 2022: 0, 2024: 0.011, 2025: 0.0085,
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

const TAX_DRAG_TICKER_ALIASES: Record<string, string> = {
  AMCAP: "AMCPX",
};

function taxRateFor(ticker: string, year: number): number | null {
  const key = TAX_DRAG_TICKER_ALIASES[ticker] ?? ticker;
  const table = TAX_DRAG_BY_TICKER[key];
  if (table && year in table) return table[year];
  const sketch = YOY_SKETCH_YEARS.find((row) => row.year === year);
  if (!sketch) return null;
  return sketch.tax == null ? null : sketch.tax / COMPARE_SUMMARY_HOLDING_DOLLARS;
}

function taxIllustration(
  label: string,
  rate: number | null,
  holding: number,
): ComparePeriodOut["left"] {
  const book = holding > 0 ? holding : COMPARE_SUMMARY_HOLDING_DOLLARS;
  const matched = rate != null;
  const dollars = rate == null ? null : rate * book;
  return {
    label,
    matched,
    holding_dollars: book,
    components: [],
    totals: {
      // Future Data shape: unmatched years send null totals, not 0.00.
      distribution_dollars: dollars,
      estimated_tax: dollars,
      estimated_tax_dollars: dollars,
      effective_tax_on_holding: rate,
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
  const holding =
    request.holding_dollars > 0
      ? request.holding_dollars
      : COMPARE_SUMMARY_HOLDING_DOLLARS;
  const years =
    request.periods && request.periods.length > 0
      ? request.periods.map((period) => period.year)
      : YOY_SKETCH_YEARS.map((row) => row.year);

  const pairs: ComparePeriodOut[] = [];
  for (let index = 0; index < Math.max(0, years.length - 1); index += 1) {
    const older = years[index];
    const newer = years[index + 1];
    const left = taxIllustration(String(older), taxRateFor(ticker, older), holding);
    const right = taxIllustration(String(newer), taxRateFor(ticker, newer), holding);
    pairs.push({
      year: newer,
      as_of: `${newer}-12-15`,
      left,
      right,
      deltas: {
        distribution_dollars:
          (right.totals?.distribution_dollars ?? 0) -
          (left.totals?.distribution_dollars ?? 0),
        estimated_tax:
          (right.totals?.estimated_tax ?? 0) - (left.totals?.estimated_tax ?? 0),
        effective_tax_on_holding: 0,
      },
    });
  }

  const fromYear = years[0] ?? 2021;
  const toYear = years[years.length - 1] ?? 2025;
  const latestRate = taxRateFor(ticker, toYear);

  return {
    mode: "yoy",
    source: "mock",
    left: pairs[0]?.left ?? taxIllustration(fundLabel, taxRateFor(ticker, fromYear), holding),
    right: pairs[pairs.length - 1]?.right ?? taxIllustration(fundLabel, latestRate, holding),
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
      // Historical YoY tax is not Upcoming. Null = undisclosed, never invent $ from annual.
      upcoming_taxable_distribution: null,
    },
    notes: [
      ...demoEngineNotes(
        "MOCK /illustrate/compare mode=yoy — calendar-year tax drag for GrowthAndTaxDragModule.",
      ),
      "Period totals.estimated_tax scale with request holding_dollars. summary.*_difference stays at $10,000.",
      "Unmatched years: matched=false + null tax totals (Data PR #2 5d02120). Published $0 stays 0.00.",
    ],
  };
}

export function mockCompareResponse(request: CompareRequest): CompareResponse {
  if (request.mode === "yoy") {
    return mockYoyResponse(request);
  }
  const leftLabel = request.left?.label?.trim() || SKETCH_COMPARE_DEFAULTS.leftLabel;
  const rightLabel = request.right?.label?.trim() || SKETCH_COMPARE_DEFAULTS.rightLabel;
  const leftTicker = tickerFromSide(request.left);
  const rightTicker = tickerFromSide(request.right);
  const holding =
    request.holding_dollars > 0
      ? request.holding_dollars
      : COMPARE_SUMMARY_HOLDING_DOLLARS;
  const years =
    request.periods && request.periods.length > 0
      ? request.periods.map((period) => period.year)
      : SKETCH_BARS.map((bar) => bar.year);

  const bars = years.map((year) => {
    const sketch = SKETCH_BARS.find((bar) => bar.year === year);
    return { year, apiDelta: sketch?.apiDelta ?? 0 };
  });

  const periods: ComparePeriodOut[] = bars.map(({ year, apiDelta }) => {
    const left = taxIllustration(leftLabel, taxRateFor(leftTicker, year), holding);
    const right = taxIllustration(rightLabel, taxRateFor(rightTicker, year), holding);
    const bothMatched = left.matched && right.matched;
    return {
      year,
      as_of: `${year}-12-15`,
      left,
      right,
      deltas: {
        distribution_dollars: bothMatched
          ? (right.totals?.distribution_dollars ?? 0) -
            (left.totals?.distribution_dollars ?? 0)
          : 0,
        estimated_tax: bothMatched
          ? (right.totals?.estimated_tax ?? 0) - (left.totals?.estimated_tax ?? 0)
          : 0,
        // Keep sketch signs when both sides matched so the delta card still demos.
        effective_tax_on_holding: bothMatched ? apiDelta : 0,
      },
    };
  });

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
      ...demoEngineNotes(
        "MOCK /illustrate/compare — sketch fixture so localhost still demos when the Data API is down.",
      ),
    ],
  };
}

/** One side announced, the other not — YoY bars still present. */
export function mockCompareMixedUpcomingResponse(
  request: CompareRequest,
): CompareResponse {
  const base = mockCompareResponse(request);
  return {
    ...base,
    summary: {
      ...base.summary,
      upcoming_taxable_distribution: {
        left_dollars: 185,
        right_dollars: null,
        delta_dollars: null,
        left_as_of: "2026-12-15",
        right_as_of: null,
        left_publication_stage: "announced",
        right_publication_stage: null,
      },
    },
    notes: [
      ...base.notes,
      "Mixed upcoming coverage: Fund B is not announced. Historical YoY bars are unchanged.",
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
