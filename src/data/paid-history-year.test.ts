import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  asOfYearBounds,
  calendarYearOfIso,
  collectPaidHistoryYears,
  defaultPaidHistoryYear,
  paidHistoryCalendarYear,
  paidHistoryYearOptions,
} from "./paid-history-year.ts";
import { paidHistoryViews, withPeerContext } from "./queries.ts";
import type { FundEstimate } from "./types.ts";

function stub(patch: Partial<FundEstimate> = {}): FundEstimate {
  return {
    id: patch.id ?? "fund-1",
    fundName: patch.fundName ?? "Fund",
    ticker: patch.ticker ?? "TICK",
    cusip: "000000000",
    family: "Vanguard",
    category: "Large Blend",
    shareClass: "Admiral",
    nav: 100,
    estimatedDistributionAmount: 1,
    estimatedOrdinaryIncome: 0.2,
    estimatedCapitalGains: 0.8,
    estimatedDistributionPctNav: 1,
    publishedAt: patch.asOfDate ?? "2025-12-24",
    asOfDate: patch.asOfDate ?? "2025-12-24",
    recordDate: patch.recordDate ?? "2025-12-22",
    exDate: patch.exDate ?? "2025-12-23",
    payableDate: patch.payableDate ?? "2025-12-23",
    publicationStage: patch.publicationStage ?? "final",
    bucket: patch.bucket ?? "paid",
    paidHistory: patch.paidHistory ?? [],
    distributionYear: patch.distributionYear ?? 2025,
    ...patch,
  };
}

describe("paid history calendar year", () => {
  it("reads the as_of calendar year and builds inclusive API bounds", () => {
    assert.equal(calendarYearOfIso("2025-12-24"), 2025);
    assert.equal(calendarYearOfIso("2026-01-22T00:00:00Z"), 2026);
    assert.equal(calendarYearOfIso("not-a-date"), null);
    assert.deepEqual(asOfYearBounds(2026), {
      asOfFrom: "2026-01-01",
      asOfTo: "2026-12-31",
    });
  });

  it("defaults to the current year when that year has data, else most recent", () => {
    const vfiax = withPeerContext([
      stub({
        ticker: "VFIAX",
        asOfDate: "2025-12-24",
        distributionYear: 2025,
      }),
    ])[0];
    const mixed = withPeerContext([
      stub({
        id: "2025",
        ticker: "VFIAX",
        asOfDate: "2025-12-24",
        distributionYear: 2025,
      }),
      stub({
        id: "2026",
        ticker: "FXAIX",
        asOfDate: "2026-12-15",
        distributionYear: 2026,
        publicationStage: "paid",
      }),
    ]);

    assert.equal(defaultPaidHistoryYear([vfiax], 2026), 2025);
    assert.equal(defaultPaidHistoryYear(mixed, 2026), 2026);
    assert.equal(defaultPaidHistoryYear([], 2026), 2026);
    assert.deepEqual(collectPaidHistoryYears(mixed), [2026, 2025]);
    assert.deepEqual(paidHistoryYearOptions([vfiax], 2026), [2026, 2025]);
  });

  it("keeps Paid history years from comingling when a year is selected", () => {
    const fund = withPeerContext([
      stub({
        ticker: "ABALX",
        asOfDate: "2026-01-22",
        distributionYear: 2026,
        paidHistory: [
          {
            asOfDate: "2025-01-22",
            recordDate: "2024-12-16",
            exDate: "2024-12-16",
            payableDate: "2024-12-17",
            publicationStage: "final",
            estimatedDistributionAmount: 1.75,
            estimatedOrdinaryIncome: 0,
            estimatedCapitalGains: 1.75,
            estimatedDistributionPctNav: 0,
            distributionYear: 2025,
          },
        ],
      }),
    ])[0];

    assert.equal(paidHistoryCalendarYear(fund), 2026);
    const twentySix = paidHistoryViews([fund], 2026);
    const twentyFive = paidHistoryViews([fund], 2025);
    assert.ok(twentySix.every((row) => row.asOfDate.startsWith("2026-")));
    assert.ok(twentyFive.every((row) => row.asOfDate.startsWith("2025-")));
    assert.equal(
      paidHistoryViews([fund]).length,
      twentySix.length + twentyFive.length,
    );
  });
});
