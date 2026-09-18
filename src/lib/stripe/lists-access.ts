import { isListsEntitled, type Entitlement } from "./entitlement.ts";

/** Keep in lockstep with `LISTS_PAYWALL_LEAD` in copy.ts — do not import copy here (legal-copy). */
export const LISTS_LOCKED_DETAIL = "Lists is included with Aftertax access.";

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
    detail: LISTS_LOCKED_DETAIL,
  };
}

export function listsApiStatus(entitlement: Entitlement): 200 | 403 {
  return isListsEntitled(entitlement) ? 200 : 403;
}
