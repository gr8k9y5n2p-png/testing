import type { FundEstimate } from "@/data/types";
import { publicationStageLabel } from "@/data/distribution-bucket";
import { formatOptionalDate } from "@/lib/format";

export type DateStripSource = Pick<
  FundEstimate,
  "asOfDate" | "recordDate" | "exDate" | "payableDate" | "publicationStage" | "bucket"
>;

/**
 * FIGFX-style date strip. `as_of` is labeled Announced — do not invent
 * announced_date.
 */
export function DistributionDateStrip({
  fund,
  compact = false,
  showPayable = true,
  showStage = false,
  className = "",
}: {
  fund: DateStripSource;
  compact?: boolean;
  showPayable?: boolean;
  showStage?: boolean;
  className?: string;
}) {
  const items = [
    { label: "Announced", value: fund.asOfDate },
    { label: "Record", value: fund.recordDate },
    { label: "Ex-div", value: fund.exDate },
    ...(showPayable ? [{ label: "Payable", value: fund.payableDate }] : []),
  ].filter((item) => item.value);

  if (items.length === 0) return null;

  const stage = showStage ? publicationStageLabel(fund.publicationStage) : "";

  return (
    <p
      className={`flex flex-wrap items-baseline gap-x-2.5 gap-y-0.5 font-mono text-[11px] text-faint ${className}`}
    >
      {items.map((item) => (
        <span key={item.label}>
          <span className="uppercase tracking-[0.08em]">{item.label}</span>{" "}
          <span className="text-muted">{formatOptionalDate(item.value, compact)}</span>
        </span>
      ))}
      {stage ? (
        <span className="text-muted">
          {fund.bucket === "paid" ? "Paid history" : "Upcoming"} · {stage}
        </span>
      ) : null}
    </p>
  );
}
