import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { PORTFOLIO_COMPARE_YEARS } from "./portfolio-compare-years.ts";
import {
  calendarYearFromPeriod,
  calendarYearFromPeriodValue,
  normalizePeriodSide,
  normalizePortfolioComparePeriods,
  periodHoldingTicker,
} from "./portfolio-period-map.ts";

describe("portfolio period year / ticker mapping", () => {
  it("reads a year from ISO dates the way Search does", () => {
    assert.equal(calendarYearFromPeriodValue("2025-12-15"), 2025);
    assert.equal(calendarYearFromPeriodValue("2021"), 2021);
    assert.equal(calendarYearFromPeriod({ as_of: "2024-12-17" }), 2024);
    assert.equal(calendarYearFromPeriod({ year: "2023-12-15" }), 2023);
  });

  it("reads a ticker from label / selectors, not only ticker", () => {
    assert.equal(periodHoldingTicker({ label: "AGTHX" }), "AGTHX");
    assert.equal(
      periodHoldingTicker({ selectors: { ticker: "AGTHX" } }),
      "AGTHX",
    );
    assert.equal(periodHoldingTicker({ fund_identifier: "agthx" }), "AGTHX");
    assert.equal(
      periodHoldingTicker({ label: "The Growth Fund of America" }),
      "",
    );
  });

  it("keeps a holding with published tax when ticker is missing", () => {
    const side = normalizePeriodSide({
      holding_index: 0,
      estimated_tax: 2140,
      covered: true,
    });
    assert.equal(side.length, 1);
    assert.equal(side[0]?.estimated_tax, 2140);
    assert.equal(side[0]?.matched, true);
    assert.equal(side[0]?.holding_index, 0);
  });

  it("accepts ticker-keyed holdings and Search-shaped totals", () => {
    const keyed = normalizePeriodSide({
      AGTHX: { estimated_tax: 2200, covered: true },
      DODIX: { totals: { estimated_tax: 4100 } },
    });
    assert.equal(keyed.find((row) => row.ticker === "AGTHX")?.estimated_tax, 2200);
    assert.equal(keyed.find((row) => row.ticker === "DODIX")?.estimated_tax, 4100);

    const labeled = normalizePeriodSide({
      label: "AGTHX",
      totals: { estimated_tax: 1888 },
    });
    assert.equal(labeled[0]?.ticker, "AGTHX");
    assert.equal(labeled[0]?.estimated_tax, 1888);
  });

  it("maps 2021–2025 AGTHX tax from date-year periods with real tax", () => {
    const periods = normalizePortfolioComparePeriods(
      PORTFOLIO_COMPARE_YEARS.map((year) => ({
        year: `${year}-12-15`,
        current: {
          holdings: [
            {
              label: "AGTHX",
              estimated_tax: 2000 + (year - 2021),
              covered: true,
            },
          ],
        },
        proposed: [],
      })),
    );
    assert.deepEqual(
      periods.map((period) => period.year),
      [2021, 2022, 2023, 2024, 2025],
    );
    assert.ok(
      periods.every(
        (period) =>
          period.current[0]?.ticker === "AGTHX" &&
          period.current[0]?.estimated_tax != null &&
          period.current[0]?.estimated_tax > 0,
      ),
    );
  });

  it("does not wipe published AGTHX tax when Upcoming flags the holding uncovered", () => {
    const periods = normalizePortfolioComparePeriods([
      {
        year: 2025,
        current: [
          {
            ticker: "AGTHX",
            estimated_tax: 2140,
            covered: false,
            gap_reason: "no unpaid announce",
          },
        ],
        proposed: [{ ticker: "CGHM", estimated_tax: 0, covered: false }],
      },
    ]);
    assert.equal(periods[0]?.current[0]?.estimated_tax, 2140);
    assert.equal(periods[0]?.current[0]?.matched, true);
    assert.equal(periods[0]?.proposed[0]?.estimated_tax, null);
    assert.equal(periods[0]?.proposed[0]?.matched, false);
  });
});
