"use client";

import { useEffect, useMemo, useState } from "react";
import type { FundEstimateView } from "@/data/types";
import { COPY } from "@/lib/copy";
import {
  looksLikeExactTicker,
  notifyPortfolioTickerMiss,
  tickerMissEmptyLabel,
} from "@/lib/data-api/request-ticker";
import { usePortfolioMissRequest } from "@/lib/data-api/use-portfolio-miss";
import { useSearchMissRequest } from "@/lib/data-api/use-search-miss";
import { shouldClearFundPickerSelection } from "@/components/illustrate/fund-picker-clear";
import { fundPickerMatches } from "@/data/fund-picker-matches";
import { shouldOpenFundSuggestions } from "@/components/illustrate/fund-picker-suggestions";
import { tickerSlotBorderClass } from "@/components/illustrate/ticker-slot-border";

const REMOTE_SEARCH_DEBOUNCE_MS = 220;

async function fetchRemoteFunds(query: string): Promise<FundEstimateView[]> {
  const params = new URLSearchParams();
  params.set("q", query);
  params.set("limit", "20");
  params.set("offset", "0");
  const response = await fetch(`/api/funds?${params.toString()}`);
  if (!response.ok) return [];
  const body = (await response.json()) as {
    items?: FundEstimateView[];
    data?: FundEstimateView[];
  };
  return Array.isArray(body.items)
    ? body.items
    : Array.isArray(body.data)
      ? body.data
      : [];
}

export function FundPicker({
  funds,
  selected,
  onSelect,
  inputId = "fund-search",
  autoFocus = false,
  label = COPY.searchCta,
  reportSearchMiss = false,
  reportPortfolioMiss = false,
  pendingTicker = null,
  onUnknownTicker,
  onClear,
  onNotice,
}: {
  funds: FundEstimateView[];
  selected: FundEstimateView | null;
  onSelect: (fund: FundEstimateView) => void;
  inputId?: string;
  autoFocus?: boolean;
  label?: string;
  /** Search tab only — Compare / Portfolio leave this off. */
  reportSearchMiss?: boolean;
  /** Compare / Portfolio slots — POST source=portfolio, not search_miss. */
  reportPortfolioMiss?: boolean;
  /** Unknown slot ticker kept without inventing fund data. */
  pendingTicker?: string | null;
  onUnknownTicker?: (ticker: string) => void;
  /** Empty the chip / query and drop the selected ticker. */
  onClear?: () => void;
  onNotice?: (message: string) => void;
}) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [remoteFunds, setRemoteFunds] = useState<FundEstimateView[]>([]);
  const [remotePending, setRemotePending] = useState(false);

  useEffect(() => {
    const q = query.trim();
    let cancelled = false;
    const handle = window.setTimeout(() => {
      if (!q) {
        if (!cancelled) {
          setRemoteFunds([]);
          setRemotePending(false);
        }
        return;
      }
      if (!cancelled) setRemotePending(true);
      void fetchRemoteFunds(q)
        .then((items) => {
          if (!cancelled) setRemoteFunds(items);
        })
        .catch(() => {
          if (!cancelled) setRemoteFunds([]);
        })
        .finally(() => {
          if (!cancelled) setRemotePending(false);
        });
    }, q ? REMOTE_SEARCH_DEBOUNCE_MS : 0);
    return () => {
      cancelled = true;
      window.clearTimeout(handle);
    };
  }, [query]);

  const matches = useMemo(
    () => fundPickerMatches(funds, remoteFunds, query),
    [funds, query, remoteFunds],
  );

  const tickerInUniverse = useMemo(() => {
    const key = query.trim().toUpperCase();
    if (!key) return false;
    return (
      remotePending ||
      funds.some((fund) => fund.ticker.toUpperCase() === key) ||
      remoteFunds.some((fund) => fund.ticker.toUpperCase() === key)
    );
  }, [funds, query, remoteFunds, remotePending]);

  useSearchMissRequest(
    reportSearchMiss ? query : "",
    matches.length,
    tickerInUniverse,
    onNotice,
  );

  usePortfolioMissRequest(
    reportPortfolioMiss && !reportSearchMiss ? query : "",
    matches.length,
    tickerInUniverse,
    onNotice,
  );

  function showSuggestions(value: string) {
    setOpen(shouldOpenFundSuggestions(value));
  }

  const hasSelection = Boolean(selected || pendingTicker);
  const displayValue = open
    ? query
    : pendingTicker
      ? pendingTicker
      : selected
        ? `${selected.ticker} · ${selected.fundName}`
        : query;
  const canClear = Boolean(displayValue || hasSelection);

  function clearSelection() {
    setQuery("");
    setOpen(false);
    onClear?.();
  }

  return (
    <div className="relative">
      <label htmlFor={inputId} className="mb-1.5 block text-[11px] font-semibold uppercase tracking-[0.12em] text-faint">
        {label}
      </label>
      <div className="relative">
        <input
          id={inputId}
          type="search"
          value={displayValue}
          onChange={(event) => {
            const next = event.target.value;
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
            setQuery(next);
            showSuggestions(next);
          }}
          onFocus={() => {
            if (selected || pendingTicker) {
              setQuery("");
              setOpen(false);
              return;
            }
            showSuggestions(query);
          }}
          onBlur={() => {
            window.setTimeout(() => setOpen(false), 120);
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
            if (event.key === "Enter" && reportPortfolioMiss) {
              const typed = query.trim().toUpperCase();
              if (!looksLikeExactTicker(typed) || matches.length > 0) return;
              event.preventDefault();
              notifyPortfolioTickerMiss(typed, tickerInUniverse, onNotice);
              onUnknownTicker?.(typed);
              setOpen(false);
            }
          }}
          placeholder="Ticker, name, CUSIP, or family"
          className={`h-12 w-full rounded-md border ${tickerSlotBorderClass({ committed: hasSelection, midEdit: open })} bg-surface px-3 pr-11 text-base text-ink placeholder:text-faint [&::-webkit-search-cancel-button]:hidden [&::-webkit-search-decoration]:hidden`}
          autoComplete="off"
          autoFocus={autoFocus}
        />
        {canClear ? (
          <button
            type="button"
            aria-label="Clear search"
            className="absolute top-1/2 right-2 flex h-5 w-5 -translate-y-1/2 items-center justify-center rounded-full bg-ink/70 text-[11px] leading-none text-white hover:bg-ink"
            onMouseDown={(event) => event.preventDefault()}
            onClick={clearSelection}
          >
            ×
          </button>
        ) : null}
      </div>
      {open ? (
        <ul className="absolute z-20 mt-1 max-h-72 w-full overflow-auto rounded-md border border-line bg-surface shadow-lg">
          {matches.length === 0 ? (
            <li className="px-3 py-3 text-sm text-muted">
              {reportPortfolioMiss
                ? tickerMissEmptyLabel({
                    query,
                    tickerInUniverse,
                    pending: remotePending,
                  })
                : remotePending
                  ? "Searching…"
                  : "No funds match."}
            </li>
          ) : (
            matches.map((fund) => (
              <li key={fund.id}>
                <button
                  type="button"
                  className="flex w-full items-start gap-3 px-3 py-2.5 text-left hover:bg-paper"
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => {
                    onSelect(fund);
                    setQuery("");
                    setOpen(false);
                  }}
                >
                  <span className="min-w-0">
                    <span className="block text-sm font-medium text-ink">
                      {fund.fundName}
                    </span>
                    <span className="font-mono text-[11px] text-faint">
                      {fund.ticker} · {fund.family}
                    </span>
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
