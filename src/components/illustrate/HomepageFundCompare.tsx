"use client";

import { useMemo, useState } from "react";
import type { FundEstimateView } from "@/data/types";
import { NoticeToast, useNoticeToast } from "@/components/NoticeToast";
import { FundPicker } from "@/components/illustrate/FundPicker";
import { FundTaxDeltaCompare } from "@/components/illustrate/FundTaxDeltaCompare";
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
  const [leftPending, setLeftPending] = useState<string | null>(null);
  const [rightPending, setRightPending] = useState<string | null>(null);
  const { notice, onNotice, dismissNotice } = useNoticeToast();

  const left = useMemo(
    () =>
      leftPending
        ? compareSideFromFund({ ticker: leftPending })
        : leftFund
          ? sideFromFund(leftFund)
          : null,
    [leftFund, leftPending],
  );
  const right = useMemo(
    () =>
      rightPending
        ? compareSideFromFund({ ticker: rightPending })
        : rightFund
          ? sideFromFund(rightFund)
          : null,
    [rightFund, rightPending],
  );

  function occupyLeft(ticker: string) {
    return (
      leftPending === ticker ||
      leftFund?.ticker.toUpperCase() === ticker
    );
  }

  function occupyRight(ticker: string) {
    return (
      rightPending === ticker ||
      rightFund?.ticker.toUpperCase() === ticker
    );
  }

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

      <div className="grid max-w-3xl items-start gap-4 sm:grid-cols-2">
        <FundPicker
          funds={funds}
          selected={leftPending ? null : leftFund}
          pendingTicker={leftPending}
          reportPortfolioMiss
          onNotice={onNotice}
          onSelect={(fund) => {
            setLeftPending(null);
            setLeftFund(fund);
            if (
              (rightFund && fund.ticker === rightFund.ticker) ||
              rightPending === fund.ticker
            ) {
              setRightPending(null);
              setRightFund(defaultComparePeer(fund, funds));
            }
          }}
          onUnknownTicker={(ticker) => {
            if (occupyRight(ticker)) return;
            setLeftFund(null);
            setLeftPending(ticker);
          }}
          inputId="compare-left-search"
          label="Fund A"
        />
        <FundPicker
          funds={funds}
          selected={rightPending ? null : rightFund}
          pendingTicker={rightPending}
          reportPortfolioMiss
          onNotice={onNotice}
          onSelect={(fund) => {
            if (occupyLeft(fund.ticker.toUpperCase())) return;
            setRightPending(null);
            setRightFund(fund);
          }}
          onUnknownTicker={(ticker) => {
            if (occupyLeft(ticker)) return;
            setRightFund(null);
            setRightPending(ticker);
          }}
          inputId="compare-right-search"
          label="Fund B"
        />
      </div>

      {left && right && !leftPending && !rightPending ? (
        <div className="mt-8">
          <FundTaxDeltaCompare
            left={left}
            right={right}
            holdingDollars={COMPARE_SUMMARY_HOLDING_DOLLARS}
            taxRates={COMPARE_TAX_RATES}
          />
        </div>
      ) : (
        <p className="mt-8 text-sm text-muted">
          {leftPending || rightPending
            ? "Not available / undisclosed. Compare stays empty until this ticker is ingested."
            : "Choose two different funds to see the tax-delta compare."}
        </p>
      )}
      <NoticeToast message={notice} onDismiss={dismissNotice} />
    </section>
  );
}
