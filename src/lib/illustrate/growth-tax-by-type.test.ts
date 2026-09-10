import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import type { CompareIllustration, CompareResponse } from "./compare-types.ts";
import {
  buildGrowthTaxByTypeModel,
  canonicalizeEstimateType,
  foldEstimateTypeAmounts,
  formatGrowthTaxCell,
  growthTaxYearFromIllustration,
  illustrationsByCalendarYear,
  selectComponentsForYear,
  taxDollarsFromComponent,
  GROWTH_TAX_EMPTY_LABEL,
  GROWTH_TAX_TYPE_COLORS,
  GROWTH_TAX_UNDISCLOSED_LABEL,
} from "./growth-tax-by-type.ts";
import { lockedTaxRates, UI_DEFAULT_TAX_RATES } from "./types.ts";

const here = dirname(fileURLToPath(import.meta.url));

function component(patch: Record<string, unknown>) {
  return {
    distribution_id: "d1",
    fund_name: "Fund",
    estimate_type: "ordinary_income",
    amount_unit: "percent_of_nav",
    publication_stage: "paid",
    as_of: "2024-12-01",
    record_date: "2024-12-10",
    ex_date: "2024-12-11",
    payable_date: "2024-12-12",
    distribution_dollars: 1000,
    distribution_dollars_min: null,
    distribution_dollars_max: null,
    rate_key: "ordinary_income",
    federal_rate: 0.37,
    state_rate: 0.05,
    effective_rate: 0.42,
    estimated_tax_dollars: 420,
    estimated_tax_dollars_min: null,
    estimated_tax_dollars_max: null,
    notes: null,
    ...patch,
  };
}

function illustration(
  matched: boolean,
  components: ReturnType<typeof component>[] = [],
): CompareIllustration {
  return {
    label: "AGTHX",
    matched,
    holding_dollars: 10_000,
    components,
    totals: {
      estimated_tax: components.reduce(
        (sum, row) => sum + (Number(row.estimated_tax_dollars) || 0),
        0,
      ),
    },
  };
}

function yoy(periods: CompareResponse["periods"]): CompareResponse {
  return {
    mode: "yoy",
    periods,
    summary: {
      normalized_holding_dollars: 10_000,
      total_tax_difference: 0,
      annualized_tax_drag_delta: 0,
      distribution_dollars_difference: 0,
      periods_compared: periods.length,
      common_inception: {},
    },
    notes: [],
  };
}

describe("lockedTaxRates", () => {
  it("expands empty / short objects to the five locked keys", () => {
    const empty = lockedTaxRates({});
    assert.deepEqual(Object.keys(empty).sort(), [
      "long_term_capital_gains",
      "ordinary_income",
      "qualified_dividend",
      "short_term_capital_gains",
      "state",
    ]);
    assert.equal(empty.ordinary_income, UI_DEFAULT_TAX_RATES.ordinary_income);
    const short = lockedTaxRates({ ordinary: 0.1, ltcg: 0.15 } as Record<string, number>);
    assert.equal(short.ordinary_income, UI_DEFAULT_TAX_RATES.ordinary_income);
    assert.equal(short.long_term_capital_gains, UI_DEFAULT_TAX_RATES.long_term_capital_gains);
  });
});

describe("estimate_type folding", () => {
  it("keeps Data-named keys and skips unknown types", () => {
    assert.equal(canonicalizeEstimateType("ordinary_income"), "ordinary_income");
    assert.equal(canonicalizeEstimateType("total_capital_gains"), "total_capital_gains");
    assert.equal(canonicalizeEstimateType("other"), "skip");
  });

  it("does not double-count total_capital_gains when LTCG/STCG rows exist", () => {
    const folded = foldEstimateTypeAmounts([
      { estimate_type: "long_term_capital_gains", tax: 1500 },
      { estimate_type: "short_term_capital_gains", tax: 200 },
      { estimate_type: "total_capital_gains", tax: 1700 },
    ]);
    assert.equal(folded.long_term_capital_gains, 1500);
    assert.equal(folded.short_term_capital_gains, 200);
  });

  it("uses total_capital_gains only when component gain rows are absent", () => {
    const folded = foldEstimateTypeAmounts([
      { estimate_type: "ordinary_income", tax: 400 },
      { estimate_type: "total_capital_gains", tax: 900 },
    ]);
    assert.equal(folded.ordinary_income, 400);
    assert.equal(folded.long_term_capital_gains, 900);
    assert.equal(folded.short_term_capital_gains, null);
  });
});

describe("tax from Dist $ × rates", () => {
  it("prefers published tax dollars and does not invent Dist $", () => {
    assert.equal(
      taxDollarsFromComponent(component({ estimated_tax_dollars: 88, distribution_dollars: 200 })),
      88,
    );
    assert.equal(
      taxDollarsFromComponent(
        component({
          estimated_tax_dollars: null,
          distribution_dollars: null,
          effective_rate: 0.42,
        }),
      ),
      null,
    );
  });

  it("applies Dist $ × effective rate when tax is omitted", () => {
    assert.equal(
      taxDollarsFromComponent(
        component({
          estimated_tax_dollars: null,
          distribution_dollars: 1000,
          effective_rate: 0.2,
          estimate_type: "long_term_capital_gains",
        }),
      ),
      200,
    );
  });

  it("does not tax return_of_capital unless Data sent tax $", () => {
    assert.equal(
      taxDollarsFromComponent(
        component({
          estimate_type: "return_of_capital",
          estimated_tax_dollars: null,
          distribution_dollars: 500,
          effective_rate: 0.37,
        }),
      ),
      0,
    );
    assert.equal(
      taxDollarsFromComponent(
        component({
          estimate_type: "return_of_capital",
          estimated_tax_dollars: 12,
          distribution_dollars: 500,
        }),
      ),
      12,
    );
  });
});

describe("paid vs announced year selection", () => {
  it("uses unpaid prelims only and never promotes paid finals into announced", () => {
    const paid = component({
      publication_stage: "final",
      payable_date: "2025-12-12",
      estimated_tax_dollars: 2100,
    });
    const announced = component({
      publication_stage: "preliminary_estimate",
      as_of: "2026-09-01",
      record_date: "2026-12-16",
      ex_date: "2026-12-17",
      payable_date: "2026-12-18",
      estimated_tax_dollars: 410,
    });
    const mixed = selectComponentsForYear([paid, announced]);
    assert.equal(mixed.status, "announced");
    assert.deepEqual(
      mixed.used.map((row) => row.estimated_tax_dollars),
      [410],
    );

    const historical = selectComponentsForYear([paid]);
    assert.equal(historical.status, "paid");
  });

  it("stays empty when there are no components — never invents a type stack from totals", () => {
    const year = growthTaxYearFromIllustration(
      "VFIAX",
      2026,
      illustration(true, []),
    );
    assert.equal(year.status, "empty");
    assert.equal(year.total, null);
    assert.equal(formatGrowthTaxCell(year.total, year.status, "total"), GROWTH_TAX_UNDISCLOSED_LABEL);
    assert.equal(
      formatGrowthTaxCell(year.amounts.ordinary_income, year.status),
      GROWTH_TAX_EMPTY_LABEL,
    );
  });

  it("does not invent announced rows from unmatched illustrations", () => {
    const year = growthTaxYearFromIllustration(
      "VFIAX",
      2026,
      illustration(false, [
        component({
          publication_stage: "preliminary_estimate",
          payable_date: "2026-12-18",
          estimated_tax_dollars: 99,
        }),
      ]),
    );
    assert.equal(year.status, "empty");
    assert.equal(year.total, null);
  });
});

describe("buildGrowthTaxByTypeModel", () => {
  it("supports 1 through 6 funds without assuming three columns", () => {
    const one = buildGrowthTaxByTypeModel(
      [
        {
          ticker: "agthx",
          tax: yoy([
            {
              year: 2024,
              left: illustration(true, [
                component({ estimate_type: "ordinary_income", estimated_tax_dollars: 400 }),
                component({
                  estimate_type: "long_term_capital_gains",
                  estimated_tax_dollars: 1500,
                }),
              ]),
              right: illustration(true, [
                component({ estimate_type: "ordinary_income", estimated_tax_dollars: 400 }),
                component({
                  estimate_type: "long_term_capital_gains",
                  estimated_tax_dollars: 1500,
                }),
              ]),
              deltas: {
                distribution_dollars: 0,
                estimated_tax: 0,
                effective_tax_on_holding: 0,
              },
            },
          ]),
        },
      ],
      [2024],
    );
    assert.deepEqual(one.tickers, ["AGTHX"]);
    assert.equal(one.series[0]?.years[0]?.total, 1900);

    const sixTickers = ["AGTHX", "FCNTX", "VFIAX", "AMCPX", "FBGRX", "DODIX"];
    const six = buildGrowthTaxByTypeModel(
      sixTickers.map((ticker) => ({ ticker, tax: null })),
      [2023, 2024, 2025, 2026],
    );
    assert.equal(six.tickers.length, 6);
    assert.equal(six.series.length, 6);
    assert.ok(six.series.every((row) => row.years.every((year) => year.status === "empty")));
  });

  it("aligns every fund to the same calendar-year columns", () => {
    const years = [2023, 2024, 2025, 2026];
    const model = buildGrowthTaxByTypeModel(
      [
        { ticker: "AGTHX", tax: null },
        { ticker: "FCNTX", tax: null },
        { ticker: "VFIAX", tax: null },
      ],
      years,
    );
    assert.deepEqual(model.years, years);
    for (const row of model.series) {
      assert.deepEqual(
        row.years.map((cell) => cell.year),
        years,
      );
    }
  });

  it("does not mix YoY left/right YE seasons into one column", () => {
    const deltas = {
      distribution_dollars: 0,
      estimated_tax: 0,
      effective_tax_on_holding: 0,
    };
    const agthx = yoy([
      {
        year: 2025,
        left: illustration(true, [
          component({
            as_of: "2024-12-12",
            ex_date: "2024-12-11",
            payable_date: "2024-12-12",
            estimated_tax_dollars: 100,
          }),
        ]),
        right: illustration(true, [
          component({
            as_of: "2025-12-12",
            ex_date: "2025-12-11",
            payable_date: "2025-12-12",
            estimated_tax_dollars: 200,
          }),
        ]),
        deltas,
      },
    ]);
    const fcntx = yoy([
      {
        year: 2025,
        left: illustration(true, []),
        right: illustration(true, [
          component({
            as_of: "2025-12-15",
            ex_date: "2025-12-16",
            payable_date: "2025-12-17",
            estimated_tax_dollars: 350,
          }),
        ]),
        deltas,
      },
    ]);

    const byYear = illustrationsByCalendarYear(agthx);
    assert.equal(byYear.get(2024)?.totals.estimated_tax, 100);
    assert.equal(byYear.get(2025)?.totals.estimated_tax, 200);
    assert.equal(byYear.has(2023), false);

    const model = buildGrowthTaxByTypeModel(
      [
        { ticker: "AGTHX", tax: agthx },
        { ticker: "FCNTX", tax: fcntx },
      ],
      [2024, 2025],
    );
    assert.deepEqual(
      model.series.map((row) => row.years.map((cell) => cell.year)),
      [
        [2024, 2025],
        [2024, 2025],
      ],
    );
    assert.equal(model.series[0]?.years[0]?.total, 100);
    assert.equal(model.series[0]?.years[1]?.total, 200);
    assert.equal(model.series[1]?.years[0]?.status, "empty");
    assert.equal(model.series[1]?.years[1]?.total, 350);
  });
});

describe("Growth & Tax chrome locks", () => {
  it("titles the Compare module Growth & Tax and does not keep the old tax-drag pair", () => {
    const moduleSource = readFileSync(
      join(here, "../../components/illustrate/GrowthAndTaxDragModule.tsx"),
      "utf8",
    );
    const workspace = readFileSync(
      join(here, "../../components/illustrate/CompareWorkspace.tsx"),
      "utf8",
    );
    const chart = readFileSync(
      join(here, "../../components/illustrate/GrowthAndTaxChart.tsx"),
      "utf8",
    );
    assert.match(moduleSource, />\s*Growth & Tax\s*</);
    assert.doesNotMatch(moduleSource, /Growth & tax drag/);
    assert.doesNotMatch(moduleSource, /Annual Tax by Estimate Type/);
    assert.doesNotMatch(moduleSource, /SAMPLE/);
    assert.doesNotMatch(moduleSource, /TaxDragByYearChart/);
    assert.doesNotMatch(moduleSource, /Estimated annual tax drag/);
    assert.match(workspace, /GrowthAndTaxDragModule/);
    assert.doesNotMatch(workspace, /CompareAnnualTable/);
    assert.doesNotMatch(workspace, /CalendarYearTaxTable/);
    assert.match(workspace, /TaxRateFields/);
    assert.match(workspace, /compareTaxRequestFields|lockedTaxRates|toDataApiTaxRates/);
    assert.match(workspace, /UpcomingTable/);
    assert.match(chart, /Announced \(unpaid\)/);
    assert.doesNotMatch(chart, /rotate\(-/);
    assert.match(chart, /fundSeries\.map/);
    assert.doesNotMatch(chart, /strokeDasharray=\{row\.dashed/);
    assert.equal(GROWTH_TAX_TYPE_COLORS.long_term_capital_gains, "#b42318");
    assert.equal(GROWTH_TAX_TYPE_COLORS.ordinary_income, "#1b7a72");
  });
});
