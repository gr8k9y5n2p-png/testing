"use client";

import { useMemo, useState } from "react";
import type { FundEstimateView } from "@/data/types";
import { NoticeToast, useNoticeToast } from "@/components/NoticeToast";
import { FundPicker } from "@/components/illustrate/FundPicker";
import { FundTaxDeltaCompare } from "@/components/illustrate/FundTaxDeltaCompare";
import { compareSideFromFund } from "@/lib/illustrate/compare-request";
import { defaultComparePeer } from "@/lib/illustrate/fund-compare-defaults";
import {
  COMPARE_SUMMARY_HOLDING_DOLLARS,
  type CompareSideIn,
} from "@/lib/illustrate/compare-types";
import { UI_DEFAULT_TAX_RATES } from "@/lib/illustrate/types";

const COMPARE_TAX_RATES = { state: UI_DEFAULT_TAX_RATES.state };

function sideFromFund(fund: FundEstimateView): CompareSideIn {
  return compareSideFromFund(fund);
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
  const [pendingPeer, setPendingPeer] = useState<string | null>(null);
  const { notice, onNotice, dismissNotice } = useNoticeToast();
  const peer =
    overridePeer && overridePeer.ticker !== selected.ticker
      ? overridePeer
      : fallbackPeer;

  const left = useMemo(() => sideFromFund(selected), [selected]);
  const right = useMemo(
    () =>
      pendingPeer
        ? compareSideFromFund({ ticker: pendingPeer })
        : peer
          ? sideFromFund(peer)
          : null,
    [peer, pendingPeer],
  );

  if (!right) return null;

  return (
    <aside
      id="fund-compare"
      aria-labelledby="compare-heading"
      className="min-w-0 scroll-mt-6"
    >
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
        selected={pendingPeer ? null : peer}
        pendingTicker={pendingPeer}
        reportPortfolioMiss
        onNotice={onNotice}
        onSelect={(fund) => {
          if (fund.ticker === selected.ticker) return;
          setPendingPeer(null);
          setOverridePeer(fund);
        }}
        onUnknownTicker={(ticker) => {
          if (ticker === selected.ticker.toUpperCase()) return;
          setOverridePeer(null);
          setPendingPeer(ticker);
        }}
        inputId="compare-peer-search"
        label="Compare with"
      />
      <div className="mt-5 flex justify-center xl:justify-start">
        {pendingPeer ? (
          <p className="text-sm text-muted">
            Not available / undisclosed. Compare stays empty until this ticker is
            ingested.
          </p>
        ) : (
          <FundTaxDeltaCompare
            left={left}
            right={right}
            holdingDollars={COMPARE_SUMMARY_HOLDING_DOLLARS}
            taxRates={COMPARE_TAX_RATES}
          />
        )}
      </div>
      <NoticeToast message={notice} onDismiss={dismissNotice} />
    </aside>
  );
}
