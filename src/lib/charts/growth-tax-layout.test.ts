import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  columnLeftEdges,
  growthTaxChartPad,
  growthTaxTableLayout,
  labelSitsOffPlot,
  startAmountLabel,
  startAmountLabelX,
  underBarTickerFontSize,
  underBarTickerLabel,
} from "./growth-tax-layout.ts";
import { SHARED_CHART_WIDTH, yearLayout } from "./shared-axis.ts";
import { formatCompactUsd } from "./money-axis.ts";

const here = dirname(fileURLToPath(import.meta.url));

describe("growthTaxChartPad / start amount off the plot", () => {
  const principals = [1, 500, 10_000, 25_000, 250_000, 1_000_000, 2_500_000, 10_000_000];

  for (const startDollars of principals) {
    it(`keeps ${startAmountLabel(startDollars)} off the plot`, () => {
      const pad = growthTaxChartPad(startDollars);
      const label = startAmountLabel(startDollars);
      assert.equal(label, formatCompactUsd(startDollars));
      assert.ok(
        labelSitsOffPlot(label, pad.left),
        `${label} at x=${startAmountLabelX(pad.left)} must sit left of pad.left=${pad.left}`,
      );
      assert.ok(pad.left >= 90, "stub column must fit Ordinary + swatch");
    });
  }

  it("widens the gutter when the compact label is longer than $10k", () => {
    const tenK = growthTaxChartPad(10_000);
    const oneM = growthTaxChartPad(1_000_000);
    const tenM = growthTaxChartPad(10_000_000);
    assert.ok(oneM.left >= tenK.left);
    assert.ok(tenM.left >= oneM.left);
    assert.notEqual(startAmountLabel(10_000), startAmountLabel(1_000_000));
  });
});

describe("growthTaxTableLayout tracks yearLayout for 1–6 funds", () => {
  const years = [2022, 2023, 2024, 2025, 2026];

  for (const funds of [1, 2, 3, 4, 5, 6]) {
    it(`places ${funds} ticker cell(s) on the bar x of each year`, () => {
      const pad = growthTaxChartPad(10_000);
      const axis = yearLayout(years, funds, SHARED_CHART_WIDTH, pad);
      const table = growthTaxTableLayout(years, funds, SHARED_CHART_WIDTH, pad, axis);
      assert.equal(table.tickerLeft.length, years.length);
      const edges = columnLeftEdges(table.fr);
      assert.ok(Math.abs(table.fr.reduce((sum, value) => sum + value, 0) - SHARED_CHART_WIDTH) < 0.02);

      const tickerCols = table.columns
        .map((column, index) => ({ column, index }))
        .filter((row) => row.column.kind === "ticker");
      assert.equal(tickerCols.length, years.length * funds);

      for (const { column, index } of tickerCols) {
        if (column.kind !== "ticker") continue;
        assert.ok(
          Math.abs(edges[index] - axis.barX(column.yearIndex, column.seriesIndex)) < 0.05,
          `fund=${funds} year=${column.yearIndex} series=${column.seriesIndex}`,
        );
        assert.ok(
          Math.abs(table.fr[index] - axis.barW) < 0.05,
        );
      }
    });
  }

  it("does not bake a 2-fund or 3-fund column count into the helper", () => {
    const pad = growthTaxChartPad(1_000_000);
    const one = growthTaxTableLayout([2025], 1, SHARED_CHART_WIDTH, pad);
    const six = growthTaxTableLayout([2024, 2025, 2026], 6, SHARED_CHART_WIDTH, pad);
    assert.equal(one.columns.filter((column) => column.kind === "ticker").length, 1);
    assert.equal(six.columns.filter((column) => column.kind === "ticker").length, 18);
    assert.notEqual(one.template, six.template);
  });
});

describe("Growth & Tax layout chrome", () => {
  it("wires the shared year-slot grid and an off-plot start label", () => {
    const table = readFileSync(
      join(here, "../../components/illustrate/GrowthAndTaxTable.tsx"),
      "utf8",
    );
    const chart = readFileSync(
      join(here, "../../components/illustrate/GrowthAndTaxChart.tsx"),
      "utf8",
    );
    const moduleSource = readFileSync(
      join(here, "../../components/illustrate/GrowthAndTaxDragModule.tsx"),
      "utf8",
    );
    const layoutSource = readFileSync(join(here, "growth-tax-layout.ts"), "utf8");
    assert.match(table, /growthTaxTableLayout/);
    assert.match(table, /data-growth-tax-table/);
    assert.match(layoutSource, /minmax\(0,/);
    assert.doesNotMatch(table, /grid-cols-2|grid-cols-3|minmax\(8rem/);
    assert.doesNotMatch(table, /tickers\.length === 2|tickers\.length === 3/);
    assert.match(chart, /data-start-label/);
    assert.match(chart, /startAmountLabel/);
    assert.match(chart, /startAmountLabelX/);
    assert.match(moduleSource, /growthTaxChartPad/);
    assert.match(moduleSource, /GrowthAndTaxTable/);
    assert.match(moduleSource, /axis=\{axis\}/);
    assert.match(chart, /underBarTickerLabel/);
    assert.match(chart, /data-bar-ticker/);
    assert.doesNotMatch(chart, /<circle[\s\S]{0,120}data-bar-ticker/);
  });
});

describe("underBarTickerLabel", () => {
  it("keeps full tickers for 1–3 fund bar widths and shortens at 6", () => {
    const wide = underBarTickerLabel("AGTHX", 28, underBarTickerFontSize(2));
    assert.equal(wide, "AGTHX");
    const six = underBarTickerLabel("AGTHX", 10.6, underBarTickerFontSize(6));
    assert.ok(six.length >= 3);
    assert.equal(six, six.toUpperCase());
    assert.ok("AGTHX".startsWith(six));
  });
});
