"use client";

import type { Facets, SearchFilters } from "@/data/types";

export function SearchToolbar({
  filters,
  facets,
  onChange,
}: {
  filters: SearchFilters;
  facets: Facets;
  onChange: (next: SearchFilters) => void;
}) {
  function update<K extends keyof SearchFilters>(key: K, value: SearchFilters[K]) {
    onChange({ ...filters, [key]: value || undefined });
  }

  const selectClass =
    "h-10 rounded-md border border-line bg-surface px-2.5 text-sm text-ink";

  return (
    <div className="mb-4 rounded-lg border border-line bg-surface p-3 shadow-[0_1px_2px_rgba(28,51,72,0.04)]">
      <div className="grid gap-3 lg:grid-cols-12">
        <label className="block lg:col-span-6">
          <span className="mb-1.5 block text-[11px] font-semibold uppercase tracking-[0.12em] text-faint">
            Search
          </span>
          <input
            type="search"
            value={filters.query ?? ""}
            onChange={(event) => update("query", event.target.value)}
            placeholder="Fund name, ticker, CUSIP, family, category, or year"
            className="h-10 w-full rounded-md border border-line bg-paper px-3 text-sm text-ink placeholder:text-faint"
          />
        </label>
        <label className="block lg:col-span-2">
          <span className="mb-1.5 block text-[11px] font-semibold uppercase tracking-[0.12em] text-faint">
            Family
          </span>
          <select
            className={`${selectClass} w-full`}
            value={filters.family ?? ""}
            onChange={(event) => update("family", event.target.value)}
          >
            <option value="">All families</option>
            {facets.families.map((family) => (
              <option key={family} value={family}>
                {family}
              </option>
            ))}
          </select>
        </label>
        <label className="block lg:col-span-2">
          <span className="mb-1.5 block text-[11px] font-semibold uppercase tracking-[0.12em] text-faint">
            Category
          </span>
          <select
            className={`${selectClass} w-full`}
            value={filters.category ?? ""}
            onChange={(event) => update("category", event.target.value)}
          >
            <option value="">All categories</option>
            {facets.categories.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
        </label>
        <div className="flex flex-col lg:col-span-2">
          <span className="mb-1.5 block text-[11px] font-semibold uppercase tracking-[0.12em] text-faint">
            Year
          </span>
          <div className="flex gap-2">
            <select
              className={`${selectClass} min-w-0 flex-1`}
              value={filters.year ?? ""}
              onChange={(event) =>
                update("year", event.target.value ? Number(event.target.value) : undefined)
              }
              aria-label="Distribution year"
            >
              <option value="">All years</option>
              {facets.years.map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={() => onChange({})}
              className="h-10 shrink-0 rounded-md border border-line px-3 text-sm text-muted hover:border-line-strong hover:text-ink"
            >
              Clear
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
