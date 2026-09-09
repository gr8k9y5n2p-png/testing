"use client";

import { useEffect, useRef } from "react";
import {
  noticeForTickerRequest,
  requestTickerOnPortfolioMiss,
  shouldReportSearchMiss,
} from "@/lib/data-api/request-ticker";

const PORTFOLIO_MISS_DEBOUNCE_MS = 650;

/**
 * Compare slot typed an exact ticker with no catalog match.
 * POSTs source=portfolio (not search_miss). Toast is non-blocking.
 * Never invents performance, historical dist, or Upcoming dollars.
 */
export function usePortfolioMissRequest(
  query: string,
  resultCount: number,
  tickerInUniverse: boolean,
  onNotice?: (message: string) => void,
): void {
  const onNoticeRef = useRef(onNotice);

  useEffect(() => {
    onNoticeRef.current = onNotice;
  }, [onNotice]);

  useEffect(() => {
    if (
      !shouldReportSearchMiss({
        query,
        resultCount,
        tickerInUniverse,
      })
    ) {
      return;
    }
    const handle = window.setTimeout(() => {
      void requestTickerOnPortfolioMiss(query).then((result) => {
        if (!result) return;
        const message = noticeForTickerRequest(result, "portfolio");
        if (message) onNoticeRef.current?.(message);
      });
    }, PORTFOLIO_MISS_DEBOUNCE_MS);
    return () => window.clearTimeout(handle);
  }, [query, resultCount, tickerInUniverse]);
}
