"use client";

import { useRef } from "react";
import { NoticeToast, useNoticeToast } from "@/components/NoticeToast";
import {
  PortfolioCompare,
  type PortfolioCompareHandle,
} from "@/components/illustrate/PortfolioCompare";
import { PortfolioSaveOpenActions } from "@/components/illustrate/PortfolioSaveOpenActions";
import { WEBSITE_PORTFOLIO_HOLDINGS } from "@/lib/illustrate/portfolio-compare-mount";

/** `/portfolio-compare` demo — same Save/Open contract as `/portfolio`. */
export function PortfolioCompareDemoMount() {
  const booksApiRef = useRef<PortfolioCompareHandle | null>(null);
  const { notice, onNotice, dismissNotice } = useNoticeToast();

  return (
    <>
      <PortfolioCompare
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
