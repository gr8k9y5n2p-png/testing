import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { formatDate, formatOptionalDate } from "./format.ts";

describe("formatDate", () => {
  it("includes the year in advisor-facing dates", () => {
    assert.equal(formatDate("2025-12-15"), "Dec 15, 2025");
    assert.equal(formatDate("2026-08-12"), "Aug 12, 2026");
  });
});

describe("formatOptionalDate", () => {
  it("uses the year-inclusive format by default", () => {
    assert.equal(formatOptionalDate("2025-12-15"), "Dec 15, 2025");
    assert.equal(formatOptionalDate("2026-08-14"), "Aug 14, 2026");
  });

  it("does not invent missing or invalid dates", () => {
    assert.equal(formatOptionalDate(null), "—");
    assert.equal(formatOptionalDate(undefined), "—");
    assert.equal(formatOptionalDate(""), "—");
    assert.equal(formatOptionalDate("not-a-date"), "—");
  });

  it("keeps compact month-day only when asked", () => {
    assert.equal(formatOptionalDate("2025-12-15", true), "Dec 15");
  });
});
