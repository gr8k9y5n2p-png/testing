import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { toDataApiIllustrateBody } from "./compare-request.ts";
import {
  NEED_FUND_PRICE_COPY,
  NAV_OR_SHARES_REQUIRED_DETAIL,
  userFacingIllustrateError,
} from "./illustrate-error.ts";

const here = dirname(fileURLToPath(import.meta.url));

const SEED_NAV: Record<string, number> = {
  AGTHX: 72.14,
  VIGAX: 186.4,
};

function seedLookup(ticker: string): number | undefined {
  return SEED_NAV[ticker.toUpperCase()];
}

describe("toDataApiIllustrateBody NAV attach", () => {
  it("attaches seed NAV on the % of NAV / holding_dollars path", () => {
    const body = toDataApiIllustrateBody(
      {
        holding_dollars: 1_000_000,
        selector: {
          fund_family: "American Funds",
          fund_identifier: "AGTHX",
          ticker: "AGTHX",
        },
        nav_per_share: null,
      },
      seedLookup,
    );
    assert.equal(body.nav_per_share, 72.14);
    assert.equal(body.holding_dollars, 1_000_000);
  });

  it("keeps an explicit NAV and does not invent one for unknown tickers", () => {
    const withExplicit = toDataApiIllustrateBody(
      {
        holding_dollars: 1_000_000,
        selector: { ticker: "AGTHX", fund_identifier: "AGTHX" },
        nav_per_share: 80,
      },
      seedLookup,
    );
    assert.equal(withExplicit.nav_per_share, 80);

    const unknown = toDataApiIllustrateBody({
      holding_dollars: 1_000_000,
      selector: { ticker: "ZZNOPE", fund_identifier: "ZZNOPE" },
      nav_per_share: null,
    });
    assert.equal(unknown.nav_per_share, undefined);
  });

  it("stays aligned with SAMPLE_FUNDS NAV for AGTHX", () => {
    const body = toDataApiIllustrateBody(
      {
        holding_dollars: 1_000_000,
        selector: { ticker: "AGTHX", fund_identifier: "AGTHX" },
      },
      seedLookup,
    );
    assert.equal(body.nav_per_share, 72.14);
    const seed = readFileSync(join(here, "../../data/seed.ts"), "utf8");
    assert.match(seed, /ticker:\s*"AGTHX"[\s\S]*?nav:\s*72\.14/);
  });
});

describe("userFacingIllustrateError nav/shares", () => {
  it("maps needs_nav_or_shares and nav_required flags/codes", () => {
    assert.equal(
      userFacingIllustrateError({ needs_nav_or_shares: true }, "raw").message,
      NEED_FUND_PRICE_COPY,
    );
    assert.equal(
      userFacingIllustrateError({ nav_required: true, detail: "x" }, "raw").message,
      NEED_FUND_PRICE_COPY,
    );
    assert.equal(
      userFacingIllustrateError({ code: "nav_required", detail: "x" }, "raw")
        .message,
      NEED_FUND_PRICE_COPY,
    );
    assert.equal(
      userFacingIllustrateError(
        { detail: { needs_nav_or_shares: true } },
        "raw",
      ).message,
      NEED_FUND_PRICE_COPY,
    );
  });

  it("maps the known Data detail string", () => {
    const mapped = userFacingIllustrateError(
      { detail: NAV_OR_SHARES_REQUIRED_DETAIL },
      "Illustrate failed (422)",
    );
    assert.equal(mapped.message, NEED_FUND_PRICE_COPY);
  });

  it("leaves unrelated API errors unchanged", () => {
    const mapped = userFacingIllustrateError(
      { detail: "holding_dollars must be greater than 0", code: "invalid" },
      "fallback",
    );
    assert.equal(mapped.message, "holding_dollars must be greater than 0");
    assert.equal(mapped.code, "invalid");
  });
});
