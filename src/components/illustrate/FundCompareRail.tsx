"use client";

import { useMemo, useState } from "react";
import type { FundEstimateView } from "@/data/types";
import { FundPicker } from "@/components/illustrate/FundPicker";
import { FundTaxDeltaCompare } from "@/components/illustrate/FundTaxDeltaCompare";
import {
  COMPARE_SUMMARY_HOLDING_DOLLARS,
  type CompareSideIn,
} from "@/lib/illustrate/compare-types";
import { UI_DEFAULT_TAX_RATES } from "@/lib/illustrate/types";

const COMPARE_TAX_RATES = { state: UI_DEFAULT_TAX_RATES.state };

export function defaultComparePeer(
  selected: FundEstimateView,
  funds: FundEstimateView[],
): FundEstimateView | null {
  const others = funds.filter(
    (fund) => fund.id !== selected.id && fund.ticker !== selected.ticker,
  );
  const sameCategoryOtherFamily = others.find(
    (fund) =>
      fund.category === selected.category && fund.family !== selected.family,
  );
  if (sameCategoryOtherFamily) return sameCategoryOtherFamily;
  return others[0] ?? null;
}

function sideFromFund(fund: FundEstimateView): CompareSideIn {
  return {
    label: fund.fundName,
    selectors: {
      ticker: fund.ticker,
      fund_identifier: fund.ticker,
      fund_family: fund.family,
      fund_name: fund.fundName,
    },
  };
}

export function FundCompareRail({
  funds,
  selected,
}: {
  funds: FundEstimateView[];
  selected: FundEstimateView;
}) {
  const fallbackPeer = defaultComparePeer(selected, funds);
  const [overridePeer, setOverridePeer] = useState<FundEstimateView | null>(
    null,
  );
  const peer =
    overridePeer && overridePeer.ticker !== selected.ticker
      ? overridePeer
      : fallbackPeer;

  const left = useMemo(() => sideFromFund(selected), [selected]);
  const right = useMemo(
    () => (peer ? sideFromFund(peer) : null),
    [peer],
  );

  if (!peer || !right) return null;

  return (
    <aside aria-labelledby="compare-heading" className="min-w-0">
      <div className="mb-4">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">
          Fund vs fund
        </p>
        <h2
          id="compare-heading"
          className="mt-1 font-serif text-xl tracking-tight text-ink"
        >
          Tax-delta compare
        </h2>
        <p className="mt-1 max-w-sm text-sm text-muted">
          Year-over-year tax cost of {selected.ticker} versus a peer. Footer
          figures are normalized to $
          {COMPARE_SUMMARY_HOLDING_DOLLARS.toLocaleString("en-US")}.
        </p>
      </div>
      <FundPicker
        funds={funds}
        selected={peer}
        onSelect={(fund) => {
          if (fund.ticker === selected.ticker) return;
          setOverridePeer(fund);
        }}
        inputId="compare-peer-search"
        label="Compare with"
      />
      <div className="mt-5 flex justify-center xl:justify-start">
        <FundTaxDeltaCompare
          left={left}
          right={right}
          holdingDollars={COMPARE_SUMMARY_HOLDING_DOLLARS}
          taxRates={COMPARE_TAX_RATES}
        />
      </div>
    </aside>
  );
}
