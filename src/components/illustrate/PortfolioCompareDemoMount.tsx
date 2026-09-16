"use client";

import { useRef } from "react";
import { NoticeToast, useNoticeToast } from "@/components/NoticeToast";
import {
  PortfolioCompare,
  type PortfolioCompareHandle,
} from "@/components/illustrate/PortfolioCompare";
import { PortfolioSaveOpenActions } from "@/components/illustrate/PortfolioSaveOpenActions";
import { WEBSITE_PORTFOLIO_HOLDINGS } from "@/lib/illustrate/portfolio-compare-mount";
import type { PortfolioFundOption } from "@/lib/illustrate/portfolio-compare-types";

/** `/portfolio-compare` demo — same Save/Open contract as `/portfolio`. */
export function PortfolioCompareDemoMount({
  funds,
}: {
  funds: PortfolioFundOption[];
}) {
  const booksApiRef = useRef<PortfolioCompareHandle | null>(null);
  const { notice, onNotice, dismissNotice } = useNoticeToast();

  return (
    <>
      <PortfolioCompare
        funds={funds}
        current={WEBSITE_PORTFOLIO_HOLDINGS}
        proposed={WEBSITE_PORTFOLIO_HOLDINGS}
        booksApiRef={booksApiRef}
        headerActions={
          <PortfolioSaveOpenActions
            booksApiRef={booksApiRef}
            onNotice={onNotice}
          />
        }
      />
      <NoticeToast message={notice} onDismiss={dismissNotice} />
    </>
  );
}
