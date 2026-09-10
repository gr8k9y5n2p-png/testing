import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

describe("Lists Data API hydrate", () => {
  it("loads identity via retried GET /funds and does not drop a page on one bad row", () => {
    const lists = readFileSync(join(here, "lists-page.ts"), "utf8");
    const dists = readFileSync(join(here, "distributions.ts"), "utf8");
    assert.match(lists, /loadFundIdentityByTicker/);
    assert.match(lists, /loadDistributionsForFundPage/);
    assert.match(lists, /loadUpcomingDistributionRows/);
    assert.match(lists, /dedupeRows/);
    assert.match(lists, /hydrateAll/);
    assert.match(lists, /rowsForTicker/);
    assert.match(lists, /listRowFromFund/);
    assert.match(lists, /upstreamFailed/);
    assert.doesNotMatch(lists, /raw\.every\(/);
    assert.doesNotMatch(lists, /getDistributionRepository/);
    assert.match(dists, /export async function loadFundIdentityByTicker/);
    assert.match(dists, /fundPageSearchParams/);
    assert.match(dists, /fundsApiItemsFromPayload/);
    assert.match(dists, /payload\.filter\(isFundsApiItem\)/);
    assert.match(dists, /attempt < 2/);
    assert.match(dists, /loadDistributionRows\(\{ q: ticker \}\)/);
    assert.match(dists, /export async function loadUpcomingDistributionRows/);
    assert.match(dists, /distributions \$\{response\.status\}/);
    assert.match(lists, /input\.upcomingRows/);
    assert.match(lists, /input\.distributionRows/);
  });
});
