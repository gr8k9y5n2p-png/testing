import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

describe("paid_history contract wiring", () => {
  it("normalizes holdings[].paid_history on portfolio compare", () => {
    const client = readFileSync(join(here, "portfolio-compare-client.ts"), "utf8");
    assert.match(client, /paid_history:/);
    assert.match(client, /normalizeUpcoming\(row\.paid_history\)/);
    assert.match(
      client,
      /Object\.prototype\.hasOwnProperty\.call\(row, "paid_history"\)/,
    );
  });

  it("ships additive paid_history on the mock fixture", () => {
    const fixture = readFileSync(join(here, "portfolio-compare-fixture.ts"), "utf8");
    assert.match(fixture, /paid_history: paidHistory/);
    assert.match(fixture, /publication_stage: "paid"/);
  });

  it("keeps the dedicated field on the holding type", () => {
    const types = readFileSync(join(here, "portfolio-compare-types.ts"), "utf8");
    assert.match(types, /paid_history\?:/);
    assert.match(types, /PortfolioPaidHistory/);
    assert.doesNotMatch(types, /Temporary Paid History fallback/);
  });

  it("does not fall back to illustration.components for Paid History", () => {
    const stage = readFileSync(join(here, "publication-stage.ts"), "utf8");
    const fn = stage.split("function paidHistoryEventsFromHolding")[1]?.split(
      "const STAGE_LABELS",
    )[0];
    assert.ok(fn);
    assert.match(fn, /holding\.paid_history/);
    assert.doesNotMatch(fn, /holding\.illustration/);
    assert.doesNotMatch(fn, /holding\.distributions/);
  });
});

describe("portfolio compare periods wiring", () => {
  it("POSTs periods 2021–2025 on portfolio compare", () => {
    const client = readFileSync(join(here, "portfolio-compare-client.ts"), "utf8");
    assert.match(client, /periods:/);
    assert.match(client, /defaultPortfolioComparePeriods/);
    assert.match(client, /normalizePortfolioComparePeriods/);
  });

  it("mocks calendar-year tax per ticker", () => {
    const fixture = readFileSync(join(here, "portfolio-compare-fixture.ts"), "utf8");
    assert.match(fixture, /mockCalendarYearPeriods/);
    assert.match(fixture, /portfolioYearTaxRate/);
  });
});
