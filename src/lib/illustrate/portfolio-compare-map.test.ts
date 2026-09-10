import assert from "node:assert/strict";
import { describe, it } from "node:test";
import type {
  PortfolioAllocationOut,
  PortfolioDistributionRow,
  PortfolioHoldingOut,
} from "./portfolio-compare-types.ts";
import {
  upcomingDistributionAmount,
  upcomingDistributionLine,
  upcomingDistributionPerShareAmount,
  upcomingEstimatedTaxLine,
  upcomingPctOfNavAmount,
} from "./portfolio-compare-copy.ts";
import {
  announcedDateOf,
  PAID_HISTORY_CAP,
  paidHistoryDateOf,
  paidHistoryRowsForSide,
  pctOfNavFromDist,
  publicationBucket,
  upcomingCutoverDateOf,
  totalUpcomingTax,
  upcomingFromHolding,
  upcomingHoldingsForSide,
  upcomingRowsForSide,
  withUpcomingNav,
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

  it("keeps paid and past finals in paid history", () => {
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
          publication_stage: "updated_estimate",
          as_of: "2025-11-02",
          record_date: "2025-12-12",
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

  it("keeps a future unpaid final in paid history, not upcoming", () => {
    assert.equal(
      publicationBucket(
        row({
          publication_stage: "final",
          as_of: "2026-08-15",
          record_date: "2026-12-12",
          ex_date: "2026-12-15",
          payable_date: "2026-12-17",
        }),
        TODAY,
      ),
      "paid_history",
    );
  });

  it("does not invent Upcoming from latest_as_of / identity-only rows", () => {
    assert.equal(
      publicationBucket(
        { as_of: "2025-12-31", publication_stage: null },
        TODAY,
      ),
      null,
    );
    assert.equal(
      publicationBucket(
        { as_of: "2025-12-24", publication_stage: "" },
        TODAY,
      ),
      null,
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

  it("moves unpaid announced to Paid History as soon as ex-date passes, not payable", () => {
    const pastExFuturePayable = row({
      publication_stage: "updated_estimate",
      as_of: "2026-08-12",
      record_date: "2026-09-01",
      ex_date: "2026-09-02",
      payable_date: "2026-12-18",
    });
    assert.equal(upcomingCutoverDateOf(pastExFuturePayable), "2026-09-02");
    assert.equal(publicationBucket(pastExFuturePayable, TODAY), "paid_history");
    assert.equal(
      publicationBucket(
        row({
          publication_stage: "preliminary_estimate",
          as_of: "2026-08-12",
          record_date: "2026-09-01",
          ex_date: "2026-09-15",
          payable_date: "2026-12-18",
        }),
        TODAY,
      ),
      "upcoming",
      "past record + future ex stays Upcoming until ex-date",
    );
    assert.equal(
      upcomingCutoverDateOf({
        ex_date: null,
        record_date: "2026-09-01",
        payable_date: "2026-12-18",
      }),
      "2026-09-01",
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
        upcoming: {
          publication_stage: "preliminary_estimate",
          distribution_dollars: 4800,
          estimated_tax: 1680,
          as_of: "2026-08-15",
          record_date: "2026-12-12",
          ex_date: "2026-12-15",
          payable_date: "2026-12-17",
        },
        paid_history: [
          {
            publication_stage: "preliminary_estimate",
            distribution_dollars: 2100,
            estimated_tax: 735,
            as_of: "2025-11-20",
            record_date: "2025-12-12",
            ex_date: "2025-12-15",
            payable_date: "2025-12-17",
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
        upcoming: {
          publication_stage: "preliminary_estimate",
          distribution_dollars: 4800,
          estimated_tax: 1680,
          as_of: "2026-12-15",
          record_date: "2026-12-16",
          ex_date: "2026-12-17",
          payable_date: "2026-12-18",
        },
        paid_history: [
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

  it("lists a past-dated preliminary estimate from paid_history, not distributions", () => {
    const book = allocation([
      holding({
        ticker: "AGTHX",
        upcoming: null,
        paid_history: [
          {
            publication_stage: "preliminary_estimate",
            distribution_dollars: 4800,
            estimated_tax: 1680,
            as_of: "2025-11-02",
            record_date: "2025-12-12",
            ex_date: "2025-12-15",
            payable_date: "2025-12-17",
          },
        ],
      }),
    ]);
    const upcoming = upcomingRowsForSide(book, "current", TODAY);
    const paid = paidHistoryRowsForSide(book, "current", TODAY);
    assert.equal(upcoming.length, 0);
    assert.equal(paid.length, 1);
    assert.equal(paid[0]?.announcedDate, "2025-11-02");
    assert.equal(paid[0]?.recordDate, "2025-12-12");
    assert.equal(paid[0]?.stage, "preliminary_estimate");
  });

  it("uses live upcoming record/ex/payable dates when distributions omit them", () => {
    const book = allocation([
      holding({
        ticker: "AGTHX",
        upcoming: {
          publication_stage: "preliminary_estimate",
          distribution_dollars: 4800,
          estimated_tax: 1680,
          as_of: "2026-09-19",
          announced_date: "2026-09-19",
          record_date: "2026-09-22",
          ex_date: "2026-09-23",
          payable_date: "2026-09-25",
        },
        distributions: [
          {
            publication_stage: "preliminary_estimate",
            distribution_dollars: 4800,
            estimated_tax: 1680,
            as_of: "2026-09-19",
          },
        ],
      }),
    ]);
    const upcoming = upcomingRowsForSide(book, "current", TODAY);
    assert.equal(upcoming.length, 1);
    assert.equal(upcoming[0]?.announcedDate, "2026-09-19");
    assert.equal(upcoming[0]?.recordDate, "2026-09-22");
    assert.equal(upcoming[0]?.exDate, "2026-09-23");
    assert.equal(upcoming[0]?.payableDate, "2026-09-25");
  });

  it("adds a live upcoming row when distributions are only paid history", () => {
    const book = allocation([
      holding({
        ticker: "AMCPX",
        upcoming: {
          publication_stage: "updated_estimate",
          distribution_dollars: 3200,
          estimated_tax: 1120,
          as_of: "2026-09-19",
          record_date: null,
          ex_date: "2026-09-23",
          payable_date: null,
        },
        paid_history: [
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
        distributions: [
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
    assert.equal(upcoming.length, 1);
    assert.equal(upcoming[0]?.announcedDate, "2026-09-19");
    assert.equal(upcoming[0]?.recordDate, null);
    assert.equal(upcoming[0]?.exDate, "2026-09-23");
    assert.equal(upcoming[0]?.payableDate, null);
    assert.equal(paid.length, 1);
    assert.equal(paid[0]?.payableDate, "2026-08-18");
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

    const pastPrelim = holding({
      ticker: "AGTHX",
      upcoming: {
        publication_stage: "preliminary_estimate",
        distribution_dollars: 4800,
        estimated_tax: 1680,
        as_of: "2025-11-02",
        record_date: "2025-12-12",
      },
    });
    assert.equal(upcomingFromHolding(pastPrelim, TODAY), null);
    assert.equal(totalUpcomingTax(allocation([pastPrelim])), 0);

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

  it("does not invent Upcoming from omitted holdings.upcoming + illustration totals", () => {
    for (const ticker of ["AMCPX", "ABALX", "VFIAX", "FXAIX", "ZZZZX"]) {
      const omitted = holding({
        ticker,
        illustration: {
          totals: {
            distribution_dollars: 1491,
            estimated_tax: 522,
            effective_tax_on_holding: 0.0021,
          },
          components: [
            {
              publication_stage: "preliminary_estimate",
              distribution_dollars: 1491,
              estimated_tax: 522,
              as_of: "2025-12-15",
            },
          ],
        },
      });
      assert.equal(Object.prototype.hasOwnProperty.call(omitted, "upcoming"), false);
      assert.equal(upcomingFromHolding(omitted, TODAY), null);
      assert.equal(totalUpcomingTax(allocation([omitted])), 0);
      const rows = upcomingHoldingsForSide(allocation([omitted]), "current", TODAY);
      assert.equal(rows.length, 1);
      assert.equal(rows[0]?.available, false);
      assert.equal(rows[0]?.distributionDollars, null);
      assert.equal(rows[0]?.estimatedTax, null);
      assert.equal(upcomingRowsForSide(allocation([omitted]), "current", TODAY).length, 0);
    }
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
    assert.equal(paidHistoryRowsForSide(book, "current", TODAY).length, 0);
  });

  it("lists paid_history when Data nulls upcoming after the unpaid gate", () => {
    const book = allocation([
      holding({
        ticker: "AMCAP",
        upcoming: null,
        paid_history: [
          {
            publication_stage: "paid",
            distribution_dollars: 1050,
            estimated_tax: 368,
            as_of: "2025-12-15",
            record_date: "2025-12-12",
            ex_date: "2025-12-15",
            payable_date: "2025-12-17",
          },
        ],
        illustration: {
          totals: {
            distribution_dollars: 1050,
            estimated_tax: 1050,
            effective_tax_on_holding: 0.0042,
          },
        },
      }),
    ]);
    book.totals = {
      distribution_dollars: 1050,
      estimated_tax: 4200,
      effective_tax_on_holding: 0.0042,
    };

    const upcoming = upcomingRowsForSide(book, "current", TODAY);
    const paid = paidHistoryRowsForSide(book, "current", TODAY);

    assert.equal(upcoming.length, 0);
    assert.equal(paid.length, 1);
    assert.equal(paid[0]?.ticker, "AMCAP");
    assert.equal(paid[0]?.recordDate, "2025-12-12");
    assert.equal(paid[0]?.exDate, "2025-12-15");
    assert.equal(paid[0]?.payableDate, "2025-12-17");
    assert.equal(paid[0]?.announcedDate, "2025-12-15");
    assert.equal(book.totals.effective_tax_on_holding, 0.0042);
    assert.equal(book.totals.estimated_tax, 4200);
  });

  it("ignores illustration.components when paid_history is present", () => {
    const book = allocation([
      holding({
        ticker: "AGTHX",
        upcoming: null,
        paid_history: [
          {
            publication_stage: "final",
            distribution_dollars: 900,
            estimated_tax: 315,
            as_of: "2026-08-12",
            record_date: "2026-08-14",
            ex_date: "2026-08-15",
            payable_date: "2026-08-18",
          },
        ],
        illustration: {
          components: [
            {
              publication_stage: "paid",
              distribution_dollars: 50,
              estimated_tax: 10,
              as_of: "2025-01-02",
              record_date: "2025-01-03",
            },
          ],
        },
      }),
    ]);
    const paid = paidHistoryRowsForSide(book, "current", TODAY);
    assert.equal(paid.length, 1);
    assert.equal(paid[0]?.distributionDollars, 900);
    assert.equal(paid[0]?.stage, "final");
  });

  it("does not derive Paid History from illustration.components", () => {
    const book = allocation([
      holding({
        ticker: "DODGX",
        upcoming: null,
        illustration: {
          components: [
            {
              publication_stage: "paid",
              distribution_dollars: 2100,
              estimated_tax: 735,
              as_of: "2026-08-12",
              record_date: "2026-08-14",
              ex_date: "2026-08-15",
              payable_date: "2026-08-18",
            },
            {
              publication_stage: "preliminary_estimate",
              distribution_dollars: 4800,
              estimated_tax: 1680,
              as_of: "2026-12-15",
              record_date: "2026-12-16",
            },
          ],
        },
      }),
    ]);
    const upcoming = upcomingRowsForSide(book, "current", TODAY);
    const paid = paidHistoryRowsForSide(book, "current", TODAY);
    assert.equal(upcoming.length, 0);
    assert.equal(paid.length, 0);
  });

  it("does not derive Paid History from distributions when paid_history is omitted", () => {
    const book = allocation([
      holding({
        ticker: "AMCPX",
        upcoming: null,
        distributions: [
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
    assert.equal(upcomingRowsForSide(book, "current", TODAY).length, 0);
    assert.equal(paidHistoryRowsForSide(book, "current", TODAY).length, 0);
  });

  it("sorts paid history newest first and leaves missing dates null", () => {
    const book = allocation([
      holding({
        ticker: "AGTHX",
        upcoming: null,
        paid_history: [
          {
            publication_stage: "paid",
            distribution_dollars: 400,
            estimated_tax: 140,
            as_of: "2025-06-01",
            record_date: "2025-06-12",
            ex_date: null,
            payable_date: null,
          },
          {
            publication_stage: "final",
            distribution_dollars: 800,
            estimated_tax: 280,
            as_of: "2025-12-15",
            record_date: "2025-12-12",
            ex_date: "2025-12-15",
            payable_date: "2025-12-17",
          },
          {
            publication_stage: "paid",
            distribution_dollars: 200,
            estimated_tax: 70,
            as_of: null,
            record_date: null,
            ex_date: null,
            payable_date: null,
          },
        ],
      }),
    ]);
    const paid = paidHistoryRowsForSide(book, "current", TODAY);
    assert.deepEqual(
      paid.map((item) => item.distributionDollars),
      [800, 400, 200],
    );
    assert.equal(paid[0]?.recordDate, "2025-12-12");
    assert.equal(paid[1]?.exDate, null);
    assert.equal(paid[1]?.payableDate, null);
    assert.equal(paid[2]?.recordDate, null);
    assert.equal(paid[2]?.announcedDate, null);
    assert.equal(
      paidHistoryDateOf({
        record_date: "2025-12-12",
        ex_date: "2025-12-15",
        payable_date: "2025-12-17",
      }),
      "2025-12-12",
    );
  });

  it("lists six AMCPX/AGTHX paid_history rows when upcoming is null", () => {
    const six = () =>
      Array.from({ length: 6 }, (_, index) => ({
        publication_stage: "paid" as const,
        distribution_dollars: 100 * (index + 1),
        estimated_tax: 35 * (index + 1),
        as_of: `202${index}-12-15`,
        record_date: `202${index}-12-12`,
        ex_date: `202${index}-12-15`,
        payable_date: `202${index}-12-17`,
      }));

    const book = allocation([
      holding({ ticker: "AMCPX", upcoming: null, paid_history: six() }),
      holding({
        ticker: "AGTHX",
        holding_index: 1,
        upcoming: null,
        paid_history: six(),
      }),
    ]);
    const paid = paidHistoryRowsForSide(book, "current", TODAY);
    assert.equal(upcomingRowsForSide(book, "current", TODAY).length, 0);
    assert.equal(paid.filter((row) => row.ticker === "AMCPX").length, 6);
    assert.equal(paid.filter((row) => row.ticker === "AGTHX").length, 6);
    for (const row of paid) {
      assert.ok(row.recordDate);
      assert.ok(row.exDate);
      assert.ok(row.payableDate);
      assert.ok(row.estimatedTax != null && row.estimatedTax > 0);
    }
  });

  it("caps paid_history at Data's 12-row newest-first window", () => {
    const paid_history = Array.from({ length: 15 }, (_, index) => ({
      publication_stage: "paid" as const,
      distribution_dollars: index + 1,
      estimated_tax: (index + 1) * 10,
      as_of: `2020-01-${String(index + 1).padStart(2, "0")}`,
      record_date: `2020-01-${String(index + 1).padStart(2, "0")}`,
    }));
    const book = allocation([
      holding({ ticker: "AGTHX", upcoming: null, paid_history }),
    ]);
    const paid = paidHistoryRowsForSide(book, "current", TODAY);
    assert.equal(PAID_HISTORY_CAP, 12);
    assert.equal(paid.length, 12);
    assert.equal(paid[0]?.recordDate, "2020-01-15");
    assert.equal(paid[11]?.recordDate, "2020-01-04");
  });

  it("lists every Current/Proposed fund when upcoming is empty, as undisclosed not $0", () => {
    const book = allocation([
      holding({ ticker: "AGTHX", upcoming: null }),
      holding({ ticker: "DODIX", holding_index: 1, upcoming: null }),
      holding({
        ticker: "AMCAP",
        holding_index: 2,
        nav_per_share: 41.22,
        upcoming: {
          publication_stage: "preliminary_estimate",
          distribution_dollars: 3200,
          estimated_tax: 1120,
          percent_of_nav: 1.28,
          record_date: "2026-09-19",
          ex_date: "2026-09-20",
        },
      }),
      holding({ ticker: "DODGX", holding_index: 3, covered: false, gap_reason: "gap" }),
    ]);
    const rows = upcomingHoldingsForSide(book, "current", TODAY);
    assert.deepEqual(
      rows.map((row) => row.ticker),
      ["AGTHX", "DODIX", "AMCAP", "DODGX"],
    );
    assert.equal(rows[0]?.available, false);
    assert.equal(rows[0]?.distributionDollars, null);
    assert.equal(rows[0]?.estimatedTax, null);
    assert.equal(rows[1]?.available, false);
    assert.equal(rows[2]?.available, true);
    assert.equal(rows[2]?.distributionDollars, 3200);
    assert.equal(rows[2]?.estimatedTax, 1120);
    assert.equal(rows[2]?.holdingDollars, 250_000);
    assert.ok(rows[2]?.pctOfNav != null);
    assert.equal(Number(rows[2]?.pctOfNav?.toFixed(2)), 1.28);
    assert.equal(rows[2]?.recordDate, "2026-09-19");
    assert.equal(rows[2]?.exDate, "2026-09-20");
    assert.equal(rows[3]?.available, false);
    assert.equal(rows[3]?.covered, false);
    assert.equal(rows[0]?.inUniverse, true);
    assert.equal(
      upcomingHoldingsForSide(book, "current", TODAY, new Set(["AGTHX", "DODIX", "AMCAP"]))[3]
        ?.inUniverse,
      false,
    );
    assert.equal(upcomingRowsForSide(book, "current", TODAY).length, 1);
  });

  it("keeps one Upcoming row per holding when a fund has two unpaid events", () => {
    const book = allocation([
      holding({
        ticker: "AGTHX",
        upcoming: [
          {
            publication_stage: "preliminary_estimate",
            distribution_dollars: 4800,
            estimated_tax: 1680,
            record_date: "2026-12-16",
            ex_date: "2026-12-17",
          },
          {
            publication_stage: "updated_estimate",
            distribution_dollars: 500,
            estimated_tax: 175,
            record_date: "2026-11-16",
            ex_date: "2026-11-17",
          },
        ],
      }),
    ]);
    const rows = upcomingHoldingsForSide(book, "current", TODAY);
    assert.equal(rows.length, 1);
    assert.equal(rows[0]?.ticker, "AGTHX");
    assert.equal(rows[0]?.available, true);
  });

  it("formats stacked ticker lines as Awaiting Estimate / N/A instead of $0", () => {
    assert.equal(
      upcomingDistributionLine({ available: false, distributionDollars: null }),
      "Est. Distribution: Awaiting Estimate",
    );
    assert.equal(
      upcomingEstimatedTaxLine({
        available: false,
        covered: true,
        estimatedTax: null,
      }),
      "Estimated Tax: Awaiting Estimate",
    );
    assert.doesNotMatch(
      upcomingDistributionLine({ available: false, distributionDollars: null }),
      /\$0/,
    );
    assert.equal(
      upcomingDistributionLine({ available: true, distributionDollars: 3200 }),
      "Est. Distribution: $3,200",
    );
    assert.equal(
      upcomingEstimatedTaxLine({
        available: true,
        covered: true,
        estimatedTax: 1120,
      }),
      "Estimated Tax: $1,120",
    );
    assert.equal(
      upcomingEstimatedTaxLine({
        available: true,
        covered: false,
        estimatedTax: 0,
      }),
      "Estimated Tax: —",
    );
    assert.equal(
      upcomingPctOfNavAmount({ available: true, pctOfNav: 1.28 }),
      "1.28%",
    );
    assert.equal(
      upcomingPctOfNavAmount({ available: false, pctOfNav: null }),
      "Awaiting Estimate",
    );
    assert.equal(
      upcomingPctOfNavAmount({
        available: false,
        inUniverse: false,
        pctOfNav: null,
      }),
      "Add to universe",
    );
  });

  it("keeps unpaid announced $0 until ex-date, then moves it to Paid History", () => {
    const announcedZero = {
      publication_stage: "preliminary_estimate" as const,
      amount: 0,
      amount_unit: "per_share",
      distribution_dollars: 0,
      estimated_tax: 0,
      announced_date: "2026-08-12",
      record_date: "2026-09-01",
      payable_date: "2026-12-18",
    };
    const stillUpcoming = allocation([
      holding({
        ticker: "ZEROX",
        upcoming: { ...announcedZero, ex_date: "2026-09-15" },
      }),
    ]);
    const upcoming = upcomingHoldingsForSide(stillUpcoming, "current", TODAY);
    assert.equal(upcoming[0]?.available, true);
    assert.equal(upcoming[0]?.distributionPerShare, 0);
    assert.equal(upcoming[0]?.distributionDollars, 0);

    const afterEx = allocation([
      holding({
        ticker: "ZEROX",
        upcoming: { ...announcedZero, ex_date: "2026-09-02" },
      }),
    ]);
    const past = upcomingHoldingsForSide(afterEx, "current", TODAY);
    assert.equal(past[0]?.available, false);
    assert.equal(upcomingRowsForSide(afterEx, "current", TODAY).length, 0);
    assert.equal(paidHistoryRowsForSide(afterEx, "current", TODAY).length, 0);
  });

  it("keeps unpaid manager-announced $0 amount and Dist $", () => {
    const book = allocation([
      holding({
        ticker: "ZEROX",
        upcoming: {
          publication_stage: "preliminary_estimate",
          amount: 0,
          amount_unit: "per_share",
          distribution_dollars: 0,
          estimated_tax: 0,
          announced_date: "2026-09-01",
          record_date: "2026-12-16",
          ex_date: "2026-12-17",
        },
      }),
    ]);
    const rows = upcomingHoldingsForSide(book, "current", TODAY);
    assert.equal(rows[0]?.available, true);
    assert.equal(rows[0]?.distributionDollars, 0);
    assert.equal(rows[0]?.distributionPerShare, 0);
    assert.equal(rows[0]?.estimatedTax, 0);
    assert.equal(rows[0]?.announcedDate, "2026-09-01");
    assert.equal(
      upcomingDistributionAmount({
        available: true,
        distributionDollars: rows[0]?.distributionDollars ?? null,
      }),
      "$0",
    );
    assert.equal(
      upcomingDistributionPerShareAmount({
        available: true,
        distributionPerShare: rows[0]?.distributionPerShare,
        distributionDollars: rows[0]?.distributionDollars ?? null,
        holdingDollars: rows[0]?.holdingDollars ?? null,
        navPerShare: rows[0]?.navPerShare ?? null,
      }),
      "$0.0000 / sh",
    );
  });

  it("keeps announced rows with dates when Dist $ is still undisclosed", () => {
    const book = allocation([
      holding({
        ticker: "AMCPX",
        upcoming: {
          publication_stage: "preliminary_estimate",
          announced_date: "2026-09-01",
          record_date: "2026-12-16",
          ex_date: "2026-12-17",
          distribution_dollars: null,
          estimated_tax: null,
        },
      }),
    ]);
    const rows = upcomingHoldingsForSide(book, "current", TODAY);
    assert.equal(rows[0]?.available, true);
    assert.equal(rows[0]?.distributionDollars, null);
    assert.equal(rows[0]?.pctOfNav, null);
    assert.equal(rows[0]?.announcedDate, "2026-09-01");
    assert.equal(rows[0]?.recordDate, "2026-12-16");
    assert.equal(rows[0]?.exDate, "2026-12-17");
    assert.doesNotMatch(
      upcomingDistributionLine({
        available: true,
        distributionDollars: rows[0]?.distributionDollars ?? null,
      }),
      /\$0/,
    );
  });

  it("uses Dist $/share ÷ weekly NAV for unpaid Upcoming, never day NAV", () => {
    const book = allocation([
      holding({
        ticker: "FCPGX",
        nav_per_share: 42.94,
        upcoming: {
          publication_stage: "preliminary_estimate",
          per_share: 7.277,
          amount: 7.277,
          amount_unit: "per_share",
          percent_of_nav: 12,
          nav_on_distribution_day: 37.09,
          distribution_dollars: null,
          record_date: "2026-12-12",
          ex_date: "2026-12-15",
        },
      }),
    ]);
    const rows = upcomingHoldingsForSide(book, "current", TODAY);
    assert.equal(rows[0]?.available, true);
    assert.equal(rows[0]?.distributionPerShare, 7.277);
    assert.equal(rows[0]?.navPerShare, 42.94);
    assert.equal(rows[0]?.navOnDistributionDay, 37.09);
    assert.equal(Number(rows[0]?.pctOfNav?.toFixed(1)), 16.9);
    assert.notEqual(Number(rows[0]?.pctOfNav?.toFixed(1)), 12);
    assert.equal(
      upcomingPctOfNavAmount({
        available: true,
        pctOfNav: rows[0]?.pctOfNav ?? null,
        distributionPerShare: 7.277,
        navPerShare: 42.94,
      }),
      "16.95%",
    );
  });

  it("uses Dist $/share ÷ nav_on_distribution_day for paid history, never weekly", () => {
    const book = allocation([
      holding({
        ticker: "ABALX",
        nav_per_share: 40.849998,
        paid_history: [
          {
            publication_stage: "paid",
            per_share: 2.125,
            amount: 2.125,
            amount_unit: "per_share",
            nav_per_share: 40.849998,
            nav_on_distribution_day: 37.09,
            distribution_dollars: 2100,
            as_of: "2025-12-15",
            record_date: "2025-12-15",
            ex_date: "2025-12-15",
            payable_date: "2025-12-16",
          },
        ],
      }),
    ]);
    const paid = paidHistoryRowsForSide(book, "current", TODAY);
    assert.equal(paid.length, 1);
    assert.equal(paid[0]?.bucket, "paid_history");
    assert.equal(paid[0]?.distributionPerShare, 2.125);
    assert.equal(paid[0]?.navPerShare, 40.849998);
    assert.equal(paid[0]?.navOnDistributionDay, 37.09);
    assert.equal(Number(paid[0]?.pctOfNav?.toFixed(2)), 5.73);
    assert.notEqual(
      Number(paid[0]?.pctOfNav?.toFixed(2)),
      Number((((2.125 / 40.849998) * 100).toFixed(2))),
      "paid % of NAV must not use weekly nav_per_share",
    );

    const rewritten = withUpcomingNav(paid, { ABALX: 40.849998 });
    assert.equal(Number(rewritten[0]?.pctOfNav?.toFixed(2)), 5.73);
    assert.equal(rewritten[0]?.navOnDistributionDay, 37.09);
  });

  it("leaves paid % of NAV null when day NAV is missing — never weekly fallback", () => {
    const book = allocation([
      holding({
        ticker: "ABALX",
        nav_per_share: 40.85,
        paid_history: [
          {
            publication_stage: "final",
            per_share: 2.125,
            amount_unit: "per_share",
            nav_per_share: 40.85,
            as_of: "2025-12-15",
            ex_date: "2025-12-15",
          },
        ],
      }),
    ]);
    const paid = paidHistoryRowsForSide(book, "current", TODAY);
    assert.equal(paid[0]?.pctOfNav, null);
  });

  it("uses issuer-published percent_of_nav only and never derives a rate", () => {
    assert.equal(pctOfNavFromDist(3200, 250_000), null);
    assert.equal(pctOfNavFromDist(3200, 250_000, 2.5), 2.5);
    assert.equal(pctOfNavFromDist(null, 250_000), null);
    assert.equal(pctOfNavFromDist(3200, null), null);
    assert.equal(pctOfNavFromDist(3200, 0), null);
  });
});
