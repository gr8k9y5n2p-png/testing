"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { FundEstimateView } from "@/data/types";
import { tickerSlotBorderClass } from "@/components/illustrate/ticker-slot-border";
import {
  LISTS_ADD,
  LISTS_ANNOUNCED_COLUMN,
  LISTS_DETAIL,
  LISTS_DIST_COLUMN,
  LISTS_EMPTY,
  LISTS_EX_COLUMN,
  LISTS_HEADING,
  LISTS_INPUT_PLACEHOLDER,
  LISTS_NAV_COLUMN,
  LISTS_NOT_FOUND,
  LISTS_PCT_COLUMN,
  LISTS_RECORD_COLUMN,
  SEARCH_UPCOMING_KICKER,
} from "@/lib/copy";
import { formatOptionalDate, formatUsd } from "@/lib/format";
import { formatSoftNav, formatSoftPct, SOFT_DASH } from "@/lib/illustrate/nav-math";
import { UPCOMING_AMOUNT_UNAVAILABLE } from "@/lib/illustrate/portfolio-compare-copy";
import {
  listsTickersPath,
  mergeTickerLists,
  removeTicker,
} from "@/lib/lists/parse-tickers";
import {
  LIST_HYDRATE_MAX_ATTEMPTS,
  listHydrateBackoffMs,
  listRowsAfterFailedHydrate,
  listRowsFromApiResponse,
  needsListHydrate,
} from "@/lib/lists/hydrate";
import {
  emptyListRow,
  LIST_ESTIMATE_TYPE_LABELS,
  LIST_ESTIMATE_TYPES,
  type ListRow,
} from "@/lib/lists/rows";

const inputClass =
  "h-11 w-full rounded-md border border-line bg-surface px-3 text-sm text-ink placeholder:text-faint";

async function fetchListRows(tickers: string[]): Promise<ListRow[]> {
  if (!tickers.length) return [];
  const params = new URLSearchParams();
  params.set("tickers", tickers.join(","));
  const response = await fetch(`/api/lists?${params.toString()}`, {
    cache: "no-store",
  });
  const body = await response.json().catch(() => null);
  return listRowsFromApiResponse(tickers, body, response.ok);
}

function SoftCell({
  value,
  loading,
}: {
  value: string;
  loading?: boolean;
}) {
  if (loading) {
    return <span className="font-mono text-[11px] text-faint">…</span>;
  }
  const empty = value === SOFT_DASH || value === UPCOMING_AMOUNT_UNAVAILABLE;
  return (
    <span
      className={`font-mono tabular-nums ${
        empty ? "text-[11px] leading-snug text-muted" : "text-[13px] text-ink"
      }`}
    >
      {value}
    </span>
  );
}

function DistCell({ row }: { row: ListRow }) {
  if (row.status === "loading") {
    return <span className="font-mono text-[11px] text-faint">…</span>;
  }
  if (row.status === "not_found") {
    return (
      <span className="font-mono text-[11px] leading-snug text-muted">{SOFT_DASH}</span>
    );
  }
  if (row.status === "undisclosed" || row.distPerShare == null) {
    return (
      <span className="font-mono text-[11px] leading-snug text-muted">
        {UPCOMING_AMOUNT_UNAVAILABLE}
      </span>
    );
  }
  return (
    <span className="font-mono text-[13px] font-medium tabular-nums text-ink">
      {formatUsd(row.distPerShare, 4)} / sh
    </span>
  );
}

function catalogHint(ticker: string, funds: FundEstimateView[]): ListRow {
  const fund = funds.find((item) => item.ticker === ticker);
  if (!fund) return emptyListRow(ticker, "loading");
  return {
    ...emptyListRow(ticker, "loading"),
    fundName: fund.fundName && fund.fundName !== "—" ? fund.fundName : null,
    family: fund.family && fund.family !== "—" ? fund.family : null,
    nav: fund.nav > 0 ? fund.nav : null,
    navAsOf: fund.navAsOf ?? null,
    found: true,
  };
}

export function ListsWorkspace({
  funds,
  initialTickers = [],
  initialRows = [],
}: {
  funds: FundEstimateView[];
  initialTickers?: string[];
  initialRows?: ListRow[];
}) {
  const [draft, setDraft] = useState("");
  const [tickers, setTickers] = useState<string[]>(initialTickers);
  const [rowsByTicker, setRowsByTicker] = useState<Record<string, ListRow>>(() => {
    const map: Record<string, ListRow> = {};
    for (const row of initialRows) map[row.ticker] = row;
    return map;
  });
  const rowsByTickerRef = useRef(rowsByTicker);
  rowsByTickerRef.current = rowsByTicker;

  const rows = useMemo(
    () =>
      tickers.map((ticker) => rowsByTicker[ticker] ?? catalogHint(ticker, funds)),
    [funds, rowsByTicker, tickers],
  );

  useEffect(() => {
    const path = listsTickersPath(tickers);
    if (`${window.location.pathname}${window.location.search}` !== path) {
      window.history.replaceState(null, "", path);
    }
  }, [tickers]);

  useEffect(() => {
    let cancelled = false;

    function unresolved(): string[] {
      return tickers.filter((ticker) =>
        needsListHydrate(rowsByTickerRef.current[ticker], 0),
      );
    }

    async function hydrate() {
      for (let attempt = 0; attempt < LIST_HYDRATE_MAX_ATTEMPTS; attempt += 1) {
        const missing = unresolved();
        if (!missing.length || cancelled) return;
        const wait = listHydrateBackoffMs(attempt);
        if (wait) {
          await new Promise((resolve) => window.setTimeout(resolve, wait));
          if (cancelled) return;
        }
        try {
          const fetched = await fetchListRows(missing);
          if (cancelled) return;
          setRowsByTicker((current) => {
            const merged = { ...current };
            for (const row of fetched) merged[row.ticker] = row;
            return merged;
          });
          const stillMissing = missing.filter((ticker) => {
            const row = fetched.find((item) => item.ticker === ticker);
            return !row || row.status === "not_found" || row.status === "loading";
          });
          if (!stillMissing.length) return;
        } catch {
          if (cancelled) return;
          if (attempt === LIST_HYDRATE_MAX_ATTEMPTS - 1) {
            setRowsByTicker((current) => {
              const merged = { ...current };
              for (const row of listRowsAfterFailedHydrate(missing)) {
                if (!merged[row.ticker] || merged[row.ticker]?.status === "loading") {
                  merged[row.ticker] = row;
                }
              }
              return merged;
            });
          }
        }
      }
    }

    void hydrate();
    return () => {
      cancelled = true;
    };
  }, [tickers]);

  function commitDraft(raw = draft) {
    const next = mergeTickerLists(tickers, raw);
    setTickers(next);
    setDraft("");
  }

  function onRemove(ticker: string) {
    setTickers((current) => removeTicker(current, ticker));
    setRowsByTicker((current) => {
      const rest = { ...current };
      delete rest[ticker];
      return rest;
    });
  }

  return (
    <section aria-labelledby="lists-heading">
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-faint">
        {SEARCH_UPCOMING_KICKER}
      </p>
      <h1
        id="lists-heading"
        className="mt-1 font-serif text-2xl tracking-tight text-ink"
      >
        {LISTS_HEADING}
      </h1>
      <p className="mt-2 max-w-2xl text-sm text-muted">{LISTS_DETAIL}</p>

      <form
        className="mt-6 flex flex-col gap-2 sm:flex-row sm:items-center"
        onSubmit={(event) => {
          event.preventDefault();
          commitDraft();
        }}
      >
        <label className="sr-only" htmlFor="lists-tickers">
          Tickers
        </label>
        <input
          id="lists-tickers"
          className={inputClass}
          value={draft}
          placeholder={LISTS_INPUT_PLACEHOLDER}
          autoComplete="off"
          spellCheck={false}
          onChange={(event) => setDraft(event.target.value)}
          onPaste={(event) => {
            const pasted = event.clipboardData.getData("text");
            if (!pasted || !/[,;\n\r]/.test(pasted)) return;
            event.preventDefault();
            commitDraft(`${draft} ${pasted}`);
          }}
        />
        <button
          type="submit"
          className="h-11 shrink-0 rounded-md bg-accent px-4 text-sm font-medium text-white hover:bg-accent-hover"
        >
          {LISTS_ADD}
        </button>
      </form>

      {tickers.length === 0 ? (
        <div className="mt-8 rounded-lg border border-dashed border-line-strong bg-surface px-6 py-16 text-center">
          <p className="font-serif text-lg text-ink">{LISTS_EMPTY}</p>
        </div>
      ) : (
        <div className="mt-6 overflow-x-auto rounded-xl border border-line bg-surface">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-line bg-paper text-[11px] font-semibold uppercase tracking-[0.1em] text-faint">
              <tr>
                <th className="sticky left-0 z-10 bg-paper px-3 py-2.5">Ticker</th>
                <th className="px-3 py-2.5 text-right">{LISTS_NAV_COLUMN}</th>
                <th className="px-3 py-2.5 text-right">{LISTS_DIST_COLUMN}</th>
                <th className="px-3 py-2.5 text-right">{LISTS_PCT_COLUMN}</th>
                {LIST_ESTIMATE_TYPES.map((type) => (
                  <th key={type} className="px-3 py-2.5 text-right">
                    {LIST_ESTIMATE_TYPE_LABELS[type]}
                  </th>
                ))}
                <th className="px-3 py-2.5">{LISTS_ANNOUNCED_COLUMN}</th>
                <th className="px-3 py-2.5">{LISTS_RECORD_COLUMN}</th>
                <th className="px-3 py-2.5">{LISTS_EX_COLUMN}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {rows.map((row) => {
                const pct =
                  row.status === "upcoming"
                    ? formatSoftPct(row.pctOfNav)
                    : row.status === "undisclosed"
                      ? UPCOMING_AMOUNT_UNAVAILABLE
                      : SOFT_DASH;
                return (
                  <tr key={row.ticker} className="align-top">
                    <td className="sticky left-0 z-10 bg-surface px-3 py-3">
                      <TickerStackItem
                        row={row}
                        onRemove={() => onRemove(row.ticker)}
                      />
                    </td>
                    <td className="whitespace-nowrap px-3 py-3 text-right">
                      <SoftCell
                        loading={row.status === "loading" && row.nav == null}
                        value={formatSoftNav(row.nav)}
                      />
                    </td>
                    <td className="whitespace-nowrap px-3 py-3 text-right">
                      <DistCell row={row} />
                    </td>
                    <td className="whitespace-nowrap px-3 py-3 text-right">
                      <SoftCell
                        loading={row.status === "loading"}
                        value={pct}
                      />
                    </td>
                    {LIST_ESTIMATE_TYPES.map((type) => (
                      <td
                        key={type}
                        className="whitespace-nowrap px-3 py-3 text-right"
                      >
                        <SoftCell
                          loading={row.status === "loading"}
                          value={
                            row.status === "upcoming" &&
                            row.estimateTypes[type] != null
                              ? formatUsd(row.estimateTypes[type] as number, 4)
                              : SOFT_DASH
                          }
                        />
                      </td>
                    ))}
                    <td className="whitespace-nowrap px-3 py-3">
                      <SoftCell
                        loading={row.status === "loading"}
                        value={formatOptionalDate(row.asOfDate)}
                      />
                    </td>
                    <td className="whitespace-nowrap px-3 py-3">
                      <SoftCell
                        loading={row.status === "loading"}
                        value={formatOptionalDate(row.recordDate)}
                      />
                    </td>
                    <td className="whitespace-nowrap px-3 py-3">
                      <SoftCell
                        loading={row.status === "loading"}
                        value={formatOptionalDate(row.exDate)}
                      />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function TickerStackItem({
  row,
  onRemove,
}: {
  row: ListRow;
  onRemove: () => void;
}) {
  return (
    <div
      className={`flex min-w-[8.5rem] items-start justify-between gap-2 rounded-md border px-2 py-1.5 ${tickerSlotBorderClass(
        { committed: true, midEdit: row.status === "loading" },
      )}`}
    >
      <div className="min-w-0">
        <p className="font-mono text-sm font-medium text-ink">{row.ticker}</p>
        {row.fundName ? (
          <p className="mt-0.5 truncate text-[11px] leading-snug text-muted">
            {row.fundName}
          </p>
        ) : null}
        {row.status === "not_found" ? (
          <p className="mt-0.5 text-[10px] font-semibold uppercase tracking-[0.08em] text-muted">
            {LISTS_NOT_FOUND}
          </p>
        ) : null}
        {row.status === "undisclosed" ? (
          <p className="mt-0.5 text-[10px] font-semibold uppercase tracking-[0.08em] text-muted">
            {UPCOMING_AMOUNT_UNAVAILABLE}
          </p>
        ) : null}
      </div>
      <button
        type="button"
        onClick={onRemove}
        aria-label={`Remove ${row.ticker}`}
        className="shrink-0 rounded px-1 text-xs text-muted hover:text-ink"
      >
        ×
      </button>
    </div>
  );
}
