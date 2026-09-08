import assert from "node:assert/strict";
import { describe, it } from "node:test";
import type {
  PortfolioAllocationOut,
  PortfolioDistributionRow,
  PortfolioHoldingOut,
} from "./portfolio-compare-types.ts";
import {
  announcedDateOf,
  paidHistoryRowsForSide,
  publicationBucket,
  totalUpcomingTax,
  upcomingFromHolding,
  upcomingRowsForSide,
} from "./publication-stage.ts";

const TODAY = "2026-09-08";

function holding(
  patch: Partial<PortfolioHoldingOut> & { ticker: string },
): PortfolioHoldingOut {
  return {
    holding_index: 0,
    fund_identifier: patch.ticker,
    holding_dollars: 250_000,
    covered: true,
    warnings: [],
    ...patch,
  };
}

function allocation(holdings: PortfolioHoldingOut[]): PortfolioAllocationOut {
  return {
    label: "Current Allocation",
    holdings,
    totals: {
      distribution_dollars: 0,
      estimated_tax: 0,
      effective_tax_on_holding: 0,
    },
    coverage: {
      dollars_total: 250_000,
      dollars_covered: 250_000,
      dollars_uncovered: 0,
      coverage_pct: 100,
    },
    gaps: [],
    warnings: [],
  };
}

function row(
  patch: PortfolioDistributionRow & { publication_stage: string },
): PortfolioDistributionRow {
  return patch;
}

describe("publicationBucket", () => {
  it("puts preliminary_estimate and updated_estimate in upcoming when event dates are future", () => {
    assert.equal(
      publicationBucket(
        row({
          publication_stage: "preliminary_estimate",
          as_of: "2026-08-12",
          record_date: "2026-12-16",
          ex_date: "2026-12-17",
        }),
        TODAY,
      ),
      "upcoming",
    );
    assert.equal(
      publicationBucket(
        row({
          publication_stage: "updated_estimate",
          payable_date: "2026-12-18",
        }),
        TODAY,
      ),
      "upcoming",
    );
  });

  it("keeps paid and final out of upcoming", () => {
    assert.equal(
      publicationBucket(row({ publication_stage: "paid", as_of: "2026-08-12" }), TODAY),
      "paid_history",
    );
    assert.equal(
      publicationBucket(
        row({
          publication_stage: "final",
          record_date: "2026-08-14",
          ex_date: "2026-08-15",
        }),
        TODAY,
      ),
      "paid_history",
    );
  });

  it("puts past event-dated prelims in paid history, not upcoming", () => {
    assert.equal(
      publicationBucket(
        row({
          publication_stage: "preliminary_estimate",
          as_of: "2026-08-12",
          record_date: "2026-08-14",
          ex_date: "2026-08-15",
          payable_date: "2026-08-18",
        }),
        TODAY,
      ),
      "paid_history",
    );
    assert.equal(
      publicationBucket(
        row({
          publication_stage: "preliminary_estimate",
          as_of: "2025-11-20",
          record_date: "2025-12-12",
        }),
        TODAY,
      ),
      "paid_history",
    );
  });

  it("does not treat as_of as an event date, so an August announcement of December still upcoming", () => {
    assert.equal(
      publicationBucket(
        row({
          publication_stage: "preliminary_estimate",
          as_of: "2026-08-12",
        }),
        TODAY,
      ),
      "upcoming",
    );
  });
});

describe("announcedDateOf", () => {
  it("uses as_of until announced_date exists and never invents a day", () => {
    assert.equal(announcedDateOf({ as_of: "2026-12-15" }), "2026-12-15");
    assert.equal(
      announcedDateOf({ as_of: "2026-12-15", announced_date: "2026-11-02" }),
      "2026-11-02",
    );
    assert.equal(announcedDateOf({ as_of: null, announced_date: null }), null);
  });
});

describe("PortfolioCompare distribution tables", () => {
  it("keeps a 2025 prelim out of Upcoming on a 2026 visit", () => {
    const book = allocation([
      holding({
        ticker: "FIGFX",
        distributions: [
          {
            publication_stage: "preliminary_estimate",
            distribution_dollars: 2100,
            estimated_tax: 735,
            as_of: "2025-11-20",
            record_date: "2025-12-12",
            ex_date: "2025-12-15",
            payable_date: "2025-12-17",
          },
          {
            publication_stage: "preliminary_estimate",
            distribution_dollars: 4800,
            estimated_tax: 1680,
            as_of: "2026-08-15",
            record_date: "2026-12-12",
            ex_date: "2026-12-15",
            payable_date: "2026-12-17",
          },
        ],
      }),
    ]);

    const upcoming = upcomingRowsForSide(book, "current", TODAY);
    const paid = paidHistoryRowsForSide(book, "current", TODAY);

    assert.deepEqual(
      upcoming.map((item) => item.announcedDate),
      ["2026-08-15"],
    );
    assert.deepEqual(
      paid.map((item) => item.announcedDate),
      ["2025-11-20"],
    );
  });

  it("does not dump paid/final rows into the upcoming table", () => {
    const book = allocation([
      holding({
        ticker: "AGTHX",
        distributions: [
          {
            publication_stage: "preliminary_estimate",
            distribution_dollars: 4800,
            estimated_tax: 1680,
            as_of: "2026-12-15",
            record_date: "2026-12-16",
            ex_date: "2026-12-17",
            payable_date: "2026-12-18",
          },
          {
            publication_stage: "paid",
            distribution_dollars: 900,
            estimated_tax: 315,
            as_of: "2026-08-12",
            record_date: "2026-08-14",
            ex_date: "2026-08-15",
            payable_date: "2026-08-18",
          },
        ],
      }),
    ]);

    const upcoming = upcomingRowsForSide(book, "current", TODAY);
    const paid = paidHistoryRowsForSide(book, "current", TODAY);

    assert.deepEqual(
      upcoming.map((item) => item.stage),
      ["preliminary_estimate"],
    );
    assert.deepEqual(
      paid.map((item) => item.stage),
      ["paid"],
    );
    assert.equal(upcoming[0]?.announcedDate, "2026-12-15");
    assert.equal(upcoming[0]?.recordDate, "2026-12-16");
    assert.equal(upcoming[0]?.exDate, "2026-12-17");
    assert.equal(upcoming[0]?.payableDate, "2026-12-18");
    assert.equal(paid[0]?.announcedDate, "2026-08-12");
  });

  it("leaves missing dates as null instead of inventing them", () => {
    const book = allocation([
      holding({
        ticker: "DODIX",
        upcoming: {
          publication_stage: "monthly",
          distribution_dollars: 2100,
          estimated_tax: 777,
          as_of: null,
        },
      }),
    ]);
    const upcoming = upcomingRowsForSide(book, "current", TODAY);
    assert.equal(upcoming.length, 1);
    assert.equal(upcoming[0]?.announcedDate, null);
    assert.equal(upcoming[0]?.recordDate, null);
    assert.equal(upcoming[0]?.exDate, null);
    assert.equal(upcoming[0]?.payableDate, null);
  });

  it("keeps paid upcoming payloads out of tax-impact dollars", () => {
    const paidOnly = holding({
      ticker: "AGTHX",
      upcoming: {
        publication_stage: "paid",
        distribution_dollars: 900,
        estimated_tax: 315,
        as_of: "2026-08-12",
        record_date: "2026-08-14",
      },
    });
    assert.equal(upcomingFromHolding(paidOnly, TODAY), null);
    assert.equal(totalUpcomingTax(allocation([paidOnly])), 0);

    const prelim = holding({
      ticker: "AMCPX",
      upcoming: {
        publication_stage: "preliminary_estimate",
        distribution_dollars: 3200,
        estimated_tax: 1120,
        as_of: "2026-12-15",
      },
    });
    assert.equal(upcomingFromHolding(prelim)?.estimated_tax, 1120);
    assert.equal(totalUpcomingTax(allocation([prelim])), 1120);
  });

  it("does not derive table rows when upcoming is explicitly null", () => {
    const book = allocation([
      holding({
        ticker: "AGTHX",
        upcoming: null,
        illustration: {
          components: [
            {
              publication_stage: "preliminary_estimate",
              distribution_dollars: 4800,
              estimated_tax: 1680,
              as_of: "2026-12-15",
            },
          ],
        },
      }),
    ]);
    assert.equal(upcomingRowsForSide(book, "current").length, 0);
    assert.equal(upcomingFromHolding(book.holdings[0]), null);
  });
});
