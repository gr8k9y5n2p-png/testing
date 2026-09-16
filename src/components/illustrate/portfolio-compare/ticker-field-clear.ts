import { shouldClearFundPickerSelection } from "../fund-picker-clear.ts";

/** Same wipe rule as Search-a-fund: empty / chip Backspace drops the selection. */
export const shouldClearTickerSelection = shouldClearFundPickerSelection;

export function emptyTickerSelection(): {
  ticker: string;
  fundName: string;
  nav: null;
} {
  return { ticker: "", fundName: "", nav: null };
}

/** After X-wipe, do not rebuild the input from a still-selected fund. */
export function tickerFieldDisplay(input: {
  open: boolean;
  query: string;
  ticker: string;
  cleared: boolean;
}): string {
  if (input.cleared) return input.query;
  return input.open ? input.query : input.ticker;
}

export function tickerFieldSubtitle(input: {
  fundName: string;
  cleared: boolean;
}): string {
  if (input.cleared || !input.fundName) return "Search a ticker";
  return input.fundName;
}

/** Focus/blur must not copy ticker back after an explicit wipe. */
export function shouldRehydrateTickerFromSelection(input: {
  cleared: boolean;
}): boolean {
  return !input.cleared;
}

/** Tab or Enter locks the typed ticker — do not wait for a dropdown click. */
export function isTickerLockKey(key: string): boolean {
  return key === "Enter" || key === "Tab";
}

/**
 * Clicking a locked ticker input must keep the value.
 * Only an explicit text edit or the X wipe may change it.
 */
export function shouldKeepLockedTickerOnFocus(input: {
  hasSelection: boolean;
  cleared: boolean;
}): boolean {
  return input.hasSelection && !input.cleared;
}
