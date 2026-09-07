"use client";

import { useDeferredValue, useMemo, useState } from "react";
import type { Facets, FundEstimateView, SearchFilters } from "@/data/types";
import { searchFunds } from "@/data/queries";
import { EmptyState } from "@/components/EmptyState";
import { ResultsTable } from "@/components/ResultsTable";
import { SearchToolbar } from "@/components/SearchToolbar";

export function Dashboard({
  funds,
  facets,
}: {
  funds: FundEstimateView[];
  facets: Facets;
}) {
  const [filters, setFilters] = useState<SearchFilters>({});
  const deferredFilters = useDeferredValue(filters);

  const results = useMemo(
    () => searchFunds(funds, deferredFilters),
    [funds, deferredFilters],
  );

  const isPending = filters !== deferredFilters;
  const hasActiveFilters = Boolean(
    filters.query?.trim() || filters.family || filters.category || filters.year,
  );

  return (
    <section aria-labelledby="results-heading">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2
            id="results-heading"
            className="font-serif text-xl tracking-tight text-navy"
          >
            All estimates
          </h2>
          <p className="mt-1 text-sm text-muted">
            Filter by name, ticker, CUSIP, family, category, or distribution year.
          </p>
        </div>
        <p className="font-mono text-xs text-faint" aria-live="polite">
          {isPending ? "Updating…" : `${results.length} of ${funds.length} funds`}
        </p>
      </div>
      <SearchToolbar
        filters={filters}
        facets={facets}
        onChange={setFilters}
      />
      <div className={isPending ? "opacity-70 transition-opacity" : ""}>
        {results.length === 0 ? (
          <EmptyState
            hasActiveFilters={hasActiveFilters}
            onClear={() => setFilters({})}
          />
        ) : (
          <ResultsTable funds={results} />
        )}
      </div>
    </section>
  );
}
