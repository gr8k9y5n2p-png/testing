import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  compareSelectorsFromFund,
  compareSideFromFund,
  compareTaxRequestFields,
  illustrationRequestNav,
  navFromFundMetadata,
  PER_SHARE_NAV_REQUIRED,
  perShareNavError,
  positiveNav,
  toDataApiCompareBody,
  toDataApiTaxRates,
  trailingCalendarPeriods,
  withPortfolioHoldingNav,
  yoyTaxDragCompareRequest,
} from "./compare-request.ts";
import { LOCKED_TAX_RATE_KEYS, lockedTaxRates, UI_DEFAULT_TAX_RATES } from "./types.ts";

const here = dirname(fileURLToPath(import.meta.url));

/** Seed NAVs for the Engineering | Data AGTHX vs VIGAX pair. */
const SEED_NAV: Record<string, number> = {
  AGTHX: 72.14,
  VIGAX: 186.4,
  AMCPX: 41.22,
};

function seedLookup(ticker: string): number | undefined {
  return SEED_NAV[ticker.toUpperCase()];
}

describe("compare-request NAV / Data body", () => {
  it("treats only values > 0 as NAV", () => {
    assert.equal(positiveNav(72.14), 72.14);
    assert.equal(positiveNav(0), undefined);
    assert.equal(positiveNav(-1), undefined);
    assert.equal(positiveNav(null), undefined);
    assert.equal(positiveNav(""), undefined);
  });

  it("uses search metadata first, then the ticker lookup", () => {
    assert.equal(navFromFundMetadata("AGTHX", 80, seedLookup), 80);
    assert.equal(navFromFundMetadata("AGTHX", 0, seedLookup), 72.14);
    assert.equal(navFromFundMetadata("vigax", undefined, seedLookup), 186.4);
    assert.equal(navFromFundMetadata("ZZNOPE", undefined, seedLookup), undefined);
  });

  it("auto-attaches ABALX $/share NAV from metadata when catalog nav is 0", () => {
    const abalxLookup = (ticker: string) =>
      ticker.toUpperCase() === "ABALX" ? 34.52 : undefined;
    const attached = illustrationRequestNav("", "ABALX", 0, abalxLookup);
    assert.equal(attached, 34.52);
    assert.equal(perShareNavError("per_share", attached), null);
    assert.equal(
      illustrationRequestNav("36.10", "ABALX", 0, abalxLookup),
      36.1,
    );
    const missing = illustrationRequestNav("", "ZZNOPE", 0);
    assert.equal(missing, undefined);
    assert.equal(perShareNavError("per_share", missing), PER_SHARE_NAV_REQUIRED);
    assert.equal(perShareNavError("percent_of_nav", missing), null);
  });

  it("builds a compare side with nav_per_share from fund metadata", () => {
    const side = compareSideFromFund(
      {
        ticker: "AGTHX",
        fundName: "The Growth Fund of America",
        family: "American Funds",
        nav: 0,
      },
      seedLookup,
    );
    assert.equal(side.selectors?.ticker, "AGTHX");
    assert.equal(side.nav_per_share, 72.14);
  });

  it("attaches seed NAV for AGTHX vs VIGAX when callers omit nav_per_share", () => {
    const body = toDataApiCompareBody(
      {
        mode: "fund_vs_fund",
        holding_dollars: 10_000,
        left: {
          label: "AGTHX",
          selectors: { ticker: "AGTHX", fund_identifier: "AGTHX" },
        },
        right: {
          label: "VIGAX",
          selectors: { ticker: "VIGAX", fund_identifier: "VIGAX" },
        },
      },
      seedLookup,
    );
    assert.equal(body.left?.nav_per_share, 72.14);
    assert.equal(body.right?.nav_per_share, 186.4);
    assert.equal(body.nav_per_share, undefined);
  });

  it("keeps an explicit per-side NAV and does not copy it to the peer", () => {
    const body = toDataApiCompareBody(
      {
        mode: "fund_vs_fund",
        holding_dollars: 10_000,
        left: {
          selectors: { ticker: "AGTHX" },
          nav_per_share: 100,
        },
        right: {
          selectors: { ticker: "VIGAX" },
          nav_per_share: 200,
        },
      },
      seedLookup,
    );
    assert.equal(body.left?.nav_per_share, 100);
    assert.equal(body.right?.nav_per_share, 200);
  });

  it("omits nav for unknown tickers so the request is holding_dollars-only", () => {
    const body = toDataApiCompareBody({
      mode: "fund_vs_fund",
      holding_dollars: 10_000,
      nav_per_share: 0,
      left: { selectors: { ticker: "ZZNOPE" }, nav_per_share: 0 },
      right: { selectors: { ticker: "YYNOPE" } },
    });
    assert.equal(body.left?.nav_per_share, undefined);
    assert.equal(body.right?.nav_per_share, undefined);
    assert.equal(body.nav_per_share, undefined);
  });

  it("stays aligned with SAMPLE_FUNDS NAVs for AGTHX and VIGAX", () => {
    const seed = readFileSync(join(here, "../../data/seed.ts"), "utf8");
    assert.match(seed, /ticker:\s*"AGTHX"[\s\S]*?nav:\s*72\.14/);
    assert.match(seed, /ticker:\s*"VIGAX"[\s\S]*?nav:\s*186\.4/);
  });

  it("fills YoY top-level and left NAV from metadata", () => {
    const body = toDataApiCompareBody(
      {
        mode: "yoy",
        holding_dollars: 10_000,
        selectors: { ticker: "AGTHX", fund_identifier: "AGTHX" },
        left: {
          label: "AGTHX",
          selectors: { ticker: "AGTHX", fund_identifier: "AGTHX" },
        },
        periods: [{ year: 2024 }, { year: 2025 }],
      },
      seedLookup,
    );
    assert.equal(body.nav_per_share, 72.14);
    assert.equal(body.left?.nav_per_share, 72.14);
  });

  it("attaches portfolio holding NAV from search/seed and omits 0", () => {
    const lookup = (ticker: string) =>
      ({ AGTHX: 72.14, DODIX: 12.8, AMCAP: 41.22, DODGX: 273.16, CGHM: 25.18 }[
        ticker.toUpperCase()
      ]);
    assert.equal(
      withPortfolioHoldingNav({ ticker: "AGTHX", nav_per_share: 0 }, lookup).nav_per_share,
      72.14,
    );
    assert.equal(
      withPortfolioHoldingNav({ ticker: "DODIX" }, lookup).nav_per_share,
      12.8,
    );
    assert.equal(
      withPortfolioHoldingNav({ ticker: "AMCAP" }, lookup).nav_per_share,
      41.22,
    );
    assert.equal(
      withPortfolioHoldingNav({ ticker: "CGHM", nav_per_share: 0 }, lookup).nav_per_share,
      25.18,
    );
    assert.equal(
      withPortfolioHoldingNav({ ticker: "ZZNOPE", nav_per_share: 0 }, lookup).nav_per_share,
      undefined,
    );
  });

  it("replaces a catalog AGTHX fund_name with the seed product name Data can AND", () => {
    const names: Record<string, string> = {
      AGTHX: "The Growth Fund of America",
      AMCPX: "AMCAP Fund",
    };
    const nameLookup = (ticker: string) => names[ticker.toUpperCase()];
    assert.equal(
      withPortfolioHoldingNav(
        { ticker: "AGTHX", fund_name: "American Funds Growth Fund of America" },
        seedLookup,
        nameLookup,
      ).fund_name,
      "The Growth Fund of America",
    );
    assert.equal(
      withPortfolioHoldingNav(
        { ticker: "AMCPX", fund_name: "AMCPX" },
        seedLookup,
        nameLookup,
      ).fund_name,
      "AMCAP Fund",
    );
    assert.equal(
      withPortfolioHoldingNav({ ticker: "DODIX", fund_name: "DODIX" }, seedLookup).fund_name,
      undefined,
    );
    assert.equal(
      withPortfolioHoldingNav(
        { ticker: "DODIX", fund_name: "Dodge & Cox Income Fund" },
        seedLookup,
      ).fund_name,
      "Dodge & Cox Income Fund",
    );
  });

  it("omits fund_name when it is just the ticker (Data ANDs fund_name)", () => {
    assert.equal(
      compareSelectorsFromFund({ ticker: "AMCPX", fundName: "AMCPX" }).fund_name,
      undefined,
    );
    assert.equal(
      compareSelectorsFromFund({ ticker: "AGTHX", fundName: "agthx" }).fund_name,
      undefined,
    );
    assert.equal(
      compareSelectorsFromFund({
        ticker: "AGTHX",
        fundName: "The Growth Fund of America",
        family: "American Funds",
      }).fund_name,
      undefined,
    );
    assert.equal(
      compareSelectorsFromFund({
        ticker: "AGTHX",
        fundName: "American Funds Growth Fund of America",
        family: "American Funds",
      }).fund_name,
      undefined,
    );
    const stripped = toDataApiCompareBody({
      mode: "yoy",
      holding_dollars: 10_000,
      selectors: {
        ticker: "AMCPX",
        fund_identifier: "AMCPX",
        fund_name: "AMCPX",
      },
      left: {
        label: "AMCPX",
        selectors: {
          ticker: "AMCPX",
          fund_identifier: "AMCPX",
          fund_name: "AMCPX",
        },
      },
      periods: [{ year: 2021 }, { year: 2025 }],
    });
    assert.equal(stripped.selectors?.fund_name, undefined);
    assert.equal(stripped.left?.selectors?.fund_name, undefined);
    assert.equal(stripped.selectors?.ticker, "AMCPX");
  });

  it("builds a homepage AMCPX YoY body without ticker-as-fund_name", () => {
    const years = [2021, 2022, 2023, 2024, 2025];
    const request = yoyTaxDragCompareRequest({
      ticker: "AMCPX",
      label: "AMCPX",
      fundFamily: "American Funds",
      fundName: "AMCPX",
      holdingDollars: 10_000,
      navPerShare: 41.22,
      periods: years.map((year) => ({ year })),
    });
    const body = toDataApiCompareBody(request, seedLookup);
    assert.equal(body.mode, "yoy");
    assert.equal(body.selectors?.ticker, "AMCPX");
    assert.equal(body.selectors?.fund_identifier, "AMCPX");
    assert.equal(body.selectors?.fund_family, "American Funds");
    assert.equal(body.selectors?.fund_name, undefined);
    assert.equal(body.left?.selectors?.fund_name, undefined);
    assert.equal(body.nav_per_share, 41.22);
    assert.deepEqual(request.tax_rates, UI_DEFAULT_TAX_RATES);
    assert.equal(request.combine_state_with_federal, true);
    assert.deepEqual(
      body.periods?.map((period) => period.year),
      years,
    );
  });

  it("expands abbreviated tax_rates to the locked five keys", () => {
    assert.deepEqual([...LOCKED_TAX_RATE_KEYS], [
      "ordinary_income",
      "long_term_capital_gains",
      "short_term_capital_gains",
      "qualified_dividend",
      "state",
    ]);
    const expanded = lockedTaxRates({ state: 0.05 });
    assert.deepEqual(expanded, UI_DEFAULT_TAX_RATES);
    const body = toDataApiCompareBody({
      mode: "yoy",
      holding_dollars: 10_000,
      tax_rates: { state: 0.05 },
      selectors: { ticker: "AGTHX", fund_identifier: "AGTHX" },
      periods: trailingCalendarPeriods(),
    });
    assert.deepEqual(body.tax_rates, UI_DEFAULT_TAX_RATES);
    assert.deepEqual(
      body.periods?.map((period) => period.year),
      [2021, 2022, 2023, 2024, 2025],
    );
    for (const key of LOCKED_TAX_RATE_KEYS) {
      assert.equal(typeof body.tax_rates?.[key], "number");
    }
  });

  it("maps rate-strip aliases onto Data API tax_rates keys", () => {
    assert.deepEqual(
      toDataApiTaxRates({
        ordinary: 0.24,
        ltcg: 0.15,
        stcg: 0.32,
        qdi: 0.18,
        state: 0.1,
      }),
      {
        ordinary_income: 0.24,
        long_term_capital_gains: 0.15,
        short_term_capital_gains: 0.32,
        qualified_dividend: 0.18,
        state: 0.1,
      },
    );
    assert.deepEqual(
      toDataApiTaxRates({
        ordinary: 0.1,
        ordinary_income: 0.37,
        extra: 0.99,
      }),
      {
        ...UI_DEFAULT_TAX_RATES,
        ordinary_income: 0.37,
      },
    );
    assert.deepEqual(toDataApiTaxRates({}), UI_DEFAULT_TAX_RATES);
    assert.equal(
      Object.keys(toDataApiTaxRates({ ordinary: 0.24, ltcg: 0.15 })).join(","),
      "ordinary_income,long_term_capital_gains,short_term_capital_gains,qualified_dividend,state",
    );
  });

  it("defaults compare tax fields to the locked top-bracket UI set", () => {
    assert.deepEqual(compareTaxRequestFields({ taxRates: { state: 0.05 } }), {
      tax_rates: UI_DEFAULT_TAX_RATES,
      combine_state_with_federal: true,
    });
    assert.deepEqual(compareTaxRequestFields({ taxRates: {} }), {
      tax_rates: UI_DEFAULT_TAX_RATES,
      combine_state_with_federal: true,
    });
    assert.deepEqual(compareTaxRequestFields(), {
      tax_rates: UI_DEFAULT_TAX_RATES,
      combine_state_with_federal: true,
    });
    assert.equal(UI_DEFAULT_TAX_RATES.ordinary_income, 0.37);
    assert.equal(UI_DEFAULT_TAX_RATES.long_term_capital_gains, 0.2);
    assert.equal(UI_DEFAULT_TAX_RATES.short_term_capital_gains, 0.37);
    assert.equal(UI_DEFAULT_TAX_RATES.qualified_dividend, 0.2);
    assert.equal(UI_DEFAULT_TAX_RATES.state, 0.05);
  });

  it("includes edited tax rates on YoY compare requests", () => {
    const taxRates = {
      ...UI_DEFAULT_TAX_RATES,
      ordinary_income: 0.24,
      state: 0.1,
    };
    const request = yoyTaxDragCompareRequest({
      ticker: "ABALX",
      holdingDollars: 25_000,
      periods: [{ year: 2025 }],
      taxRates,
      combineStateWithFederal: false,
    });
    assert.deepEqual(request.tax_rates, taxRates);
    assert.equal(request.combine_state_with_federal, false);
    assert.notDeepEqual(request.tax_rates, {});
    const body = toDataApiCompareBody(request);
    assert.deepEqual(body.tax_rates, taxRates);
    assert.equal(body.combine_state_with_federal, false);
  });

  it("builds an AGTHX YoY body without fund_name so Data does not AND-miss", () => {
    const body = toDataApiCompareBody(
      yoyTaxDragCompareRequest({
        ticker: "AGTHX",
        fundFamily: "American Funds",
        fundName: "American Funds Growth Fund of America",
        holdingDollars: 10_000,
        periods: [{ year: 2021 }, { year: 2022 }, { year: 2023 }, { year: 2024 }, { year: 2025 }],
      }),
      seedLookup,
    );
    assert.equal(body.selectors?.fund_name, undefined);
    assert.equal(body.left?.selectors?.fund_name, undefined);
    assert.equal(body.nav_per_share, 72.14);
    assert.equal(body.left?.selectors?.ticker, "AGTHX");
    assert.equal(body.selectors?.fund_family, "American Funds");
  });

  it("POSTs the locked 2021–2025 paid-history window for AGTHX / AMCPX", () => {
    assert.deepEqual(
      trailingCalendarPeriods(2026).map((period) => period.year),
      [2021, 2022, 2023, 2024, 2025],
    );
    assert.deepEqual(
      trailingCalendarPeriods().map((period) => period.year),
      [2021, 2022, 2023, 2024, 2025],
    );
  });

  it("builds AMCPX vs AGTHX fund_vs_fund without ticker-as-fund_name", () => {
    const body = toDataApiCompareBody(
      {
        mode: "fund_vs_fund",
        holding_dollars: 10_000,
        left: {
          ...compareSideFromFund({
            ticker: "AMCPX",
            fundName: "AMCPX",
            family: "American Funds",
            label: "AMCPX",
            nav: 41.22,
          }),
          holding_dollars: 10_000,
        },
        right: {
          ...compareSideFromFund({
            ticker: "AGTHX",
            fundName: "The Growth Fund of America",
            family: "American Funds",
            label: "AGTHX",
            nav: 72.14,
          }),
          holding_dollars: 10_000,
        },
        periods: trailingCalendarPeriods(2026),
      },
      seedLookup,
    );
    assert.equal(body.mode, "fund_vs_fund");
    assert.equal(body.left?.selectors?.ticker, "AMCPX");
    assert.equal(body.left?.selectors?.fund_name, undefined);
    assert.equal(body.right?.selectors?.ticker, "AGTHX");
    assert.equal(body.right?.selectors?.fund_name, undefined);
    assert.equal(body.left?.nav_per_share, 41.22);
    assert.equal(body.right?.nav_per_share, 72.14);
    assert.deepEqual(
      body.periods?.map((period) => period.year),
      [2021, 2022, 2023, 2024, 2025],
    );
  });
});
