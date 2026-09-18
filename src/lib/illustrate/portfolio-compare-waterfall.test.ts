import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

/**
 * Request budget after the Portfolios populate fix (parity with Compare #276).
 *
 * Before (measured from source):
 *   /portfolio and /portfolio-compare SSR awaited getDistributionRepository()
 *   — unpaid-announce /distributions walk (or 5×200 dump fallback) — before
 *   any client JS could start Calendar-year tax / Upcoming.
 *   PortfolioCompare then waited 250ms, POSTed the full book, and had no
 *   in-flight cache. Confirm identity used the hydrated catalog, not thin
 *   /funds/lookup.
 *
 * After:
 *   first paint skips the catalog dump.
 *   Confirm uses thin /api/funds (nav_only) + /api/funds/lookup.
 *   Compare POST starts at 50ms and shares the 45s in-flight cache.
 *   Lookup and the book POST run together; adding a holding does not
 *   remount the page or walk the repository.
 */

const here = dirname(fileURLToPath(import.meta.url));

function read(relative: string): string {
  return readFileSync(join(here, relative), "utf8");
}

describe("portfolio page first paint", () => {
  it("does not block /portfolio on the unpaid catalog dump", () => {
    const page = read("../../app/portfolio/page.tsx");
    const demo = read("../../app/portfolio-compare/page.tsx");
    const homepage = read("../../components/illustrate/HomepagePortfolioCompare.tsx");
    const compare = read("../../components/illustrate/PortfolioCompare.tsx");
    const client = read("portfolio-compare-client.ts");

    for (const source of [page, demo, homepage]) {
      assert.doesNotMatch(source, /getDistributionRepository/);
      assert.doesNotMatch(source, /repository\.search/);
    }
    assert.match(page, /HomepagePortfolioCompare/);
    assert.match(compare, /fetchFundLookup/);
    assert.match(compare, /PORTFOLIO_FETCH_DEBOUNCE_MS/);
    assert.doesNotMatch(compare, /,\s*250\)/);
    assert.match(client, /PORTFOLIO_FETCH_DEBOUNCE_MS = 50/);
    assert.match(client, /portfolioCompareCache\.remember/);
    assert.match(client, /portfolioCompareRequestCacheKey/);
    assert.doesNotMatch(compare, /navOnly: false/);
  });
});
