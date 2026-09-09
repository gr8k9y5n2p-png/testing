/**
 * Shared ticker-intake client for Search and Modules.
 * One fetch — do not copy POST /request/ticker.
 *
 *   import { requestTicker } from "@/lib/request-ticker";
 *   // also re-exported from "@/components/illustrate"
 *
 *   await requestTicker({ ticker: "ABCDX", note: "optional", source: "portfolio" });
 *
 * `source` (locked):
 *   web          — Request a fund form on Search
 *   search_miss  — Search exact ticker with no match
 *   portfolio    — Portfolio import / Compare slot miss
 */

export {
  noticeForTickerRequest,
  requestTicker,
  TICKER_REQUEST_PATH,
  TICKER_REQUEST_SOURCES,
} from "./data-api/request-ticker.ts";
export type {
  RequestTickerArgs,
  TickerRequestBody,
  TickerRequestResult,
  TickerRequestSource,
} from "./data-api/request-ticker.ts";
