import { formatPct, formatUsd } from "@/lib/format";
import type { PortfolioIllustrateResponse } from "@/lib/illustrate/portfolio";

export function PortfolioCoverageCard({
  result,
}: {
  result: PortfolioIllustrateResponse;
}) {
  const { coverage, gaps, warnings } = result;
  const uncovered = coverage.dollars_uncovered > 0 || gaps.length > 0;

  return (
    <div
      className={`rounded-md border px-4 py-3 ${
        uncovered ? "border-gold/30 bg-gold-soft" : "border-line bg-paper"
      }`}
    >
      <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-faint">
        Portfolio coverage
      </p>
      <p className="mt-1 font-serif text-xl tracking-tight text-navy">
        {formatPct(coverage.coverage_pct, 1)} covered
      </p>
      <p className="mt-1 text-xs text-muted">
        {formatUsd(coverage.dollars_covered, 0)} covered ·{" "}
        {formatUsd(coverage.dollars_uncovered, 0)} uncovered
        {coverage.dollars_total
          ? ` of ${formatUsd(coverage.dollars_total, 0)}`
          : ""}
      </p>
      {gaps.length > 0 ? (
        <ul className="mt-2 space-y-1 text-xs text-navy">
          {gaps.map((gap, index) => (
            <li key={`${gap.ticker ?? "gap"}-${index}`}>
              Coverage gap
              {gap.ticker ? ` · ${gap.ticker}` : ""}
              {gap.fund_family ? ` · ${gap.fund_family}` : ""}: {gap.reason}
            </li>
          ))}
        </ul>
      ) : null}
      {warnings.length > 0 ? (
        <ul className="mt-2 space-y-1 text-xs text-gold">
          {warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
