import { DATA_SOURCE } from "@/data/types";

export function DemoBanner() {
  return (
    <div className="flex flex-col gap-2 rounded-md border border-line bg-notice px-4 py-3 text-sm text-ink sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 inline-flex shrink-0 rounded-sm border border-line bg-surface px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-muted">
          Sample
        </span>
        <p className="text-muted">
          <span className="font-semibold text-ink">{DATA_SOURCE.label}.</span>{" "}
          {DATA_SOURCE.notice}
        </p>
      </div>
    </div>
  );
}
