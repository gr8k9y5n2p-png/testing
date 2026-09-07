import {
  COMPARE_SUMMARY_HOLDING_DOLLARS,
  type ComparePeriodOut,
  type CompareRequest,
  type CompareResponse,
  type CompareSideIn,
  type CompareUpcomingDistribution,
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

const UNANNOUNCED_IDS = new Set(["UNANN", "NOANN"]);
const UNANNOUNCED_STAGES = new Set([
  "unannounced",
  "not_announced",
  "none",
  "not announced",
]);

export function isUnannouncedSide(side?: CompareSideIn | null): boolean {
  if (!side) return false;
  const id = (
    side.selectors?.fund_identifier ??
    side.selectors?.ticker ??
    ""
  ).toUpperCase();
  if (UNANNOUNCED_IDS.has(id)) return true;
  const stage = (side.selectors?.publication_stage ?? "").trim().toLowerCase();
  return UNANNOUNCED_STAGES.has(stage);
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

function selectorsHasLookup(request: CompareRequest): boolean {
  return Boolean(
    request.selectors?.fund_identifier ||
      request.selectors?.ticker ||
      request.selectors?.fund_name ||
      request.selectors?.fund_family,
  );
}

function taxIllustration(
  label: string,
  tax: number | null,
): ComparePeriodOut["left"] {
  const matched = tax != null;
  const dollars = tax ?? 0;
  return {
    label,
    matched,
    holding_dollars: COMPARE_SUMMARY_HOLDING_DOLLARS,
    components: [],
    totals: {
      distribution_dollars: dollars,
      estimated_tax: dollars,
      estimated_tax_dollars: dollars,
      effective_tax_on_holding: dollars / COMPARE_SUMMARY_HOLDING_DOLLARS,
    },
    notes: matched ? [] : ["No distribution estimates matched the selector"],
  };
}

function taxForYear(year: number): number | null {
  return YOY_SKETCH_YEARS.find((row) => row.year === year)?.tax ?? null;
}

function mockYoyResponse(request: CompareRequest): CompareResponse {
  const years =
    request.periods && request.periods.length > 0
      ? request.periods.map((period) => period.year)
      : YOY_SKETCH_YEARS.map((row) => row.year);
  const fundLabel =
    request.left?.label?.trim() ||
    request.selectors?.fund_name?.trim() ||
    request.selectors?.ticker?.trim() ||
    "AMCAP Fund";

  const pairs: ComparePeriodOut[] = [];
  for (let index = 0; index < years.length - 1; index += 1) {
    const older = years[index];
    const newer = years[index + 1];
    pairs.push({
      year: newer,
      as_of: `${newer}-12-15`,
      left: taxIllustration(String(older), taxForYear(older)),
      right: taxIllustration(String(newer), taxForYear(newer)),
      deltas: {
        distribution_dollars: 0,
        estimated_tax: 0,
        effective_tax_on_holding: 0,
      },
    });
  }

  const fromYear = years[0] ?? 2021;
  const toYear = years[years.length - 1] ?? 2025;
  const latestTax = taxForYear(toYear);

  return {
    mode: "yoy",
    source: "mock",
    left: pairs[0]?.left ?? taxIllustration(fundLabel, taxForYear(fromYear)),
    right: pairs[pairs.length - 1]?.right ?? taxIllustration(fundLabel, latestTax),
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
      "MOCK /illustrate/compare mode=yoy — calendar-year tax $ with a 2023 gap.",
      "Unmatched years stay null; the chart must not invent tax-drag rows.",
    ],
  };
}

function upcomingForRequest(
  request: CompareRequest,
): CompareUpcomingDistribution {
  const leftUnannounced = isUnannouncedSide(request.left);
  const rightUnannounced = isUnannouncedSide(request.right);
  const leftDollars = leftUnannounced ? null : 185;
  const rightDollars = rightUnannounced ? null : 100;
  const mixed = leftUnannounced !== rightUnannounced;
  const neither = leftUnannounced && rightUnannounced;
  return {
    left_dollars: leftDollars,
    right_dollars: rightDollars,
    delta_dollars: mixed || neither ? null : -85,
    left_publication_stage: leftUnannounced ? null : "updated_estimate",
    right_publication_stage: rightUnannounced ? null : "preliminary_estimate",
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
      upcoming_taxable_distribution: upcomingForRequest(request),
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
  const leftOk = sideHasLookup(body.left);
  const rightOk = sideHasLookup(body.right);
  if (body.mode === "yoy") {
    if (!(selectorsHasLookup(body) || leftOk)) {
      return "yoy requires selectors or left.selectors";
    }
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
