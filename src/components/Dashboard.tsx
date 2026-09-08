"use client";

import { useDeferredValue, useEffect, useMemo, useState } from "react";
import {
  FUND_PAGE_SIZE,
  paginateViews,
  type FundPageResult,
} from "@/data/pagination";
import type { Facets, FundEstimateView, SearchFilters } from "@/data/types";
import { EmptyState } from "@/components/EmptyState";
import { ResultsTable } from "@/components/ResultsTable";
import { SearchToolbar } from "@/components/SearchToolbar";
import type { SortDirection, SortKey } from "@/lib/format";

async function fetchFundPage(query: {
  filters: SearchFilters;
  sort: SortKey;
  direction: SortDirection;
  limit: number;
  offset: number;
}): Promise<FundPageResult> {
  const params = new URLSearchParams();
  params.set("limit", String(query.limit));
  params.set("offset", String(query.offset));
  params.set("sort", query.sort);
  params.set("direction", query.direction);
  if (query.filters.query?.trim()) params.set("q", query.filters.query.trim());
  if (query.filters.family) params.set("family", query.filters.family);
  if (query.filters.category) params.set("category", query.filters.category);
  if (query.filters.year) params.set("year", String(query.filters.year));

  const response = await fetch(`/api/funds?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`funds page ${response.status}`);
  }
  const body = (await response.json()) as {
    items?: FundEstimateView[];
    data?: FundEstimateView[];
    total?: number;
    count?: number;
    limit?: number;
    offset?: number;
  };
  const items = Array.isArray(body.items)
    ? body.items
    : Array.isArray(body.data)
      ? body.data
      : [];
  return {
    items,
    total: typeof body.total === "number" ? body.total : (body.count ?? items.length),
    limit: typeof body.limit === "number" ? body.limit : query.limit,
    offset: typeof body.offset === "number" ? body.offset : query.offset,
  };
}

function pageRequestKey(
  filters: SearchFilters,
  sort: SortKey,
  direction: SortDirection,
  offset: number,
) {
  return JSON.stringify({
    q: filters.query ?? "",
    family: filters.family ?? "",
    category: filters.category ?? "",
    year: filters.year ?? "",
    sort,
    direction,
    offset,
  });
}

export function Dashboard({
  funds,
  facets,
  onIllustrate,
}: {
  funds: FundEstimateView[];
  facets: Facets;
  onIllustrate?: (fund: FundEstimateView) => void;
}) {
  const [filters, setFilters] = useState<SearchFilters>({});
  const deferredFilters = useDeferredValue(filters);
  const [sortKey, setSortKey] = useState<SortKey>("fundName");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");
  const [offset, setOffset] = useState(0);
  const [page, setPage] = useState<FundPageResult>(() =>
    paginateViews(funds, { limit: FUND_PAGE_SIZE, offset: 0 }),
  );
  const [appliedKey, setAppliedKey] = useState(() =>
    pageRequestKey({}, "fundName", "asc", 0),
  );

  const requestKey = pageRequestKey(
    deferredFilters,
    sortKey,
    sortDirection,
    offset,
  );

  useEffect(() => {
    let cancelled = false;
    void fetchFundPage({
      filters: deferredFilters,
      sort: sortKey,
      direction: sortDirection,
      limit: FUND_PAGE_SIZE,
      offset,
    })
      .then((next) => {
        if (cancelled) return;
        setPage(next);
        setAppliedKey(requestKey);
      })
      .catch(() => {
        if (cancelled) return;
        setPage(
          paginateViews(funds, {
            ...deferredFilters,
            sort: sortKey,
            direction: sortDirection,
            limit: FUND_PAGE_SIZE,
            offset,
          }),
        );
        setAppliedKey(requestKey);
      });
    return () => {
      cancelled = true;
    };
  }, [deferredFilters, funds, offset, requestKey, sortDirection, sortKey]);

  const isPending = filters !== deferredFilters || appliedKey !== requestKey;
  const hasActiveFilters = Boolean(
    filters.query?.trim() || filters.family || filters.category || filters.year,
  );

  const rangeLabel = useMemo(() => {
    if (page.total === 0) return `0 of ${page.total} funds`;
    const from = page.offset + 1;
    const to = Math.min(page.offset + page.items.length, page.total);
    return `${from}–${to} of ${page.total} funds`;
  }, [page]);

  function applyFilters(next: SearchFilters) {
    setFilters(next);
    setOffset(0);
  }

  function toggleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDirection((current) => (current === "asc" ? "desc" : "asc"));
      setOffset(0);
      return;
    }
    setSortKey(key);
    setSortDirection(
      key === "fundName" || key === "family" || key === "category" ? "asc" : "desc",
    );
    setOffset(0);
  }

  return (
    <section aria-labelledby="results-heading">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2
            id="results-heading"
            className="font-serif text-xl tracking-tight text-ink"
          >
            Sample estimates
          </h2>
          <p className="mt-1 text-sm text-muted">
            Filter by name, ticker, CUSIP, family, category, or distribution year.
            Upcoming estimates stay separate from paid history.
          </p>
        </div>
        <p className="font-mono text-xs text-faint" aria-live="polite">
          {isPending ? "Updating…" : rangeLabel}
        </p>
      </div>
      <SearchToolbar
        filters={filters}
        facets={facets}
        onChange={applyFilters}
      />
      <div className={isPending ? "opacity-70 transition-opacity" : ""}>
        {page.total === 0 ? (
          <EmptyState
            hasActiveFilters={hasActiveFilters}
            onClear={() => applyFilters({})}
          />
        ) : (
          <ResultsTable
            funds={page.items}
            onIllustrate={onIllustrate}
            sortKey={sortKey}
            sortDirection={sortDirection}
            onSort={toggleSort}
            page={{
              total: page.total,
              limit: page.limit,
              offset: page.offset,
              onOffset: setOffset,
            }}
          />
        )}
      </div>
    </section>
  );
}
