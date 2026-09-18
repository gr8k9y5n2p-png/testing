import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { COMPARE_DEFAULT_HOLDING_DOLLARS } from "./compare-workspace.ts";
import { PORTFOLIO_COMPARE_BOOK_DOLLARS } from "./portfolio-compare-types.ts";
import {
  parsePortfolioBooksPayload,
  toPortfolioAssetPayload,
} from "../saved-assets/payloads.ts";
import {
  compareWorkspaceIsSavable,
  compareWorkspaceToPortfolioBooks,
  emptyPortfolioBooks,
  portfolioBooksAreSavable,
  portfolioBooksToCompareWorkspace,
  portfolioSavePayloadFromBooks,
  savedPortfolioSubtitle,
} from "./portfolio-save-open.ts";

const here = dirname(fileURLToPath(import.meta.url));

function read(rel: string): string {
  return readFileSync(join(here, rel), "utf8");
}

describe("portfolio Save/Open helpers", () => {
  it("refuses empty books and empty Compare slots", () => {
    assert.equal(portfolioBooksAreSavable(null), false);
    assert.equal(portfolioBooksAreSavable(emptyPortfolioBooks()), false);
    assert.equal(
      portfolioBooksAreSavable({
        current: [{ ticker: "   ", fundName: "", weightPct: 0, holdingDollars: 0, id: "x" }],
        proposed: [],
      }),
      false,
    );
    assert.equal(
      portfolioBooksAreSavable({
        current: [],
        proposed: [{ ticker: "FBGRX", fundName: "FBGRX", weightPct: 10, holdingDollars: 100, id: "fb" }],
      }),
      true,
    );
    assert.equal(compareWorkspaceIsSavable([]), false);
    assert.equal(compareWorkspaceIsSavable(["", "  "]), false);
    assert.equal(compareWorkspaceIsSavable(["fbgrx", "AGTHX"]), true);
  });

  it("subtitles envelope and flat books without inventing holdings", () => {
    assert.equal(savedPortfolioSubtitle(null), "Current 0 · Proposed 0");
    assert.equal(
      savedPortfolioSubtitle({
        version: 1,
        books: {
          bookDollars: 1_000_000,
          current: [{ ticker: "FBGRX" }, { ticker: "AGTHX" }],
          proposed: [{ ticker: "ABALX" }],
        },
      }),
      "Current 2 · Proposed 1",
    );
    assert.equal(
      savedPortfolioSubtitle({
        current: [{ ticker: "FBGRX" }],
        proposed: [],
      }),
      "Current 1 · Proposed 0",
    );
  });

  it("snapshots Compare slots without inventing tickers or names", () => {
    const books = compareWorkspaceToPortfolioBooks(
      { tickers: ["fbgrx", "AGTHX", ""], holdingDollars: 10_000 },
      [
        { ticker: "FBGRX", fundName: "Fidelity Blue Chip Growth", family: "Fidelity", nav: 12.5 },
      ],
    );
    assert.deepEqual(books.compareSlots, ["FBGRX", "AGTHX"]);
    assert.equal(books.compareHoldingDollars, 10_000);
    assert.equal(books.bookDollars, 20_000);
    assert.equal(books.proposed.length, 0);
    assert.equal(books.current[0]?.fundName, "Fidelity Blue Chip Growth");
    assert.equal(books.current[0]?.nav, 12.5);
    assert.equal(books.current[1]?.fundName, "AGTHX");
    assert.equal(books.current[1]?.nav, null);
    assert.equal(books.current.every((row) => row.holdingDollars === 10_000), true);

    const payload = toPortfolioAssetPayload(books);
    assert.equal(payload.version, 1);
    assert.deepEqual(
      (payload.books as { compareSlots?: string[] }).compareSlots,
      ["FBGRX", "AGTHX"],
    );
    const parsed = parsePortfolioBooksPayload(payload);
    assert.deepEqual(
      parsed?.current.map((row) => row.ticker),
      ["FBGRX", "AGTHX"],
    );
    assert.deepEqual(parsed?.proposed, []);
  });

  it("restores Compare slots and keeps Portfolio book dollars off Compare", () => {
    const fromCompare = compareWorkspaceToPortfolioBooks({
      tickers: ["FBGRX", "ABALX"],
      holdingDollars: 25_000,
    });
    const opened = portfolioBooksToCompareWorkspace(
      toPortfolioAssetPayload(fromCompare),
      COMPARE_DEFAULT_HOLDING_DOLLARS,
    );
    assert.deepEqual(opened.tickers, ["FBGRX", "ABALX"]);
    assert.equal(opened.holdingDollars, 25_000);

    const fromPortfolio = portfolioBooksToCompareWorkspace(
      {
        version: 1,
        books: {
          bookDollars: PORTFOLIO_COMPARE_BOOK_DOLLARS,
          current: [{ ticker: "VFIAX" }, { ticker: "AMCPX" }],
          proposed: [{ ticker: "FBGRX" }],
          currentUnit: "pct",
          proposedUnit: "pct",
        },
      },
      COMPARE_DEFAULT_HOLDING_DOLLARS,
    );
    assert.deepEqual(fromPortfolio.tickers, ["VFIAX", "AMCPX", "FBGRX"]);
    assert.equal(fromPortfolio.holdingDollars, COMPARE_DEFAULT_HOLDING_DOLLARS);
  });

  it("caps Compare open at four unique tickers and skips empty payload", () => {
    const many = portfolioBooksToCompareWorkspace(
      {
        current: ["AA", "BB", "CC", "DD", "EE", "FF", "GG"].map((ticker) => ({
          ticker,
        })),
        proposed: [{ ticker: "HH" }],
      },
      10_000,
    );
    assert.deepEqual(many.tickers, ["AA", "BB", "CC", "DD"]);
    assert.deepEqual(
      portfolioBooksToCompareWorkspace(null, 10_000),
      { tickers: [], holdingDollars: 10_000 },
    );
  });

  it("wraps getBooks() in the Modules envelope without seeding holdings", () => {
    const empty = portfolioSavePayloadFromBooks(null);
    assert.equal(empty.version, 1);
    assert.deepEqual(empty.books.current, []);
    assert.deepEqual(empty.books.proposed, []);
    assert.equal(empty.books.bookDollars, PORTFOLIO_COMPARE_BOOK_DOLLARS);
  });
});

describe("Portfolio Save/Open chrome", () => {
  it("wires Compare and Portfolios to the shared SavedAssetActions contract", () => {
    const workspace = read("../../components/illustrate/CompareWorkspace.tsx");
    const homepage = read("../../components/illustrate/HomepagePortfolioCompare.tsx");
    const actions = read("../../components/saved-assets/SavedAssetActions.tsx");
    const toolbar = read("../../components/illustrate/PortfolioSaveOpenActions.tsx");
    const demo = read("../../app/portfolio-compare/page.tsx");
    const demoMount = read("../../components/illustrate/PortfolioCompareDemoMount.tsx");

    for (const source of [workspace, homepage, toolbar, demoMount]) {
      assert.doesNotMatch(source, /NEXT_PUBLIC_FREEMIUM/);
      assert.doesNotMatch(source, /PaywallDialog/);
      assert.doesNotMatch(source, /STRIPE_SECRET_KEY/);
    }

    assert.match(workspace, /SavedAssetActions/);
    assert.match(workspace, /type="portfolio"/);
    assert.match(workspace, /onNotice/);
    assert.match(workspace, /compareWorkspaceToPortfolioBooks/);
    assert.match(workspace, /portfolioBooksToCompareWorkspace/);
    assert.match(workspace, /compareWorkspaceIsSavable/);
    assert.match(homepage, /PortfolioSaveOpenActions/);
    assert.match(homepage, /booksApiRef/);
    assert.match(homepage, /onNotice/);
    assert.match(toolbar, /type="portfolio"/);
    assert.match(toolbar, /portfolioBooksAreSavable/);
    assert.match(toolbar, /portfolioSavePayloadFromBooks/);
    assert.match(toolbar, /parsePortfolioBooksPayload/);
    assert.match(actions, /savedPortfolioSubtitle/);
    assert.match(actions, /PORTFOLIO_SAVE_EMPTY/);
    assert.match(actions, /PORTFOLIO_OPEN_EMPTY/);
    assert.match(demo, /PortfolioCompareDemoMount/);
    assert.match(demoMount, /PortfolioSaveOpenActions/);
  });
});
