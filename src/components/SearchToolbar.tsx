"use client";

import type { Facets, SearchFilters } from "@/data/types";

/** Homepage Upcoming / Announced filters. Year lives on Paid History only. */
export type UpcomingSearchFilters = Pick<SearchFilters, "family" | "category">;

export function SearchToolbar({
  filters,
  facets,
  onChange,
}: {
  filters: UpcomingSearchFilters;
  facets: Pick<Facets, "families" | "categories">;
  onChange: (next: UpcomingSearchFilters) => void;
}) {
  function update<K extends keyof UpcomingSearchFilters>(
    key: K,
    value: UpcomingSearchFilters[K],
  ) {
    onChange({ ...filters, [key]: value || undefined });
  }

  const selectClass =
    "h-10 w-full min-w-[10rem] rounded-md border border-line bg-surface px-2.5 text-sm text-ink";

  return (
    <div className="mb-4 rounded-lg border border-line bg-surface p-3 shadow-[0_1px_2px_rgba(26,29,26,0.04)]">
      <div className="flex flex-wrap items-end justify-start gap-3">
        <label className="block">
          <span className="mb-1.5 block text-[11px] font-semibold uppercase tracking-[0.12em] text-faint">
            Family
          </span>
          <select
            className={selectClass}
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
        <label className="block">
          <span className="mb-1.5 block text-[11px] font-semibold uppercase tracking-[0.12em] text-faint">
            Category
          </span>
          <select
            className={selectClass}
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
        <button
          type="button"
          onClick={() => onChange({})}
          className="h-10 shrink-0 rounded-md border border-line px-3 text-sm text-muted hover:border-line-strong hover:text-ink"
        >
          Clear
        </button>
      </div>
    </div>
  );
}
