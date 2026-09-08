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

  it("maps null estimated_tax to N/A (Data’s upcoming unmatched shape)", () => {
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
    const response = fundCompare([period(2024, missing, publishedZero)]);
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
