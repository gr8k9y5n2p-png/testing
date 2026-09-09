"use client";

import { useEffect, useRef } from "react";
import {
  noticeForTickerRequest,
  requestTickerOnSearchMiss,
  shouldReportSearchMiss,
} from "@/lib/data-api/request-ticker";

const SEARCH_MISS_DEBOUNCE_MS = 650;

/**
 * When Search has no match for an exact typed ticker, POST source=search_miss.
 * Toast is non-blocking; never invents fund rows.
 */
export function useSearchMissRequest(
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
      void requestTickerOnSearchMiss(query).then((result) => {
        if (!result) return;
        const message = noticeForTickerRequest(result, "search_miss");
        if (message) onNoticeRef.current?.(message);
      });
    }, SEARCH_MISS_DEBOUNCE_MS);
    return () => window.clearTimeout(handle);
  }, [query, resultCount, tickerInUniverse]);
}
