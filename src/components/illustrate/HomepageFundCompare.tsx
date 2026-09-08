"use client";

import { useMemo, useState } from "react";
import type { FundEstimateView } from "@/data/types";
import { FundPicker } from "@/components/illustrate/FundPicker";
import { FundTaxDeltaCompare } from "@/components/illustrate/FundTaxDeltaCompare";
import {
  GrowthAndTaxDragModule,
  type GrowthFundInput,
} from "@/components/illustrate/GrowthAndTaxDragModule";
import {
  defaultComparePeer,
  findFundByTicker,
} from "@/lib/illustrate/fund-compare-defaults";
import { compareSideFromFund } from "@/lib/illustrate/compare-request";
import { seedNavLookup } from "@/lib/illustrate/seed-nav";
import {
  COMPARE_SUMMARY_HOLDING_DOLLARS,
  type CompareSideIn,
} from "@/lib/illustrate/compare-types";
import { UI_DEFAULT_TAX_RATES } from "@/lib/illustrate/types";
import { DEFAULT_START_DOLLARS } from "@/lib/performance/types";

const COMPARE_TAX_RATES = { state: UI_DEFAULT_TAX_RATES.state };

/** Seed-catalog pair: golden AMCPX vs same-category other-family VIGAX. */
const DEFAULT_LEFT_TICKER = "AMCPX";
const DEFAULT_RIGHT_TICKER = "VIGAX";

function sideFromFund(fund: FundEstimateView): CompareSideIn {
  return compareSideFromFund(fund, seedNavLookup);
}

function defaultLeft(funds: FundEstimateView[]): FundEstimateView | null {
  return (
    findFundByTicker(funds, DEFAULT_LEFT_TICKER) ??
    funds[0] ??
    null
  );
}

function defaultRight(
  funds: FundEstimateView[],
  left: FundEstimateView | null,
): FundEstimateView | null {
  if (!left) return findFundByTicker(funds, DEFAULT_RIGHT_TICKER) ?? funds[1] ?? null;
  return (
    findFundByTicker(funds, DEFAULT_RIGHT_TICKER) ??
    defaultComparePeer(left, funds)
  );
}

export function HomepageFundCompare({
  funds,
  initialLeftTicker,
  initialRightTicker,
  headingAs: Heading = "h1",
}: {
  funds: FundEstimateView[];
  initialLeftTicker?: string;
  initialRightTicker?: string;
  headingAs?: "h1" | "h2";
}) {
  const seededLeft =
    findFundByTicker(funds, initialLeftTicker) ?? defaultLeft(funds);
  const seededRight =
    findFundByTicker(funds, initialRightTicker) ??
    defaultRight(funds, seededLeft);

  const [leftFund, setLeftFund] = useState<FundEstimateView | null>(seededLeft);
  const [rightFund, setRightFund] = useState<FundEstimateView | null>(
    seededRight && seededLeft && seededRight.ticker === seededLeft.ticker
      ? defaultComparePeer(seededLeft, funds)
      : seededRight,
  );

  const left = useMemo(
    () => (leftFund ? sideFromFund(leftFund) : null),
    [leftFund],
  );
  const right = useMemo(
    () => (rightFund ? sideFromFund(rightFund) : null),
    [rightFund],
  );
  const growthFunds = useMemo(() => {
    const next: GrowthFundInput[] = [];
    if (leftFund) next.push(toGrowthFund(leftFund));
    if (rightFund) next.push(toGrowthFund(rightFund));
    return next;
  }, [leftFund, rightFund]);

  return (
    <section id="fund-compare" aria-label="Fund-to-fund comparison" className="w-full">
      <header className="mb-6">
        <p className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-faint">
          <span aria-hidden className="inline-block size-1.5 rounded-full bg-tax-less" />
          Aftertax · Compare
        </p>
        <Heading className="mt-1 font-serif text-3xl tracking-tight text-ink">
          Fund-to-fund comparison
        </Heading>
        <p className="mt-2 max-w-2xl text-sm text-muted">
          Year-over-year tax cost of two funds. Footer figures are normalized to $
          {COMPARE_SUMMARY_HOLDING_DOLLARS.toLocaleString("en-US")}.
        </p>
      </header>

      <div className="grid w-full items-start gap-4 sm:grid-cols-2">
        <FundPicker
          funds={funds}
          selected={leftFund}
          onSelect={(fund) => {
            setLeftFund(fund);
            if (rightFund && fund.ticker === rightFund.ticker) {
              setRightFund(defaultComparePeer(fund, funds));
            }
          }}
          inputId="compare-left-search"
          label="Fund A"
        />
        <FundPicker
          funds={funds}
          selected={rightFund}
          onSelect={(fund) => {
            if (leftFund && fund.ticker === leftFund.ticker) return;
            setRightFund(fund);
          }}
          inputId="compare-right-search"
          label="Fund B"
        />
      </div>

      {left && right ? (
        <div className="mt-8 w-full">
          <FundTaxDeltaCompare
            left={left}
            right={right}
            holdingDollars={COMPARE_SUMMARY_HOLDING_DOLLARS}
            taxRates={COMPARE_TAX_RATES}
            fullWidth
          />
        </div>
      ) : (
        <p className="mt-8 text-sm text-muted">
          Choose two different funds to see the tax-delta compare.
        </p>
      )}

      <section
        id="growth-and-tax"
        aria-label="Growth of dollars and tax drag"
        className="mt-10 w-full scroll-mt-20"
      >
        <GrowthAndTaxDragModule
          funds={growthFunds}
          seedFunds={growthFunds}
          startDollars={DEFAULT_START_DOLLARS}
        />
      </section>
    </section>
  );
}

function toGrowthFund(fund: FundEstimateView): GrowthFundInput {
  return {
    ticker: fund.ticker,
    label: fund.ticker,
    fundIdentifier: fund.ticker,
    fundFamily: fund.family,
    fundName: fund.fundName,
    navPerShare: fund.nav > 0 ? fund.nav : undefined,
  };
}
