import assert from "node:assert/strict";
import { test } from "node:test";
import {
  distributionBucket,
  eventDateOf,
  hasDisclosedUpcomingAmount,
  isPastDistribution,
  isStaleAnnouncedOnly,
  isUpcomingFund,
  splitFundsByBucket,
} from "./distribution-bucket.ts";

const TODAY = "2026-09-08";

test("preliminary and updated estimates stay upcoming when ex/payable are future", () => {
  assert.equal(
    distributionBucket(
      {
        asOfDate: "2026-08-15",
        recordDate: "2026-12-12",
        exDate: "2026-12-15",
        payableDate: "2026-12-17",
        publicationStage: "preliminary_estimate",
      },
      TODAY,
    ),
    "upcoming",
  );
  assert.equal(
    distributionBucket(
      {
        asOfDate: "2026-08-22",
        exDate: "2026-12-15",
        publicationStage: "updated_estimate",
      },
      TODAY,
    ),
    "upcoming",
  );
});

test("paid and final-past rows are paid history", () => {
  assert.equal(
    distributionBucket(
      {
        asOfDate: "2025-12-15",
        exDate: "2025-12-15",
        payableDate: "2025-12-17",
        publicationStage: "paid",
      },
      TODAY,
    ),
    "paid",
  );
  assert.equal(
    distributionBucket(
      {
        asOfDate: "2025-12-10",
        exDate: "2025-12-12",
        publicationStage: "final",
      },
      TODAY,
    ),
    "paid",
  );
});

test("latest_as_of-only identity rows are paid history, not Upcoming", () => {
  assert.equal(
    distributionBucket(
      {
        asOfDate: "2025-12-31",
        recordDate: null,
        exDate: null,
        payableDate: null,
        publicationStage: null,
      },
      TODAY,
    ),
    "paid",
  );
  assert.equal(
    distributionBucket(
      {
        asOfDate: "2025-12-24",
        publicationStage: null,
      },
      TODAY,
    ),
    "paid",
  );
});

test("has_estimate false never qualifies as Upcoming", () => {
  const { upcoming, paid } = splitFundsByBucket([
    { ticker: "FXAIX", bucket: "upcoming" as const, hasEstimate: false },
    { ticker: "VFIAX", bucket: "paid" as const, hasEstimate: false },
    {
      ticker: "AMCPX",
      bucket: "upcoming" as const,
      hasEstimate: true,
      estimatedDistributionAmount: 2.6,
    },
  ]);
  assert.deepEqual(
    upcoming.map((row) => row.ticker),
    ["AMCPX"],
  );
  assert.deepEqual(
    paid.map((row) => row.ticker),
    ["FXAIX", "VFIAX"],
  );
});

test("$0 / empty fake upcoming rows are not Upcoming", () => {
  assert.equal(hasDisclosedUpcomingAmount({}), true);
  assert.equal(
    hasDisclosedUpcomingAmount({
      estimatedDistributionAmount: 0,
      estimatedDistributionPctNav: 0,
      estimatedOrdinaryIncome: 0,
      estimatedCapitalGains: 0,
    }),
    false,
  );
  assert.equal(
    isUpcomingFund({
      bucket: "upcoming",
      hasEstimate: true,
      estimatedDistributionAmount: 0,
      estimatedDistributionPctNav: 0,
      asOfDate: "2025-10-31",
      publicationStage: "updated_estimate",
    }),
    false,
  );
});

test("past final with only as_of (no ex/payable) is paid history, not upcoming", () => {
  assert.equal(
    isPastDistribution(
      {
        asOfDate: "2025-12-31",
        publicationStage: "final",
      },
      TODAY,
    ),
    true,
  );
  assert.equal(
    distributionBucket(
      {
        asOfDate: "2025-12-31",
        recordDate: null,
        exDate: null,
        payableDate: null,
        publicationStage: "final",
      },
      TODAY,
    ),
    "paid",
  );
  assert.equal(
    distributionBucket(
      {
        asOfDate: "2026-01-22",
        publicationStage: "final",
      },
      TODAY,
    ),
    "paid",
  );
});

test("final is paid history even when event dates are still ahead", () => {
  assert.equal(
    distributionBucket(
      {
        asOfDate: "2026-08-15",
        recordDate: "2026-12-12",
        exDate: "2026-12-15",
        payableDate: "2026-12-17",
        publicationStage: "final",
      },
      TODAY,
    ),
    "paid",
  );
});

test("finals-only rows never become Upcoming for any fund (future YE dates or missing stages)", () => {
  assert.equal(
    distributionBucket(
      {
        asOfDate: "2026-01-22",
        recordDate: "2026-12-15",
        exDate: "2026-12-15",
        payableDate: "2026-12-16",
        publicationStage: "final",
      },
      TODAY,
    ),
    "paid",
  );
  assert.equal(
    distributionBucket(
      {
        asOfDate: "2026-01-22",
        recordDate: null,
        exDate: null,
        payableDate: null,
        publicationStage: "final",
      },
      TODAY,
    ),
    "paid",
  );
  assert.equal(
    distributionBucket(
      {
        asOfDate: "2026-12-31",
        recordDate: "2026-12-15",
        exDate: "2026-12-15",
        payableDate: "2026-12-16",
        publicationStage: null,
      },
      TODAY,
    ),
    "paid",
  );
});

test("stale announced-only $0 placeholders are not Upcoming", () => {
  const oct2023 = {
    asOfDate: "2023-10-31",
    recordDate: null,
    exDate: null,
    payableDate: null,
    publicationStage: "updated_estimate",
  };
  const oct2025 = {
    asOfDate: "2025-10-31",
    recordDate: null,
    exDate: null,
    payableDate: null,
    publicationStage: "updated_estimate",
  };
  assert.equal(isStaleAnnouncedOnly(oct2023, TODAY), true);
  assert.equal(isStaleAnnouncedOnly(oct2025, TODAY), true);
  assert.equal(
    isUpcomingFund(
      {
        bucket: "upcoming",
        hasEstimate: true,
        estimatedDistributionAmount: 0,
        estimatedDistributionPctNav: 0,
        ...oct2023,
      },
      TODAY,
    ),
    false,
  );
  assert.equal(
    isUpcomingFund(
      {
        bucket: "upcoming",
        hasEstimate: true,
        estimatedDistributionAmount: 19.71,
        asOfDate: "2026-07-31",
        publicationStage: "preliminary_estimate",
      },
      TODAY,
    ),
    true,
    "unpaid announced dollars with dates still TBD stay Upcoming",
  );
});

test("as_of in the past does not make an announced estimate paid", () => {
  assert.equal(
    isPastDistribution(
      {
        asOfDate: "2026-08-15",
        recordDate: "2026-12-12",
        exDate: "2026-12-15",
      },
      TODAY,
    ),
    false,
  );
  assert.equal(
    distributionBucket(
      {
        asOfDate: "2026-08-15",
        recordDate: "2026-12-12",
        publicationStage: "preliminary_estimate",
      },
      TODAY,
    ),
    "upcoming",
  );
});

test("mid-year 2026 already-paid distribution is paid history, not upcoming", () => {
  const midyear = {
    asOfDate: "2026-06-12",
    recordDate: "2026-06-13",
    exDate: "2026-06-16",
    payableDate: "2026-06-18",
  };
  assert.equal(
    distributionBucket({ ...midyear, publicationStage: "paid" }, TODAY),
    "paid",
  );
  assert.equal(
    distributionBucket(
      { ...midyear, publicationStage: "preliminary_estimate" },
      TODAY,
    ),
    "paid",
  );
});

test("past ex-date keeps a preliminary row out of upcoming", () => {
  assert.equal(
    distributionBucket(
      {
        asOfDate: "2026-06-12",
        exDate: "2026-06-16",
        payableDate: "2026-06-18",
        publicationStage: "preliminary_estimate",
      },
      TODAY,
    ),
    "paid",
  );
});

test("2025 record/ex/payable prelim is paid history on a 2026 visit", () => {
  const stale = {
    asOfDate: "2025-11-20",
    recordDate: "2025-12-12",
    exDate: "2025-12-15",
    payableDate: "2025-12-17",
    publicationStage: "preliminary_estimate",
  };
  assert.equal(eventDateOf(stale), "2025-12-17");
  assert.equal(isPastDistribution(stale, TODAY), true);
  assert.equal(distributionBucket(stale, TODAY), "paid");
  assert.equal(
    distributionBucket(
      {
        asOfDate: "2025-11-22",
        recordDate: "2025-12-12",
        exDate: "2025-12-15",
        payableDate: "2025-12-17",
        publicationStage: "updated_estimate",
      },
      TODAY,
    ),
    "paid",
  );
});

test("past record_date alone is enough to keep a prelim out of upcoming", () => {
  assert.equal(
    eventDateOf({
      recordDate: "2025-12-12",
      exDate: null,
      payableDate: null,
    }),
    "2025-12-12",
  );
  assert.equal(
    distributionBucket(
      {
        asOfDate: "2025-11-20",
        recordDate: "2025-12-12",
        exDate: null,
        payableDate: null,
        publicationStage: "preliminary_estimate",
      },
      TODAY,
    ),
    "paid",
  );
  assert.equal(
    distributionBucket(
      {
        asOfDate: "2025-11-02",
        recordDate: "2025-12-12",
        publicationStage: "updated_estimate",
      },
      TODAY,
    ),
    "paid",
  );
});

test("eventDateOf prefers payable, then ex, then record, and invents nothing", () => {
  assert.equal(
    eventDateOf({
      payableDate: "2026-12-17",
      exDate: "2026-12-15",
      recordDate: "2026-12-12",
    }),
    "2026-12-17",
  );
  assert.equal(
    eventDateOf({
      payableDate: null,
      exDate: "2026-12-15",
      recordDate: "2026-12-12",
    }),
    "2026-12-15",
  );
  assert.equal(
    eventDateOf({
      payableDate: "",
      exDate: "",
      recordDate: "",
    }),
    null,
  );
});

test("FIGFX-style upcoming row is not mixed with paid history", () => {
  const announced = distributionBucket(
    {
      asOfDate: "2026-08-15",
      recordDate: "2026-12-12",
      exDate: "2026-12-15",
      payableDate: "2026-12-17",
      publicationStage: "preliminary_estimate",
    },
    TODAY,
  );
  const history = distributionBucket(
    {
      asOfDate: "2025-12-15",
      recordDate: "2025-12-12",
      exDate: "2025-12-15",
      payableDate: "2025-12-17",
      publicationStage: "paid",
    },
    TODAY,
  );
  assert.equal(announced, "upcoming");
  assert.equal(history, "paid");

  const { upcoming, paid } = splitFundsByBucket([
    { ticker: "FIGFX", bucket: announced },
    { ticker: "FIGFX", bucket: history },
  ]);
  assert.equal(upcoming.length, 1);
  assert.equal(paid.length, 1);
  assert.ok(upcoming.every((row) => row.bucket === "upcoming"));
  assert.ok(paid.every((row) => row.bucket === "paid"));
});
