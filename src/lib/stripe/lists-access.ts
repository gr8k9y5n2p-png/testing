import { LISTS_PAYWALL_LEAD } from "../copy.ts";
import { isListsEntitled, type Entitlement } from "./entitlement.ts";

export type ListsApiDenial = {
  items: [];
  tickers: string[];
  count: 0;
  entitled: false;
  detail: string;
};

export function listsApiDenial(tickers: string[]): ListsApiDenial {
  return {
    items: [],
    tickers,
    count: 0,
    entitled: false,
    detail: LISTS_PAYWALL_LEAD,
  };
}

export function listsApiStatus(entitlement: Entitlement): 200 | 403 {
  return isListsEntitled(entitlement) ? 200 : 403;
}
