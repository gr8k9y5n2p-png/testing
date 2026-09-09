import {
  COMPARE_DELTA_STRIP_LABELS,
  reservedDeltaStrip,
  type CompareDeltaStripItem,
} from "@/lib/illustrate/compare-delta-strip";

const POLARITY_TEXT = {
  more: "text-tax-more",
  less: "text-tax-less",
  even: "text-ink",
} as const;

export function CompareDeltaStrip({
  items,
  className = "",
}: {
  items?: CompareDeltaStripItem[];
  className?: string;
}) {
  const cells = items?.length === 4 ? items : reservedDeltaStrip();

  return (
    <section
      aria-label="Compare delta strip"
      className={`w-full rounded-2xl border border-dashed border-line bg-surface/80 px-4 py-3 ${className}`}
    >
      <header className="mb-2 flex flex-wrap items-end justify-between gap-2">
        <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-faint">
          Delta strip
        </p>
        <p className="text-[10px] text-muted">
          reserved · pair Δ when two funds · never invent $0
        </p>
      </header>
      <dl className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {cells.map((item) => (
          <div key={item.key} className="min-w-0">
            <dt className="text-[10px] font-semibold uppercase tracking-[0.12em] text-faint">
              {item.label || COMPARE_DELTA_STRIP_LABELS[item.key]}
            </dt>
            <dd
              className={`mt-1 font-serif text-[17px] leading-tight tracking-tight ${
                item.headline
                  ? POLARITY_TEXT[item.polarity ?? "even"]
                  : "text-faint"
              }`}
            >
              {item.headline ?? "—"}
            </dd>
            <dd className="mt-0.5 text-[10px] leading-snug text-faint">{item.detail}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
