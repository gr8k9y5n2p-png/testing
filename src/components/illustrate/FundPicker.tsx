"use client";

import { useMemo, useState } from "react";
import type { FundEstimateView } from "@/data/types";
import { searchFunds } from "@/data/queries";
import { COPY } from "@/lib/copy";
import { isLiveCoveredFamily } from "@/lib/coverage";

export function FundPicker({
  funds,
  selected,
  onSelect,
  inputId = "fund-search",
  autoFocus = false,
}: {
  funds: FundEstimateView[];
  selected: FundEstimateView | null;
  onSelect: (fund: FundEstimateView) => void;
  inputId?: string;
  autoFocus?: boolean;
}) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);

  const matches = useMemo(
    () => searchFunds(funds, { query }).slice(0, 8),
    [funds, query],
  );

  return (
    <div className="relative">
      <label htmlFor={inputId} className="mb-1.5 block text-[11px] font-semibold uppercase tracking-[0.12em] text-faint">
        {COPY.searchCta}
      </label>
      <input
        id={inputId}
        type="search"
        value={selected && !open ? `${selected.ticker} · ${selected.fundName}` : query}
        onChange={(event) => {
          setQuery(event.target.value);
          setOpen(true);
        }}
        onFocus={() => {
          setOpen(true);
          if (selected) setQuery("");
        }}
        onBlur={() => {
          window.setTimeout(() => setOpen(false), 120);
        }}
        placeholder="Ticker, name, CUSIP, or family"
        className="h-12 w-full rounded-md border border-line bg-surface px-3 text-base text-ink placeholder:text-faint"
        autoComplete="off"
        autoFocus={autoFocus}
      />
      {open ? (
        <ul className="absolute z-20 mt-1 max-h-72 w-full overflow-auto rounded-md border border-line bg-surface shadow-lg">
          {matches.length === 0 ? (
            <li className="px-3 py-3 text-sm text-muted">No funds match.</li>
          ) : (
            matches.map((fund) => (
              <li key={fund.id}>
                <button
                  type="button"
                  className="flex w-full items-start justify-between gap-3 px-3 py-2.5 text-left hover:bg-paper"
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => {
                    onSelect(fund);
                    setQuery("");
                    setOpen(false);
                  }}
                >
                  <span>
                    <span className="block text-sm font-medium text-ink">
                      {fund.fundName}
                    </span>
                    <span className="font-mono text-[11px] text-faint">
                      {fund.ticker} · {fund.family}
                    </span>
                  </span>
                  {!isLiveCoveredFamily(fund.family) ? (
                    <span className="mt-0.5 shrink-0 rounded-sm bg-gold-soft px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.08em] text-gold">
                      Gap
                    </span>
                  ) : (
                    <span className="mt-0.5 shrink-0 rounded-sm bg-above-soft px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.08em] text-above">
                      Live
                    </span>
                  )}
                </button>
              </li>
            ))
          )}
        </ul>
      ) : null}
    </div>
  );
}
