"use client";

import { useMemo, useRef, useState } from "react";
import { shouldClearFundPickerSelection } from "@/components/illustrate/fund-picker-clear";
import { shouldOpenFundSuggestions } from "@/components/illustrate/fund-picker-suggestions";
import { tickerSlotBorderClass } from "@/components/illustrate/ticker-slot-border";
import {
  looksLikeExactTicker,
  notifyPortfolioTickerMiss,
} from "@/lib/data-api/request-ticker";
import type { PortfolioFundOption } from "@/lib/illustrate/portfolio-compare-types";
import {
  emptyTickerSelection,
  tickerFieldDisplay,
  tickerFieldSubtitle,
} from "@/components/illustrate/portfolio-compare/ticker-field-clear";

function findExactFund(funds: PortfolioFundOption[], ticker: string) {
  const key = ticker.trim().toUpperCase();
  return funds.find((fund) => fund.ticker.toUpperCase() === key);
}

export function TickerField({
  ticker,
  fundName,
  funds,
  inputId,
  onSelect,
  onNotice,
  autoFocus = false,
  allowEmpty = false,
  placeholder = "Ticker",
  hideSubtitle = false,
}: {
  ticker: string;
  fundName: string;
  funds: PortfolioFundOption[];
  inputId: string;
  allowEmpty?: boolean;
  placeholder?: string;
  /** Compare slots: number lives in the placeholder, not a label above/below. */
  hideSubtitle?: boolean;
  onSelect: (fund: {
    ticker: string;
    fundName: string;
    family?: string;
    nav?: number | null;
  }) => void;
  onNotice?: (message: string) => void;
  autoFocus?: boolean;
}) {
  const [query, setQuery] = useState(ticker);
  const [open, setOpen] = useState(false);
  const [cleared, setCleared] = useState(false);
  const pickedRef = useRef(false);
  const hasSelection = Boolean((ticker || fundName) && !cleared);
  const display = tickerFieldDisplay({ open, query, ticker, cleared });
  const subtitle = hideSubtitle
    ? ""
    : tickerFieldSubtitle({ fundName, cleared });
  const canClear = Boolean(display || hasSelection);

  function commitUnknown(typed: string) {
    setCleared(false);
    onSelect({ ticker: typed, fundName: "", nav: null });
    notifyPortfolioTickerMiss(typed, false, onNotice);
  }

  function clearSelection() {
    setQuery("");
    setOpen(false);
    setCleared(true);
    pickedRef.current = true;
    onSelect(emptyTickerSelection());
  }

  const matches = useMemo(() => {
    const needle = (open ? query : cleared ? "" : ticker).trim().toLowerCase();
    if (!needle) return [];
    return funds
      .filter((fund) => {
        const haystack = `${fund.ticker} ${fund.fundName} ${fund.family ?? ""}`.toLowerCase();
        return haystack.includes(needle);
      })
      .slice(0, 8);
  }, [cleared, funds, open, query, ticker]);

  function showSuggestions(value: string) {
    setOpen(shouldOpenFundSuggestions(value));
  }

  return (
    <div className="relative min-w-0 flex-1">
      <div className="relative">
        <input
          id={inputId}
          type="text"
          role="combobox"
          value={display}
          autoComplete="off"
          spellCheck={false}
          placeholder={placeholder}
          autoFocus={autoFocus}
          aria-label={placeholder}
          aria-autocomplete="list"
          aria-expanded={open}
          aria-controls={`${inputId}-list`}
          className={`h-10 w-full rounded-md border ${tickerSlotBorderClass({ committed: hasSelection, midEdit: open })} bg-paper px-2.5 pr-9 font-mono text-sm font-medium uppercase tracking-wide text-ink placeholder:normal-case placeholder:tracking-normal placeholder:text-faint`}
          onChange={(event) => {
            const next = event.target.value.toUpperCase();
            if (
              shouldClearFundPickerSelection({
                nextValue: next,
                hasSelection,
                suggestionsOpen: open,
              })
            ) {
              clearSelection();
              return;
            }
            setCleared(false);
            setQuery(next);
            showSuggestions(next);
          }}
          onFocus={() => {
            if (hasSelection || cleared) {
              setQuery("");
              setOpen(false);
              return;
            }
            setQuery(ticker);
            showSuggestions(ticker);
          }}
          onBlur={() => {
            window.setTimeout(() => {
              setOpen(false);
              if (pickedRef.current) {
                pickedRef.current = false;
                return;
              }
              if (cleared) {
                setQuery("");
                return;
              }
              const typed = query.trim().toUpperCase();
              if (!typed) {
                setQuery("");
                if (allowEmpty || ticker || fundName) {
                  onSelect(emptyTickerSelection());
                }
                return;
              }
              if (typed !== ticker) {
                const match = findExactFund(funds, typed);
                if (match) {
                  onSelect(match);
                  return;
                }
                if (looksLikeExactTicker(typed)) {
                  commitUnknown(typed);
                  return;
                }
                onSelect({
                  ticker: typed,
                  fundName: "",
                  nav: null,
                });
              } else {
                setQuery(ticker);
              }
            }, 120);
          }}
          onKeyDown={(event) => {
            if (event.key === "Escape") {
              event.preventDefault();
              setOpen(false);
              return;
            }
            if (
              shouldClearFundPickerSelection({
                key: event.key,
                hasSelection,
                suggestionsOpen: open,
              })
            ) {
              event.preventDefault();
              clearSelection();
              return;
            }
            if (event.key === "Enter") {
              event.preventDefault();
              const typed = query.trim().toUpperCase();
              if (!typed) return;
              const exact = findExactFund(funds, typed);
              const match = exact ?? matches[0];
              if (match) {
                pickedRef.current = true;
                setCleared(false);
                onSelect(match);
                setQuery(match.ticker);
                setOpen(false);
              } else if (looksLikeExactTicker(typed)) {
                pickedRef.current = true;
                commitUnknown(typed);
                setQuery(typed);
                setOpen(false);
              }
            }
          }}
        />
        {canClear ? (
          <button
            type="button"
            aria-label="Clear ticker"
            className="absolute top-1/2 right-2 flex h-5 w-5 -translate-y-1/2 items-center justify-center rounded-full bg-ink/70 text-[11px] leading-none text-white hover:bg-ink"
            onMouseDown={(event) => event.preventDefault()}
            onClick={clearSelection}
          >
            ×
          </button>
        ) : null}
      </div>
      {hideSubtitle ? null : (
        <p className="mt-1 truncate text-[11px] leading-snug text-muted">
          {subtitle}
        </p>
      )}
      {open ? (
        <ul
          id={`${inputId}-list`}
          role="listbox"
          className="absolute z-30 mt-1 max-h-60 w-[min(100%,20rem)] overflow-auto rounded-md border border-line bg-surface shadow-lg"
        >
          {matches.length === 0 ? (
            <li className="px-3 py-2.5 text-sm text-muted">No funds match.</li>
          ) : (
            matches.map((fund) => (
              <li key={fund.ticker} role="option" aria-selected={fund.ticker === ticker}>
                <button
                  type="button"
                  className="flex w-full items-start justify-between gap-3 px-3 py-2 text-left hover:bg-paper"
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => {
                    pickedRef.current = true;
                    setCleared(false);
                    onSelect(fund);
                    setQuery(fund.ticker);
                    setOpen(false);
                  }}
                >
                  <span>
                    <span className="block font-mono text-sm font-medium text-ink">
                      {fund.ticker}
                    </span>
                    <span className="block text-[11px] text-muted">{fund.fundName}</span>
                    {fund.family ? (
                      <span className="block text-[11px] text-faint">{fund.family}</span>
                    ) : null}
                  </span>
                </button>
              </li>
            ))
          )}
        </ul>
      ) : null}
    </div>
  );
}
