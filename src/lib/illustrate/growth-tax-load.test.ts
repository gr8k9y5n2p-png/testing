import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { buildGrowthTaxByTypeModel } from "./growth-tax-by-type.ts";
import { loadGrowthAndTaxDrag } from "./growth-tax-load.ts";
import {
  calendarYearsFromRows,
  growthLinesFromRows,
  mapFundsWithOptionalPerformance,
  missingPerformanceTickers,
  settlePerformancePack,
  taxSeriesFromRows,
  type GrowthSeriesRow,
} from "./growth-tax-series.ts";
import type { CompareResponse } from "./compare-types.ts";
import { TAX_DRAG_NA_LABEL } from "./tax-drag-map.ts";
import { PERFORMANCE_UNAVAILABLE_LABEL } from "../performance/coverage.ts";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import type { PerformanceResponse } from "../performance/types.ts";

function fundInput(ticker: string) {
  return { ticker, label: ticker, fundIdentifier: ticker };
}

function pack(ticker: string, years = [2024, 2025]): PerformanceResponse {
  return {
    fund_ticker: ticker,
    fund_identifier: ticker,
    fund_name: ticker,
    asset_class: "equity",
    start_dollars: 10_000,
    start_date: `${years[0]}-12-31`,
    end_date: `${years[years.length - 1]}-12-31`,
    as_of: `${years[years.length - 1]}-12-31`,
    frequency: "monthly",
    mode: "live",
    source: "live",
    source_urls: [],
    benchmark_id: "SPY",
    benchmark_label: "S&P 500",
    benchmark_tracks: "S&P 500",
    is_proxy: true,
    fund: {
      ticker,
      name: ticker,
      currency: "USD",
      price_unit: "usd_per_share_adjusted",
      return_unit: "decimal",
      growth_unit: "usd",
      points: years.map((year, index) => ({
        date: `${year}-12-31`,
        adj_close: 40 + index,
        monthly_return: index === 0 ? null : 0.08,
        growth_of_x: 10_000 * 1.08 ** index,
      })),
    },
    benchmark: {
      ticker: "SPY",
      name: "SPY",
      currency: "USD",
      price_unit: "usd_per_share_adjusted",
      return_unit: "decimal",
      growth_unit: "usd",
      points: years.map((year, index) => ({
        date: `${year}-12-31`,
        adj_close: 400 + index,
        monthly_return: index === 0 ? null : 0.07,
        growth_of_x: 10_000 * 1.07 ** index,
      })),
    },
    disclaimers: [],
  };
}

function yoyTax(ticker: string, years = [2024, 2025], tax = 185): CompareResponse {
  return {
    mode: "yoy",
    periods: years.map((year) => ({
      year,
      left: {
        label: ticker,
        matched: true,
        totals: {
          estimated_tax: tax,
          estimated_tax_dollars: tax,
          effective_tax_on_holding: 0.0185,
        },
      },
      right: {
        label: ticker,
        matched: true,
        totals: {
          estimated_tax: tax,
          estimated_tax_dollars: tax,
          effective_tax_on_holding: 0.0185,
        },
      },
      deltas: {
        distribution_dollars: 0,
        estimated_tax: 0,
        effective_tax_on_holding: 0,
      },
    })),
    summary: {
      normalized_holding_dollars: 10_000,
      total_tax_difference: 0,
      annualized_tax_drag_delta: 0,
      distribution_dollars_difference: 0,
      periods_compared: years.length,
      common_inception: { from_year: years[0], to_year: years[years.length - 1] },
    },
    notes: [],
  };
}

function row(
  ticker: string,
  performance: PerformanceResponse | null,
  tax: CompareResponse | null = null,
  color = "#1b7a72",
): GrowthSeriesRow {
  return {
    input: fundInput(ticker),
    color,
    performance,
    tax,
    taxSide: "auto",
  };
}

describe("mapFundsWithOptionalPerformance", () => {
  it("skips a 404 ticker and keeps the fund that has a pack", async () => {
    const mapped = await mapFundsWithOptionalPerformance(
      [fundInput("AMCPX"), fundInput("VIGAX")],
      async (fund) => {
        if (fund.ticker === "VIGAX") {
          const error = new Error("No performance fixture for VIGAX") as Error & {
            status: number;
          };
          error.status = 404;
          throw error;
        }
        return pack(fund.ticker);
      },
    );

    assert.ok(mapped.find((item) => item.fund.ticker === "AMCPX")?.performance);
    assert.equal(mapped.find((item) => item.fund.ticker === "VIGAX")?.performance, null);

    const rows = mapped.map((item, index) =>
      row(
        item.fund.ticker,
        item.performance,
        item.fund.ticker === "AMCPX" ? yoyTax("AMCPX") : yoyTax("VIGAX"),
        index === 0 ? "#1b7a72" : "#3a4348",
      ),
    );
    assert.deepEqual(missingPerformanceTickers(rows), ["VIGAX"]);

    const years = calendarYearsFromRows(rows, "effective_tax");
    const growth = growthLinesFromRows(rows, years, 10_000);
    assert.equal(
      growth.some((line) => line.id === "AMCPX"),
      true,
    );
    assert.equal(
      growth.some((line) => line.id === "VIGAX"),
      false,
    );
    assert.equal(
      growth.some((line) => line.points.every((point) => point.value === 0)),
      false,
    );
  });

  it("does not reject Promise.all when every selected fund 404s", async () => {
    const mapped = await mapFundsWithOptionalPerformance(
      [fundInput("VIGAX"), fundInput("ZZNOPE")],
      async (fund) => {
        const error = new Error(`No performance fixture for ${fund.ticker}`) as Error & {
          status: number;
        };
        error.status = 404;
        throw error;
      },
    );

    assert.equal(
      mapped.every((item) => item.performance == null),
      true,
    );
    const rows = mapped.map((item) => row(item.fund.ticker, null, yoyTax(item.fund.ticker)));
    const years = calendarYearsFromRows(rows, "effective_tax");
    const growth = growthLinesFromRows(rows, years, 10_000);
    assert.deepEqual(
      growth.filter((line) => !line.dashed),
      [],
    );
    assert.equal(growth.flatMap((line) => line.points).length, 0);
  });

  it("keeps tax-drag years from compare when growth packs are missing", () => {
    const rows = [row("VIGAX", null, yoyTax("VIGAX", [2024, 2025], 185))];
    const years = calendarYearsFromRows(rows, "tax_dollars");
    assert.ok(years.includes(2024) || years.includes(2025));
    const series = taxSeriesFromRows(rows, years, "tax_dollars");
    assert.equal(series[0]?.id, "VIGAX");
    assert.ok(series[0]?.points.some((point) => point.value != null));
    assert.deepEqual(growthLinesFromRows(rows, years, 10_000), []);
    assert.equal(rows[0]?.tax?.summary.upcoming_taxable_distribution, undefined);
  });

  it("maps uncovered / empty packs to N/A tax gaps and no growth line", () => {
    const uncovered = settlePerformancePack({
      ...pack("FBGRX"),
      covered: false,
      fund: { ...pack("FBGRX").fund, points: [] },
    });
    assert.equal(uncovered, null);

    const rows = [row("FBGRX", null, null)];
    const years = [2024, 2025];
    const series = taxSeriesFromRows(rows, years, "effective_tax");
    assert.deepEqual(
      series[0]?.points.map((point) => (point.value == null ? TAX_DRAG_NA_LABEL : point.value)),
      [TAX_DRAG_NA_LABEL, TAX_DRAG_NA_LABEL],
    );
    assert.deepEqual(growthLinesFromRows(rows, years, 10_000), []);
  });
});

describe("module empty-state wiring", () => {
  it("keeps No Performance on the growth chart and does not blank tax-drag", () => {
    const here = dirname(fileURLToPath(import.meta.url));
    const moduleSource = readFileSync(
      join(here, "../../components/illustrate/GrowthAndTaxDragModule.tsx"),
      "utf8",
    );
    assert.equal(PERFORMANCE_UNAVAILABLE_LABEL, "No Performance");
    assert.match(moduleSource, /PERFORMANCE_UNAVAILABLE_LABEL/);
    assert.match(moduleSource, /GrowthAndTaxChart/);
    assert.doesNotMatch(moduleSource, /Module unavailable/);
    assert.match(moduleSource, /Keep last rows so tax stacks/);
  });
});

describe("growthLinesFromRows", () => {
  it("never draws a zero history line for a row without a pack", () => {
    const rows = [
      row("AMCPX", pack("AMCPX")),
      row("VIGAX", null, yoyTax("VIGAX"), "#3a4348"),
    ];
    const lines = growthLinesFromRows(rows, [2024, 2025], 10_000);
    assert.deepEqual(
      lines.filter((line) => !line.dashed).map((line) => line.id),
      ["AMCPX"],
    );
    assert.ok(lines[0]?.points.every((point) => point.value > 0));
  });
});

describe("loadGrowthAndTaxDrag performance mode", () => {
  it("does not hardcode fixture on the PerformanceQuery", () => {
    const here = dirname(fileURLToPath(import.meta.url));
    const source = readFileSync(join(here, "growth-tax-load.ts"), "utf8");
    assert.match(source, /mode:\s*defaultPerformanceMode\(\)/);
    assert.doesNotMatch(source, /mode:\s*"fixture"/);
    assert.match(source, /defaultPerformanceMode/);
  });
});

describe("3-fund Compare Growth & Tax", () => {
  it("does not fail the book when one performance AbortErrors and one compare fails", async () => {
    const abort = new DOMException("Aborted", "AbortError");
    const result = await loadGrowthAndTaxDrag(
      [
        fundInput("ABALX"),
        fundInput("AGTHX"),
        fundInput("VFIAX"),
      ],
      10_000,
      null,
      undefined,
      new AbortController().signal,
      {
        loaders: {
          async loadPerformance(request) {
            if (request.ticker === "VFIAX") throw abort;
            if (request.ticker === "AGTHX") return null;
            return pack("ABALX", [2022, 2023, 2024, 2025]);
          },
          async loadCompare(request) {
            const ticker =
              request.selectors?.ticker ??
              request.left?.selectors?.ticker ??
              "";
            if (ticker === "AGTHX") throw new Error("compare 422");
            return yoyTax(ticker || "ABALX", [2022, 2023, 2024, 2025], 80);
          },
        },
      },
    );

    assert.equal(result.rows.length, 3);
    assert.ok(result.rows.find((row) => row.input.ticker === "ABALX")?.tax);
    assert.equal(result.rows.find((row) => row.input.ticker === "AGTHX")?.tax, null);
    assert.ok(result.rows.find((row) => row.input.ticker === "VFIAX")?.tax);
    assert.deepEqual(result.missingTickers.sort(), ["AGTHX", "VFIAX"]);

    const years = calendarYearsFromRows(result.rows, "tax_dollars");
    assert.ok(years.length >= 2);
    assert.ok(years.every((year) => year >= 2022 && year <= 2025));

    const model = buildGrowthTaxByTypeModel(
      result.rows.map((row) => ({
        ticker: row.input.ticker,
        tax: row.tax,
        taxSide: row.taxSide,
      })),
      years,
    );
    assert.deepEqual(model.tickers, ["ABALX", "AGTHX", "VFIAX"]);
    assert.ok(model.series.every((row) => row.years.map((cell) => cell.year).join() === years.join()));
    const empty = model.series.find((row) => row.ticker === "AGTHX");
    assert.ok(empty?.years.every((cell) => cell.status === "empty"));
  });

  it("keeps shared calendar years when only some funds have tax or performance", () => {
    const rows = [
      row("ABALX", pack("ABALX", [2022, 2023, 2024, 2025]), yoyTax("ABALX", [2022, 2023, 2024, 2025])),
      row("AGTHX", null, null, "#3a4348"),
      row("VFIAX", pack("VFIAX", [2023, 2024, 2025]), null, "#0f7a4b"),
    ];
    const years = calendarYearsFromRows(rows, "tax_dollars");
    assert.ok(years.includes(2023) && years.includes(2024) && years.includes(2025));
    const model = buildGrowthTaxByTypeModel(
      rows.map((item) => ({ ticker: item.input.ticker, tax: item.tax, taxSide: item.taxSide })),
      years,
    );
    assert.equal(model.series.length, 3);
    assert.ok(model.series.every((series) => series.years.length === years.length));
    const vfiax = model.series.find((series) => series.ticker === "VFIAX");
    assert.ok(vfiax?.years.every((cell) => cell.status === "empty"));
  });

  it("falls back to the locked calendar window when no fund has years yet", () => {
    const years = calendarYearsFromRows(
      [row("ABALX", null, null), row("AGTHX", null, null), row("VFIAX", null, null)],
      "tax_dollars",
    );
    assert.ok(years.length >= 2);
    assert.ok(years.every((year) => year >= 2021 && year <= 2025));
  });

  it("wires Compare prefetch tax so a 3-fund book does not require a second compare storm", () => {
    const here = dirname(fileURLToPath(import.meta.url));
    const workspace = readFileSync(
      join(here, "../../components/illustrate/CompareWorkspace.tsx"),
      "utf8",
    );
    const load = readFileSync(join(here, "growth-tax-load.ts"), "utf8");
    const moduleSource = readFileSync(
      join(here, "../../components/illustrate/GrowthAndTaxDragModule.tsx"),
      "utf8",
    );
    assert.match(workspace, /prefetchTax=\{prefetchTax\}/);
    assert.match(load, /prefetchTax/);
    assert.match(moduleSource, /settledKey !== fetchKey && rows == null/);
    assert.match(moduleSource, /if \(controller\.signal\.aborted\) return/);
  });
});

describe("loadGrowthAndTaxDrag tax rates", () => {
  it("forwards Compare rates through fund_vs_fund and YoY bodies", () => {
    const here = dirname(fileURLToPath(import.meta.url));
    const source = readFileSync(join(here, "growth-tax-load.ts"), "utf8");
    assert.match(source, /compareTaxRequestFields/);
    assert.match(source, /taxRates:\s*options\.taxRates/);
    assert.match(source, /combineStateWithFederal:\s*options\.combineStateWithFederal/);
    assert.match(source, /taxRates:\s*taxFields\.tax_rates/);
    assert.match(source, /combineStateWithFederal:\s*taxFields\.combine_state_with_federal/);
    assert.doesNotMatch(source, /tax_rates:\s*\{\}/);
  });
});
