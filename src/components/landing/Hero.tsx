import { COPY } from "@/lib/copy";

export function Hero({
  onSearch,
  onImport,
}: {
  onSearch: () => void;
  onImport: () => void;
}) {
  return (
    <section className="mb-8 max-w-3xl pt-4">
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-teal">
        Aftertax
      </p>
      <h1 className="mt-2 font-serif text-3xl tracking-tight text-navy sm:text-[2.35rem] sm:leading-tight">
        {COPY.hero}
      </h1>
      <p className="mt-3 text-[16px] leading-relaxed text-muted">{COPY.sub}</p>
      <div className="mt-5 flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={onSearch}
          className="inline-flex h-11 items-center rounded-md bg-navy px-4 text-sm font-medium text-white hover:bg-navy-deep"
        >
          {COPY.searchCta}
        </button>
        <button
          type="button"
          onClick={onImport}
          className="inline-flex h-11 items-center rounded-md border border-line px-4 text-sm text-ink hover:border-line-strong"
        >
          {COPY.importCta}
        </button>
      </div>
      <p className="mt-4 text-xs text-faint">{COPY.trust}</p>
    </section>
  );
}
