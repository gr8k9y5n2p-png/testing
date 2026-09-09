import type { FundEstimateView } from "@/data/types";
import { deltaTone, formatSignedPp } from "@/lib/format";

export function DeltaBadge({
  fund,
  compact = false,
}: {
  fund: FundEstimateView;
  compact?: boolean;
}) {
  if (fund.hasEstimate === false) {
    return (
      <span className="inline-flex items-center rounded-sm bg-paper px-1.5 py-0.5 font-mono text-[11px] font-medium text-muted">
        —
      </span>
    );
  }

  const tone = deltaTone(fund.vsCategoryPctNav);
  // Eric: above category avg = more tax to the client (red / bad).
  // Below = less tax (green/teal / good). Do not use Ledger --above green for +.
  const classes = {
    above: "bg-tax-more-soft text-tax-more",
    below: "bg-tax-less-soft text-tax-less",
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
