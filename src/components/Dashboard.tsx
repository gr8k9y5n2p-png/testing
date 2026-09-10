"use client";

import { useDeferredValue, useEffect, useMemo, useState } from "react";
import {
  FUND_PAGE_SIZE,
  PAID_HISTORY_PAGE_SIZE,
  PAID_HISTORY_PAGE_SIZES,
  clampPaidHistoryPageSize,
  paginateViews,
  type FundPageResult,
} from "@/data/pagination";
import {
  buildSearchTableFunds,
  currentPaidHistoryYear,
  splitFundsByBucket,
} from "@/data";
import { collectTaxYearsFromFunds, mergeTaxYears } from "@/data/tax-years";
import type { Facets, FundEstimateView, SearchFilters } from "@/data/types";
import { ResultsTable } from "@/components/ResultsTable";
import { SearchToolbar } from "@/components/SearchToolbar";
import type { SortDirection, SortKey } from "@/lib/format";
import {
  SEARCH_UPCOMING_DETAIL,
  SEARCH_UPCOMING_HEADING,
} from "@/lib/copy";

async function fetchFundPage(query: {
  filters: SearchFilters;
  sort: SortKey;
  direction: SortDirection;
  limit: number;
  offset: number;
  upcoming?: boolean;
  paidHistory?: boolean;
}): Promise<FundPageResult> {
  const params = new URLSearchParams();
  params.set("limit", String(query.limit));
  params.set("offset", String(query.offset));
  params.set("sort", query.sort);
  params.set("direction", query.direction);
  if (query.upcoming) params.set("upcoming", "1");
  if (query.paidHistory) params.set("paid_history", "1");
  if (query.filters.query) params.set("q", query.filters.query);
  if (!query.filters.query && query.filters.family) {
    params.set("family", query.filters.family);
  }
  if (!query.filters.query && query.filters.category) {
    params.set("category", query.filters.category);
  }
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
    years?: number[];
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
    years: mergeTaxYears(body.years, collectTaxYearsFromFunds(items)),
  };
}

function pageRequestKey(
  filters: SearchFilters,
  sort: SortKey,
  direction: SortDirection,
  offset: number,
) {
  return JSON.stringify({
    query: filters.query ?? "",
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
  ticker,
}: {
  funds: FundEstimateView[];
  facets: Facets;
  onIllustrate?: (fund: FundEstimateView) => void;
  onNotice?: (message: string) => void;
  /** Selected Search ticker — highlight / hydrate in place. Never shrinks Upcoming. */
  ticker?: string | null;
}) {
  const [filters, setFilters] = useState<SearchFilters>(() => ({
    year: currentPaidHistoryYear(),
  }));
  const deferredFilters = useDeferredValue(filters);
  const scopedTicker = ticker?.trim().toUpperCase() || undefined;
  const requestFilters = useMemo<SearchFilters>(
    () => ({
      family: deferredFilters.family,
      category: deferredFilters.category,
    }),
    [deferredFilters.category, deferredFilters.family],
  );
  const [sortKey, setSortKey] = useState<SortKey>("fundName");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");
  const [offset, setOffset] = useState(0);
  const [page, setPage] = useState<FundPageResult>(() =>
    paginateViews(funds, { limit: FUND_PAGE_SIZE, offset: 0 }),
  );
  const [paidLimit, setPaidLimit] = useState(PAID_HISTORY_PAGE_SIZE);
  const [paidOffset, setPaidOffset] = useState(0);
  const [paidPage, setPaidPage] = useState<FundPageResult>({
    items: [],
    total: 0,
    limit: PAID_HISTORY_PAGE_SIZE,
    offset: 0,
  });
  const [focusedItems, setFocusedItems] = useState<FundEstimateView[]>([]);
  const [pageYears, setPageYears] = useState<number[]>(() =>
    mergeTaxYears(facets.years, collectTaxYearsFromFunds(funds)),
  );
  const [appliedKey, setAppliedKey] = useState(() =>
    pageRequestKey({}, "fundName", "asc", 0),
  );
  const paidYear = deferredFilters.year ?? currentPaidHistoryYear();
  const paidRequestKey = JSON.stringify({
    family: requestFilters.family ?? "",
    category: requestFilters.category ?? "",
    year: paidYear,
    limit: paidLimit,
    offset: paidOffset,
  });

  const requestKey = pageRequestKey(
    requestFilters,
    sortKey,
    sortDirection,
    offset,
  );

  useEffect(() => {
    let cancelled = false;
    void fetchFundPage({
      filters: requestFilters,
      sort: sortKey,
      direction: sortDirection,
      limit: FUND_PAGE_SIZE,
      offset,
    })
      .then((next) => {
        if (cancelled) return;
        setPage(next);
        setPageYears((current) => mergeTaxYears(current, next.years));
        setAppliedKey(requestKey);
      })
      .catch(() => {
        if (cancelled) return;
        const fallback = paginateViews(funds, {
          ...requestFilters,
          sort: sortKey,
          direction: sortDirection,
          limit: FUND_PAGE_SIZE,
          offset,
        });
        setPage(fallback);
        setPageYears((current) =>
          mergeTaxYears(current, collectTaxYearsFromFunds(fallback.items)),
        );
        setAppliedKey(requestKey);
      });
    return () => {
      cancelled = true;
    };
  }, [funds, offset, requestFilters, requestKey, sortDirection, sortKey]);

  useEffect(() => {
    let cancelled = false;
    void fetchFundPage({
      filters: { ...requestFilters, year: paidYear },
      sort: sortKey,
      direction: sortDirection,
      limit: paidLimit,
      offset: paidOffset,
      paidHistory: true,
    })
      .then((next) => {
        if (cancelled) return;
        setPaidPage(next);
        if (next.offset !== paidOffset) setPaidOffset(next.offset);
        setPageYears((current) => mergeTaxYears(current, next.years));
      })
      .catch(() => {
        if (cancelled) return;
        setPaidPage({
          items: [],
          total: 0,
          limit: paidLimit,
          offset: paidOffset,
        });
      });
    return () => {
      cancelled = true;
    };
  }, [paidLimit, paidOffset, paidRequestKey, paidYear, requestFilters, sortDirection, sortKey]);

  useEffect(() => {
    if (!scopedTicker) {
      setFocusedItems([]);
      return;
    }
    let cancelled = false;
    void fetchFundPage({
      filters: { query: scopedTicker },
      sort: sortKey,
      direction: sortDirection,
      limit: 10,
      offset: 0,
    })
      .then((next) => {
        if (!cancelled) setFocusedItems(next.items);
      })
      .catch(() => {
        if (!cancelled) setFocusedItems([]);
      });
    return () => {
      cancelled = true;
    };
  }, [scopedTicker, sortDirection, sortKey]);

  const isPending = filters !== deferredFilters || appliedKey !== requestKey;
  const toolbarFacets = useMemo<Facets>(
    () => ({
      ...facets,
      years: mergeTaxYears(
        facets.years,
        pageYears,
        collectTaxYearsFromFunds(page.items),
        collectTaxYearsFromFunds(paidPage.items),
      ),
    }),
    [facets, page.items, pageYears, paidPage.items],
  );

  const tableFunds = useMemo(
    () =>
      buildSearchTableFunds(
        funds,
        [...focusedItems, ...page.items],
        {
          family: deferredFilters.family,
          category: deferredFilters.category,
        },
        scopedTicker,
      ),
    [
      deferredFilters.category,
      deferredFilters.family,
      focusedItems,
      funds,
      page.items,
      scopedTicker,
    ],
  );

  const upcomingCount = useMemo(
    () => splitFundsByBucket(tableFunds).upcoming.length,
    [tableFunds],
  );

  const paidFunds = useMemo(
    () => [...focusedItems, ...paidPage.items],
    [focusedItems, paidPage.items],
  );


  const rangeLabel = `${upcomingCount} unpaid announced`;

  function applyFilters(next: SearchFilters) {
    setFilters(next);
    setOffset(0);
    setPaidOffset(0);
  }

  function applyPaidLimit(next: number) {
    setPaidLimit(clampPaidHistoryPageSize(next));
    setPaidOffset(0);
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
            {SEARCH_UPCOMING_HEADING}
          </h2>
          <p className="mt-1 text-sm text-muted">{SEARCH_UPCOMING_DETAIL}</p>
        </div>
        <p className="font-mono text-xs text-faint" aria-live="polite">
          {isPending ? "Updating…" : rangeLabel}
        </p>
      </div>
      <SearchToolbar
        filters={filters}
        facets={toolbarFacets}
        onChange={applyFilters}
      />
      <div className={isPending ? "opacity-70 transition-opacity" : ""}>
        <ResultsTable
          funds={tableFunds}
          paidFunds={paidFunds}
          onIllustrate={onIllustrate}
          sortKey={sortKey}
          sortDirection={sortDirection}
          onSort={toggleSort}
          year={paidYear}
          years={mergeTaxYears(toolbarFacets.years, [paidYear])}
          onYear={(nextYear) =>
            applyFilters({ ...filters, year: nextYear })
          }
          paidFacets={{
            families: toolbarFacets.families,
            categories: toolbarFacets.categories,
          }}
          paidFamily={filters.family}
          paidCategory={filters.category}
          onPaidFamily={(family) => applyFilters({ ...filters, family })}
          onPaidCategory={(category) => applyFilters({ ...filters, category })}
          highlightedTicker={scopedTicker}
          page={
            upcomingCount > FUND_PAGE_SIZE
              ? {
                  total: upcomingCount,
                  limit: FUND_PAGE_SIZE,
                  offset,
                  onOffset: setOffset,
                }
              : undefined
          }
          paidPage={{
            total: paidPage.total,
            limit: paidPage.limit,
            offset: paidPage.offset,
            onOffset: setPaidOffset,
            onLimit: applyPaidLimit,
            limitOptions: PAID_HISTORY_PAGE_SIZES,
          }}
        />
      </div>
    </section>
  );
}
