import { DATA_SOURCE } from "@/data/types";

export function DemoBanner() {
  return (
    <div className="flex flex-col gap-2 rounded-md border border-gold/25 bg-gold-soft px-4 py-3 text-sm text-navy sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 inline-flex shrink-0 rounded-sm bg-gold px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-white">
          Sample
        </span>
        <p>
          <span className="font-semibold">{DATA_SOURCE.label}.</span>{" "}
          {DATA_SOURCE.notice}
        </p>
      </div>
    </div>
  );
}
