import assert from "node:assert/strict";
import { test } from "node:test";
import {
  distributionBucket,
  isPastDistribution,
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

test("future unpaid announced final stays upcoming", () => {
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
    "upcoming",
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
