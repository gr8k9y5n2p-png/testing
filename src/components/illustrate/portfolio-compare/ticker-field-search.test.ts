import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  tickerFieldMatches,
  toTickerFieldOption,
} from "./ticker-field-search.ts";

const here = dirname(fileURLToPath(import.meta.url));

function read(relative: string): string {
  return readFileSync(join(here, relative), "utf8");
}

describe("Compare / Portfolio live /api/funds autocomplete", () => {
  it("keeps AGTHX from GET /api/funds when the SSR catalog is empty / awaiting", () => {
    const remote = toTickerFieldOption({
      ticker: "AGTHX",
      fundName: "The Growth Fund of America",
      family: "American Funds",
      has_estimate: false,
      coverage_status: "awaiting_estimate",
      nav: 88.419998,
    });
    assert.equal(remote?.ticker, "AGTHX");
    const matches = tickerFieldMatches([], remote ? [remote] : [], "AGTHX");
    assert.equal(matches.length, 1);
    assert.equal(matches[0]?.ticker, "AGTHX");
    assert.equal(matches[0]?.fundName, "The Growth Fund of America");
  });

  it("surfaces Blackrock family and iShares name hits from live search", () => {
    const remote = [
      toTickerFieldOption({
        ticker: "BACPX",
        fund_name: "BlackRock Allocation Target Shares",
        fund_family: "BlackRock",
      }),
      toTickerFieldOption({
        ticker: "IVV",
        fund_name: "iShares Core S&P 500 ETF",
        fund_family: "iShares",
      }),
    ].filter((row): row is NonNullable<typeof row> => row != null);
    const matches = tickerFieldMatches([], remote, "Blackrock");
    assert.equal(matches.some((fund) => fund.ticker === "BACPX"), true);
    assert.equal(matches.some((fund) => fund.ticker === "IVV"), true);
  });

  it("does not require has_estimate or a heroes catalog to keep the identity row", () => {
    const remote = toTickerFieldOption({
      ticker: "FBGRX",
      fund_name: "Fidelity Blue Chip Growth Fund",
      fund_family: "Fidelity",
      has_estimate: false,
    });
    const matches = tickerFieldMatches([], remote ? [remote] : [], "FBGRX");
    assert.equal(matches[0]?.ticker, "FBGRX");
    assert.equal(toTickerFieldOption({ fundName: "No ticker" }), null);
  });

  it("TickerField hits fetchFundsSearch /api/funds on each typed query", () => {
    const field = read("TickerField.tsx");
    const client = read("../../../lib/data-api/funds-client.ts");
    const workspace = read("../CompareWorkspace.tsx");
    const column = read("AllocationColumn.tsx");
    assert.match(field, /fetchFundsSearch/);
    assert.match(field, /fetchFundsSearch\(q\)/);
    assert.match(field, /tickerFieldMatches/);
    assert.match(field, /toTickerFieldOption/);
    assert.match(field, /REMOTE_SEARCH_DEBOUNCE_MS/);
    assert.match(field, /searchPickerEmptyState/);
    assert.doesNotMatch(field, /event\.target\.value\.toUpperCase\(\)/);
    assert.doesNotMatch(field, /NEXT_PUBLIC_DATA_API_URL/);
    assert.doesNotMatch(field, /aftertax-data-api/);
    assert.doesNotMatch(field, /has_estimate/);
    assert.doesNotMatch(field, /PORTFOLIO_TICKER_RATES/);
    assert.match(client, /FUNDS_SEARCH_PATH = "\/api\/funds"/);
    assert.match(client, /fundsSearchParams/);
    assert.match(workspace, /TickerField/);
    assert.match(column, /TickerField/);
  });
});
