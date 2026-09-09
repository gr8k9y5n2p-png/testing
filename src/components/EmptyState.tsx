export function EmptyState({
  hasActiveFilters,
  universeEmpty = false,
  onClear,
}: {
  hasActiveFilters: boolean;
  universeEmpty?: boolean;
  onClear: () => void;
}) {
  const headline = universeEmpty
    ? "No live estimates"
    : "No funds match this search";
  const detail = universeEmpty
    ? "Search and Sample Estimates read the Data API only. Uncovered or missing funds stay empty, N/A, or Undisclosed — they are not backfilled from demo data."
    : "Try a ticker, CUSIP, fund family, category, or distribution year from the live Data API.";

  return (
    <div className="rounded-lg border border-dashed border-line-strong bg-surface px-6 py-16 text-center">
      <p className="font-serif text-lg text-ink">{headline}</p>
      <p className="mx-auto mt-2 max-w-md text-sm text-muted">{detail}</p>
      <p className="mx-auto mt-2 max-w-md text-sm text-muted">
        <a href="#request-a-fund" className="text-accent underline">
          Request a fund
        </a>{" "}
        if you want us to look for issuer sources.
      </p>
      {hasActiveFilters && !universeEmpty ? (
        <button
          type="button"
          onClick={onClear}
          className="mt-5 inline-flex h-9 items-center rounded-md bg-accent px-3 text-sm text-white hover:bg-accent-hover"
        >
          Clear filters
        </button>
      ) : null}
    </div>
  );
}
