import assert from "node:assert/strict";
import { describe, it } from "node:test";
import type { CompareIllustration, ComparePeriodOut, CompareResponse } from "./compare-types.ts";
import {
  TAX_DRAG_NA_LABEL,
  alignTaxDragYears,
  comparePeriodIsCovered,
  illustrationIsMatched,
  illustrationIsUnmatched,
  taxDragValueFromIllustration,
  taxDragValueFromPeriodSide,
  toCompareTaxDragSeries,
  toTaxDragPeriods,
} from "./tax-drag-map.ts";

function side(
  label: string,
  matched: boolean,
  tax: number | string = 0,
  rate: number | string = 0,
): CompareIllustration {
  return {
    label,
    matched,
    holding_dollars: 10_000,
    totals: {
      distribution_dollars: Number(tax),
      estimated_tax: tax as number,
      estimated_tax_dollars: tax as number,
      effective_tax_on_holding: rate as number,
    },
  };
}

function period(
  year: number,
  left: CompareIllustration,
  right: CompareIllustration,
  delta = 0,
): ComparePeriodOut {
  return {
    year,
    left,
    right,
    deltas: {
      distribution_dollars: 0,
      estimated_tax: 0,
      effective_tax_on_holding: delta,
    },
  };
}

function yoyCompare(periods: ComparePeriodOut[]): CompareResponse {
  const years = periods.flatMap((row) => [row.year - 1, row.year]).filter((year) => year > 0);
  const fromYear = Math.min(...years, 2021);
  const toYear = Math.max(...years, 2025);
  return {
    mode: "yoy",
    periods,
    summary: {
      normalized_holding_dollars: 10_000,
      total_tax_difference: 0,
      annualized_tax_drag_delta: 0,
      distribution_dollars_difference: 0,
      periods_compared: periods.length,
      common_inception: { from_year: fromYear, to_year: toYear },
    },
    notes: [],
  };
}

/**
 * Live Data `mode=yoy` with periods[2021..2025]: zip consecutive years,
 * `period.year` = newer, labels stay the ticker when the client sent left.label.
 */
function liveYoyPairs(
  years: number[],
  makeSide: (year: number) => CompareIllustration,
  deltasForPair?: (older: number, newer: number) => ComparePeriodOut["deltas"],
): ComparePeriodOut[] {
  const pairs: ComparePeriodOut[] = [];
  for (let index = 0; index < years.length - 1; index += 1) {
    const older = years[index];
    const newer = years[index + 1];
    const row = period(newer, makeSide(older), makeSide(newer));
    if (deltasForPair) row.deltas = deltasForPair(older, newer);
    pairs.push(row);
  }
  return pairs;
}

function fundCompare(periods: ComparePeriodOut[]): CompareResponse {
  return {
    mode: "fund_vs_fund",
    left: periods[0]?.left,
    right: periods[0]?.right,
    periods,
    summary: {
      normalized_holding_dollars: 10_000,
      total_tax_difference: 0,
      annualized_tax_drag_delta: 0,
      distribution_dollars_difference: 0,
      periods_compared: periods.length,
      common_inception: { from_year: 2021, to_year: 2025 },
    },
    notes: [],
  };
}

describe("matched boolean is the miss signal", () => {
  it("treats only explicit true as matched", () => {
    assert.equal(illustrationIsMatched({ matched: true }), true);
    assert.equal(illustrationIsMatched({ matched: "true" }), true);
    assert.equal(illustrationIsMatched({ matched: false }), false);
    assert.equal(illustrationIsMatched({ matched: "false" }), false);
    assert.equal(illustrationIsMatched({}), false);
    assert.equal(illustrationIsMatched(null), false);
    assert.equal(illustrationIsUnmatched({ matched: false }), true);
    assert.equal(illustrationIsUnmatched({ matched: true }), false);
    assert.equal(illustrationIsUnmatched({}), false);
  });

  it("maps matched:false + 0.00 totals to N/A, not a zero bar", () => {
    const response = fundCompare([
      period(
        2023,
        side("A", false, "0.00", "0.000000"),
        side("B", true, "0.00", "0.000000"),
      ),
    ]);
    const left = toTaxDragPeriods(response, "effective_tax", "left");
    const right = toTaxDragPeriods(response, "effective_tax", "right");
    assert.deepEqual(left, [{ year: 2023, value: null }]);
    assert.deepEqual(right, [{ year: 2023, value: 0 }]);
    assert.equal(left[0].value == null ? TAX_DRAG_NA_LABEL : "0%", TAX_DRAG_NA_LABEL);
    assert.equal(right[0].value, 0);
    assert.equal(comparePeriodIsCovered(response.periods[0]), false);
  });

  it("maps matched:true + estimated_tax 0.00 to a real zero", () => {
    const response = fundCompare([
      period(2022, side("Muni", true, "0.00", "0.000000"), side("Peer", true, 110, 0.011)),
    ]);
    assert.deepEqual(toTaxDragPeriods(response, "tax_dollars", "left"), [
      { year: 2022, value: 0 },
    ]);
    assert.deepEqual(toTaxDragPeriods(response, "effective_tax", "left"), [
      { year: 2022, value: 0 },
    ]);
    assert.equal(comparePeriodIsCovered(response.periods[0]), true);
  });

  it("maps null estimated_tax to N/A when deltas also have no tax", () => {
    const missing: CompareIllustration = {
      label: "A",
      matched: true,
      totals: {
        distribution_dollars: null,
        estimated_tax: null,
        estimated_tax_dollars: null,
        effective_tax_on_holding: null,
      },
    };
    const publishedZero: CompareIllustration = {
      label: "B",
      matched: true,
      totals: {
        distribution_dollars: 0,
        estimated_tax: 0,
        estimated_tax_dollars: 0,
        effective_tax_on_holding: 0,
      },
    };
    const row = period(2024, missing, publishedZero);
    row.deltas = {
      distribution_dollars: null,
      estimated_tax: null,
      effective_tax_on_holding: null,
    };
    const response = fundCompare([row]);
    assert.equal(taxDragValueFromIllustration(missing, "tax_dollars"), null);
    assert.equal(taxDragValueFromIllustration(publishedZero, "tax_dollars"), 0);
    assert.equal(taxDragValueFromIllustration(publishedZero, "effective_tax"), 0);
    assert.deepEqual(toTaxDragPeriods(response, "tax_dollars", "left"), [
      { year: 2024, value: null },
    ]);
    assert.deepEqual(toTaxDragPeriods(response, "effective_tax", "right"), [
      { year: 2024, value: 0 },
    ]);
    assert.equal(comparePeriodIsCovered(response.periods[0]), false);
  });

  it("does not invent 0 when a shared year has no point", () => {
    const aligned = alignTaxDragYears([{ year: 2021, value: 0.01 }], [2021, 2022, 2023]);
    assert.deepEqual(aligned, [
      { year: 2021, value: 0.01 },
      { year: 2022, value: null },
      { year: 2023, value: null },
    ]);
  });
});

describe("toCompareTaxDragSeries — per-fund YoY", () => {
  it("emits left and right series for fund_vs_fund", () => {
    const response = fundCompare([
      period(2021, side("VTSAX", true, 120, 0.012), side("AGTHX", true, 82, 0.0082)),
      period(2022, side("VTSAX", true, "0.00", "0.000000"), side("AGTHX", true, 71, 0.0071)),
      period(2023, side("VTSAX", false, "0.00", "0.000000"), side("AGTHX", true, 118, 0.0118)),
    ]);
    const series = toCompareTaxDragSeries(response, "effective_tax");
    assert.equal(series.length, 2);
    assert.equal(series[0].label, "VTSAX");
    assert.equal(series[1].label, "AGTHX");
    assert.deepEqual(
      series[0].points.map((point) => point.value),
      [0.012, 0, null],
    );
    assert.deepEqual(
      series[1].points.map((point) => point.value),
      [0.0082, 0.0071, 0.0118],
    );
  });

  it("maps Data PR #2 unmatched sides: matched:false + null money + null deltas", () => {
    const unmatched: CompareIllustration = {
      label: "2019",
      matched: false,
      notes: ["No distribution estimates matched the selector"],
      totals: {
        distribution_dollars: null,
        estimated_tax: null,
        estimated_tax_dollars: null,
        estimated_tax_min: null,
        estimated_tax_max: null,
        federal_tax: null,
        state_tax: null,
        effective_tax_on_holding: null,
      },
    };
    const published = side("AMCPX", true, "170.00", "0.017");
    const row = period(2024, unmatched, published);
    row.deltas = {
      distribution_dollars: null,
      estimated_tax: null,
      federal_tax: null,
      state_tax: null,
      effective_tax_on_holding: null,
    };
    assert.equal(taxDragValueFromIllustration(unmatched, "tax_dollars"), null);
    assert.equal(taxDragValueFromIllustration(unmatched, "effective_tax"), null);
    assert.equal(taxDragValueFromIllustration(published, "effective_tax"), 0.017);
    assert.equal(comparePeriodIsCovered(row), false);
    assert.deepEqual(toTaxDragPeriods(fundCompare([row]), "tax_dollars", "left"), [
      { year: 2024, value: null },
    ]);
  });

  it("keeps AMCPX ∩ DODIX 2021–2025 fully charted (Data history tip)", () => {
    const years = [2021, 2022, 2023, 2024, 2025] as const;
    const amcpx: Record<(typeof years)[number], number> = {
      2021: 0.016, 2022: 0.009, 2023: 0.014, 2024: 0.017, 2025: 0.012,
    };
    const dodix: Record<(typeof years)[number], number> = {
      2021: 0.015, 2022: 0.014, 2023: 0.017, 2024: 0.02, 2025: 0.016,
    };
    const response = fundCompare(
      years.map((year) =>
        period(
          year,
          side("AMCPX", true, amcpx[year] * 10_000, amcpx[year]),
          side("DODIX", true, dodix[year] * 10_000, dodix[year]),
        ),
      ),
    );
    const series = toCompareTaxDragSeries(response, "effective_tax");
    assert.deepEqual(
      series[0].points.map((point) => point.year),
      [...years],
    );
    assert.ok(series[0].points.every((point) => point.value != null));
    assert.ok(series[1].points.every((point) => point.value != null));
    assert.ok(response.periods.every((row) => comparePeriodIsCovered(row)));
  });

  it("keeps a yoy vintage pair as one fund series", () => {
    const response: CompareResponse = {
      mode: "yoy",
      periods: [
        period(2022, side("2021", true, 80, 0.008), side("2022", true, "0.00", 0)),
        period(2023, side("2022", true, "0.00", 0), side("2023", false, "0.00", "0.000000")),
      ],
      summary: {
        normalized_holding_dollars: 10_000,
        total_tax_difference: 0,
        annualized_tax_drag_delta: 0,
        distribution_dollars_difference: 0,
        periods_compared: 2,
        common_inception: { from_year: 2021, to_year: 2023 },
      },
      notes: [],
    };
    const series = toCompareTaxDragSeries(response, "effective_tax");
    assert.equal(series.length, 1);
    assert.deepEqual(series[0].points, [
      { year: 2021, value: 0.008 },
      { year: 2022, value: 0 },
      { year: 2023, value: null },
    ]);
  });
});

function matchedNullTotals(label: string): CompareIllustration {
  return {
    label,
    matched: true,
    holding_dollars: 10_000,
    totals: {
      distribution_dollars: null,
      estimated_tax: null,
      estimated_tax_dollars: null,
      effective_tax_on_holding: null,
    },
  };
}

describe("matched:true + null totals falls back to period deltas", () => {
  it("charts yoy shared deltas.estimated_tax when both vintages are matched with null totals", () => {
    const row = period(2024, matchedNullTotals("AGTHX"), matchedNullTotals("AGTHX"));
    row.deltas = {
      distribution_dollars: null,
      estimated_tax: "82.00" as unknown as number,
      estimated_tax_dollars: "82.00" as unknown as number,
      effective_tax_on_holding: "0.0082" as unknown as number,
    };
    assert.equal(taxDragValueFromPeriodSide(row, "left", "tax_dollars", true), 82);
    assert.equal(taxDragValueFromPeriodSide(row, "right", "effective_tax", true), 0.0082);
    assert.equal(comparePeriodIsCovered(row), true);
    const yoy = yoyCompare([row]);
    assert.deepEqual(toTaxDragPeriods(yoy, "tax_dollars"), [
      { year: 2023, value: 82 },
      { year: 2024, value: 82 },
    ]);
  });

  it("does not use shared deltas for a fund_vs_fund series (peer miss must not wipe a fund)", () => {
    const row = period(2024, matchedNullTotals("AGTHX"), matchedNullTotals("FBGRX"));
    row.deltas = {
      distribution_dollars: null,
      estimated_tax: 82,
      effective_tax_on_holding: 0.0082,
    };
    assert.equal(taxDragValueFromPeriodSide(row, "left", "tax_dollars"), null);
    assert.deepEqual(toTaxDragPeriods(fundCompare([row]), "tax_dollars", "left"), [
      { year: 2024, value: null },
    ]);
  });

  it("keeps matched:true + 0.00 totals as a real zero even when deltas are nonzero", () => {
    const row = period(2022, side("Muni", true, "0.00", "0.000000"), side("Peer", true, 110, 0.011));
    row.deltas = {
      distribution_dollars: 110,
      estimated_tax: 110,
      effective_tax_on_holding: 0.011,
    };
    assert.equal(taxDragValueFromPeriodSide(row, "left", "tax_dollars"), 0);
    assert.deepEqual(toTaxDragPeriods(fundCompare([row]), "tax_dollars", "left"), [
      { year: 2022, value: 0 },
    ]);
  });

  it("does not chart shared deltas when matched:false", () => {
    const unmatched = {
      ...matchedNullTotals("FBGRX"),
      matched: false,
      notes: ["No distribution estimates matched the selector"],
    };
    const row = period(2023, unmatched, matchedNullTotals("AGTHX"));
    row.deltas = {
      distribution_dollars: 95,
      estimated_tax: 95,
      effective_tax_on_holding: 0.0095,
    };
    assert.equal(taxDragValueFromPeriodSide(row, "left", "tax_dollars", true), null);
    assert.equal(taxDragValueFromPeriodSide(row, "right", "tax_dollars", true), 95);
    assert.equal(comparePeriodIsCovered(row), false);
    assert.deepEqual(toTaxDragPeriods(fundCompare([row]), "tax_dollars", "left"), [
      { year: 2023, value: null },
    ]);
  });

  it("prefers per-side delta fields when Data nests tax under deltas.left/right", () => {
    const row = period(2025, matchedNullTotals("AGTHX"), matchedNullTotals("FBGRX"));
    row.deltas = {
      distribution_dollars: null,
      estimated_tax: 40,
      effective_tax_on_holding: 0.004,
      left: { estimated_tax: 88, effective_tax_on_holding: 0.0088 },
      right: { estimated_tax: 12, effective_tax_on_holding: 0.0012 },
    };
    assert.equal(taxDragValueFromPeriodSide(row, "left", "tax_dollars"), 88);
    assert.equal(taxDragValueFromPeriodSide(row, "right", "tax_dollars"), 12);
    assert.deepEqual(toTaxDragPeriods(fundCompare([row]), "effective_tax", "left"), [
      { year: 2025, value: 0.0088 },
    ]);
    assert.deepEqual(toTaxDragPeriods(fundCompare([row]), "effective_tax", "right"), [
      { year: 2025, value: 0.0012 },
    ]);
  });

  it("maps live yoy AGTHX 2021–2025 from totals on ticker-labeled pairs", () => {
    const taxes: Record<number, { dollars: number; rate: number }> = {
      2021: { dollars: 82, rate: 0.0082 },
      2022: { dollars: 71, rate: 0.0071 },
      2023: { dollars: 118, rate: 0.0118 },
      2024: { dollars: 96, rate: 0.0096 },
      2025: { dollars: 88, rate: 0.0088 },
    };
    const years = [2021, 2022, 2023, 2024, 2025];
    const response = yoyCompare(
      liveYoyPairs(years, (year) =>
        side("AGTHX", true, taxes[year].dollars, taxes[year].rate),
      ),
    );
    const points = toTaxDragPeriods(response, "effective_tax");
    assert.deepEqual(
      points.map((point) => point.year),
      years,
    );
    assert.deepEqual(
      points.map((point) => point.value),
      years.map((year) => taxes[year].rate),
    );
    assert.ok(points.every((point) => point.value != null));
    const aligned = alignTaxDragYears(points, years);
    assert.ok(
      aligned.every((point) => point.value != null),
      "growth-axis 2021–2025 must not be all N/A after alignTaxDragYears",
    );
  });

  it("maps FBGRX yoy unmatched 2021–2023 as N/A and matched 2024–2025 from totals", () => {
    const years = [2021, 2022, 2023, 2024, 2025];
    const covered = new Set([2024, 2025]);
    const response = yoyCompare(
      liveYoyPairs(years, (year) =>
        covered.has(year)
          ? side("FBGRX", true, 310, 0.031)
          : { ...matchedNullTotals("FBGRX"), matched: false },
      ),
    );
    const points = toTaxDragPeriods(response, "tax_dollars");
    assert.deepEqual(
      points.map((point) => point.year),
      years,
    );
    assert.deepEqual(
      points.map((point) => point.value),
      [null, null, null, 310, 310],
    );
  });

  it("charts AGTHX independently when FBGRX is unmatched for 2021–2023", () => {
    const years = [2021, 2022, 2023, 2024, 2025];
    const agthx: Record<number, number> = {
      2021: 0.0082, 2022: 0.0071, 2023: 0.0118, 2024: 0.0096, 2025: 0.0088,
    };
    const fbgrx: Record<number, number | null> = {
      2021: null, 2022: null, 2023: null, 2024: 0.036, 2025: 0.031,
    };
    const response = fundCompare(
      years.map((year) => {
        const rightMatched = fbgrx[year] != null;
        const row = period(
          year,
          side("AGTHX", true, agthx[year] * 10_000, agthx[year]),
          rightMatched
            ? side("FBGRX", true, (fbgrx[year] as number) * 10_000, fbgrx[year] as number)
            : { ...matchedNullTotals("FBGRX"), matched: false },
        );
        row.deltas = rightMatched
          ? {
              distribution_dollars: 0,
              estimated_tax: ((fbgrx[year] as number) - agthx[year]) * 10_000,
              effective_tax_on_holding: (fbgrx[year] as number) - agthx[year],
            }
          : {
              distribution_dollars: null,
              estimated_tax: null,
              effective_tax_on_holding: null,
            };
        return row;
      }),
    );
    const series = toCompareTaxDragSeries(response, "effective_tax");
    assert.equal(series[0].label, "AGTHX");
    assert.equal(series[1].label, "FBGRX");
    assert.deepEqual(
      series[0].points.map((point) => point.value),
      years.map((year) => agthx[year]),
    );
    assert.deepEqual(
      series[1].points.map((point) => point.value),
      [null, null, null, 0.036, 0.031],
    );
    assert.equal(comparePeriodIsCovered(response.periods[0]), false);
    assert.ok(
      series[0].points.every((point) => point.value != null),
      "AGTHX bars must not be wiped by FBGRX gaps or comparePeriodIsCovered",
    );
  });

  it("charts a matched yoy vintage even when the paired vintage is unmatched", () => {
    const response: CompareResponse = {
      mode: "yoy",
      periods: [
        period(2022, { ...matchedNullTotals("2021"), matched: false }, side("2022", true, 71, 0.0071)),
      ],
      summary: {
        normalized_holding_dollars: 10_000,
        total_tax_difference: 0,
        annualized_tax_drag_delta: 0,
        distribution_dollars_difference: 0,
        periods_compared: 1,
        common_inception: { from_year: 2021, to_year: 2022 },
      },
      notes: [],
    };
    response.periods[0].deltas = {
      distribution_dollars: null,
      estimated_tax: null,
      effective_tax_on_holding: null,
    };
    const points = toTaxDragPeriods(response, "effective_tax");
    assert.deepEqual(points, [
      { year: 2021, value: null },
      { year: 2022, value: 0.0071 },
    ]);
  });

  it("derives % tax drag from estimated_tax / holding when effective_tax_on_holding is null", () => {
    const left: CompareIllustration = {
      label: "AGTHX",
      matched: true,
      holding_dollars: 10_000,
      totals: {
        distribution_dollars: 82,
        estimated_tax: 82,
        estimated_tax_dollars: 82,
        effective_tax_on_holding: null,
      },
    };
    const response = fundCompare([period(2021, left, { ...matchedNullTotals("FBGRX"), matched: false })]);
    response.periods[0].deltas = {
      distribution_dollars: null,
      estimated_tax: null,
      effective_tax_on_holding: null,
    };
    assert.equal(taxDragValueFromIllustration(left, "effective_tax"), 0.0082);
    assert.deepEqual(toTaxDragPeriods(response, "effective_tax", "left"), [
      { year: 2021, value: 0.0082 },
    ]);
    assert.deepEqual(toTaxDragPeriods(response, "effective_tax", "right"), [
      { year: 2021, value: null },
    ]);
  });

  it("ignores side-level estimated_tax and reads totals.estimated_tax", () => {
    const illustration = {
      ...matchedNullTotals("AGTHX"),
      estimated_tax: 999,
      estimated_tax_dollars: 999,
      effective_tax_on_holding: 0.0999,
    } as CompareIllustration & {
      estimated_tax: number;
      estimated_tax_dollars: number;
      effective_tax_on_holding: number;
    };
    assert.equal(taxDragValueFromIllustration(illustration, "tax_dollars"), null);
    assert.equal(taxDragValueFromIllustration(illustration, "effective_tax"), null);
    const withTotals: CompareIllustration = {
      ...illustration,
      totals: {
        distribution_dollars: 82,
        estimated_tax: 82,
        estimated_tax_dollars: 82,
        effective_tax_on_holding: 0.0082,
      },
    };
    assert.equal(taxDragValueFromIllustration(withTotals, "tax_dollars"), 82);
    assert.equal(taxDragValueFromIllustration(withTotals, "effective_tax"), 0.0082);
  });

  it("derives % from totals.estimated_tax / summary holding when illustration holding is missing", () => {
    const left: CompareIllustration = {
      label: "AGTHX",
      matched: true,
      totals: {
        distribution_dollars: 82,
        estimated_tax: 82,
        effective_tax_on_holding: null,
      },
    };
    const response = fundCompare([
      period(2024, left, { ...matchedNullTotals("FBGRX"), matched: false }),
    ]);
    assert.deepEqual(toTaxDragPeriods(response, "effective_tax", "left"), [
      { year: 2024, value: 0.0082 },
    ]);
  });

  it("recovers yoy pair years from as_of when period.year is 0", () => {
    const row = period(0, side("AGTHX", true, 82, 0.0082), side("AGTHX", true, 71, 0.0071));
    row.as_of = "2024-12-15";
    const points = toTaxDragPeriods(yoyCompare([row]), "effective_tax");
    assert.deepEqual(points, [
      { year: 2023, value: 0.0082 },
      { year: 2024, value: 0.0071 },
    ]);
  });
});
