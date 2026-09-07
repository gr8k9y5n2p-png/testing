"use client";

import { useMemo, useState } from "react";
import type { PortfolioFundOption } from "@/lib/illustrate/portfolio-compare-types";

export function TickerField({
  ticker,
  fundName,
  funds,
  inputId,
  onSelect,
}: {
  ticker: string;
  fundName: string;
  funds: PortfolioFundOption[];
  inputId: string;
  onSelect: (fund: { ticker: string; fundName: string; family?: string }) => void;
}) {
  const [query, setQuery] = useState(ticker);
  const [open, setOpen] = useState(false);
  const display = open ? query : ticker;

  const matches = useMemo(() => {
    const needle = (open ? query : ticker).trim().toLowerCase();
    const pool = funds;
    if (!needle) return pool.slice(0, 8);
    return pool
      .filter((fund) => {
        const haystack = `${fund.ticker} ${fund.fundName} ${fund.family ?? ""}`.toLowerCase();
        return haystack.includes(needle);
      })
      .slice(0, 8);
  }, [funds, open, query, ticker]);

  return (
    <div className="relative min-w-0 flex-1">
      <input
        id={inputId}
        type="text"
        role="combobox"
        value={display}
        autoComplete="off"
        spellCheck={false}
        placeholder="Ticker"
        aria-autocomplete="list"
        aria-expanded={open}
        aria-controls={`${inputId}-list`}
        className="h-10 w-full rounded-md border border-line bg-paper px-2.5 font-mono text-sm font-medium uppercase tracking-wide text-ink placeholder:normal-case placeholder:tracking-normal placeholder:text-faint"
        onChange={(event) => {
          const next = event.target.value.toUpperCase();
          setQuery(next);
          setOpen(true);
        }}
        onFocus={() => {
          setOpen(true);
          setQuery(ticker);
        }}
        onBlur={() => {
          window.setTimeout(() => {
            setOpen(false);
            const typed = query.trim().toUpperCase();
            if (typed && typed !== ticker) {
              const match = funds.find((fund) => fund.ticker.toUpperCase() === typed);
              onSelect({
                ticker: typed,
                fundName: match?.fundName || "",
                family: match?.family,
              });
            } else {
              setQuery(ticker);
            }
          }, 120);
        }}
        onKeyDown={(event) => {
          if (event.key === "Enter") {
            event.preventDefault();
            const typed = query.trim().toUpperCase();
            if (!typed) return;
            const match = funds.find((fund) => fund.ticker.toUpperCase() === typed) ?? matches[0];
            if (match) {
              onSelect(match);
              setQuery(match.ticker);
              setOpen(false);
            } else {
              onSelect({ ticker: typed, fundName: "" });
              setOpen(false);
            }
          }
          if (event.key === "Escape") {
            setOpen(false);
            setQuery(ticker);
          }
        }}
      />
      <p className="mt-1 truncate text-[11px] leading-snug text-muted">
        {fundName || "Search a ticker"}
      </p>
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
