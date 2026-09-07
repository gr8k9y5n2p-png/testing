import type { FundEstimateView } from "@/data/types";
import { deltaTone, formatSignedPp } from "@/lib/format";

export function DeltaBadge({
  fund,
  compact = false,
}: {
  fund: FundEstimateView;
  compact?: boolean;
}) {
  const tone = deltaTone(fund.vsCategoryPctNav);
  const classes = {
    above: "bg-above-soft text-above",
    below: "bg-below-soft text-below",
    neutral: "bg-paper text-muted",
  }[tone];

  return (
    <span
      className={`inline-flex items-center rounded-sm px-1.5 py-0.5 font-mono text-[11px] font-medium ${classes}`}
    >
      {formatSignedPp(fund.vsCategoryPctNav)}
      {compact ? null : (
        <span className="ml-1 font-sans font-normal opacity-70">vs cat.</span>
      )}
    </span>
  );
}
