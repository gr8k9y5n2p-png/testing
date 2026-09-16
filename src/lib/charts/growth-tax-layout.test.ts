import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  columnLeftEdges,
  GROWTH_TAX_MAX_BAR_W,
  growthTaxBarCenter,
  growthTaxBarWidth,
  growthTaxBarX,
  growthTaxChartPad,
  growthTaxTableLayout,
  labelSitsOffPlot,
  shouldDrawZeroBaselineLabel,
  startAmountCollidesWithZeroAxis,
  startAmountLabel,
  startAmountLabelX,
  startAmountLabelY,
  START_ZERO_LABEL_GAP_PX,
  underBarTickerFontSize,
  underBarTickerLabel,
} from "./growth-tax-layout.ts";
import { SHARED_CHART_WIDTH, yearLayout } from "./shared-axis.ts";
import { formatCompactUsd, niceMoneyScale } from "./money-axis.ts";

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

  it("keeps $18k, $10k, and -$400 fully left of the plot", () => {
    const pad = growthTaxChartPad(10_000, ["$18k", "$10k", "-$400"]);
    assert.ok(pad.left >= 128, "left gutter must clear the plot edge");
    for (const label of ["$18k", "$10k", "-$400"] as const) {
      assert.ok(
        labelSitsOffPlot(label, pad.left),
        `${label} must sit left of pad.left=${pad.left}`,
      );
    }
  });
});

describe("start-$ and $0 tax baseline never overlap", () => {
  it("lifts $10k off the shared zero axis and keeps $0", () => {
    const zeroY = 200;
    const startPlotY = 200;
    assert.equal(startAmountLabel(10_000), "$10k");
    assert.ok(startAmountCollidesWithZeroAxis(startPlotY, zeroY));
    const startY = startAmountLabelY(startPlotY, zeroY);
    assert.equal(startY, zeroY - START_ZERO_LABEL_GAP_PX);
    assert.ok(Math.abs(startY - zeroY) >= START_ZERO_LABEL_GAP_PX);
    assert.equal(shouldDrawZeroBaselineLabel("$10k", startY, zeroY), true);
    assert.notEqual(startAmountLabel(10_000), "$0");
  });

  it("omits duplicate $0 when the start amount is $0", () => {
    const zeroY = 180;
    const startY = startAmountLabelY(zeroY, zeroY);
    assert.equal(startAmountLabel(0), formatCompactUsd(0));
    assert.equal(shouldDrawZeroBaselineLabel(startAmountLabel(0), startY, zeroY), false);
  });

  it("leaves a mid-plot start-$ on its own tick", () => {
    const zeroY = 220;
    const startPlotY = 80;
    assert.equal(startAmountCollidesWithZeroAxis(startPlotY, zeroY), false);
    assert.equal(startAmountLabelY(startPlotY, zeroY), startPlotY);
    assert.equal(shouldDrawZeroBaselineLabel("$10k", startPlotY, zeroY), true);
  });

  it("separates the $10k floor from $0 on the shared Growth + Tax axis", () => {
    const pad = growthTaxChartPad(10_000);
    const growthInner = 220 - pad.top - 10;
    const zeroY = pad.top + growthInner;
    const scale = niceMoneyScale(10_000, 15_438, 10_000);
    const startPlotY =
      pad.top +
      growthInner -
      ((10_000 - scale.min) / (scale.max - scale.min || 1)) * growthInner;
    assert.ok(startAmountCollidesWithZeroAxis(startPlotY, zeroY));
    const startY = startAmountLabelY(startPlotY, zeroY);
    assert.ok(startY < zeroY);
    assert.ok(Math.abs(startY - zeroY) >= START_ZERO_LABEL_GAP_PX);
    assert.equal(shouldDrawZeroBaselineLabel("$10k", startY, zeroY), true);
    assert.ok(labelSitsOffPlot("$10k", pad.left));
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
    assert.match(chart, /startAmountLabelY/);
    assert.match(chart, /shouldDrawZeroBaselineLabel/);
    assert.match(chart, /data-zero-label/);
    assert.match(chart, /data-start-y/);
    assert.match(moduleSource, /growthTaxChartPad/);
    assert.match(moduleSource, /GrowthAndTaxTable/);
    assert.match(moduleSource, /axis=\{axis\}/);
    assert.match(chart, /underBarTickerLabel/);
    assert.match(chart, /data-bar-ticker/);
    assert.match(chart, /data-year-label/);
    assert.match(chart, /growthTaxBarWidth/);
    assert.match(chart, /growthTaxBarCenter/);
    assert.doesNotMatch(chart, /<circle[\s\S]{0,120}data-bar-ticker/);
    assert.match(table, /sr-only/);
    assert.doesNotMatch(
      table,
      /role="row"\s+className="grid min-w-0"[\s\S]*kind === "ticker"/,
    );
  });
});

describe("growthTaxBarWidth slims inverted stacks", () => {
  it("caps wide 1–2 fund slots and leaves 6-fund bars alone", () => {
    assert.equal(growthTaxBarWidth(78.5), GROWTH_TAX_MAX_BAR_W);
    assert.equal(growthTaxBarWidth(37.7), GROWTH_TAX_MAX_BAR_W);
    assert.equal(growthTaxBarWidth(10.6), 10.6);
    assert.ok(GROWTH_TAX_MAX_BAR_W < 28);
    assert.equal(growthTaxBarX(100, 40), 100 + (40 - GROWTH_TAX_MAX_BAR_W) / 2);
    assert.equal(growthTaxBarCenter(100, 40), 120);
  });

  it("keeps the ticker at the bar-stack center for 1–6 funds", () => {
    const years = [2022, 2023, 2024, 2025];
    const pad = growthTaxChartPad(10_000);
    for (const funds of [1, 2, 3, 4, 5, 6]) {
      const axis = yearLayout(years, funds, SHARED_CHART_WIDTH, pad);
      for (let yearIndex = 0; yearIndex < years.length; yearIndex += 1) {
        for (let seriesIndex = 0; seriesIndex < funds; seriesIndex += 1) {
          const left = axis.barX(yearIndex, seriesIndex);
          const visualX = growthTaxBarX(left, axis.barW);
          const visualW = growthTaxBarWidth(axis.barW);
          const tickerX = growthTaxBarCenter(left, axis.barW);
          assert.ok(Math.abs(tickerX - (visualX + visualW / 2)) < 0.05);
        }
      }
    }
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
