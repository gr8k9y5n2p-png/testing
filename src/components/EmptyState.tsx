export function EmptyState({
  hasActiveFilters,
  onClear,
}: {
  hasActiveFilters: boolean;
  onClear: () => void;
}) {
  return (
    <div className="rounded-lg border border-dashed border-line-strong bg-surface px-6 py-16 text-center">
      <p className="font-serif text-lg text-navy">No funds match this search</p>
      <p className="mx-auto mt-2 max-w-md text-sm text-muted">
        Try a ticker, CUSIP, fund family, category, or distribution year. Sample
        coverage includes American Funds, Vanguard, Fidelity, and T. Rowe Price.
      </p>
      {hasActiveFilters ? (
        <button
          type="button"
          onClick={onClear}
          className="mt-5 inline-flex h-9 items-center rounded-md bg-navy px-3 text-sm text-white hover:bg-navy-deep"
        >
          Clear filters
        </button>
      ) : null}
    </div>
  );
}
