import type { IllustrateResponse } from "@/lib/illustrate/types";
import { Disclaimer } from "@/components/Disclaimer";
import { formatRatePct, formatUsdRange } from "@/lib/format";

const ESTIMATE_LABELS: Record<string, string> = {
  ordinary_income: "Ordinary income",
  long_term_capital_gains: "Long-term capital gains",
  short_term_capital_gains: "Short-term capital gains",
  qualified_dividend: "Qualified dividends",
  total_capital_gains: "Total capital gains",
  special_dividend: "Special dividend",
  return_of_capital: "Return of capital",
  total: "Total (treated as ordinary)",
};

export function IllustrationResults({
  result,
}: {
  result: IllustrateResponse;
}) {
  const { totals, components, warnings } = result;

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2">
        <StatCard
          label="Estimated distribution"
          value={formatUsdRange(
            totals.distribution_dollars,
            totals.distribution_dollars_min,
            totals.distribution_dollars_max,
          )}
        />
        <StatCard
          label="Estimated tax"
          value={formatUsdRange(
            totals.estimated_tax_dollars,
            totals.estimated_tax_dollars_min,
            totals.estimated_tax_dollars_max,
          )}
          emphasize
        />
      </div>

      <div className="overflow-hidden rounded-md border border-line">
        <table className="min-w-full text-sm">
          <thead className="bg-paper text-[11px] font-semibold uppercase tracking-[0.1em] text-faint">
            <tr>
              <th className="px-3 py-2 text-left">Component</th>
              <th className="px-3 py-2 text-right">Distribution</th>
              <th className="px-3 py-2 text-right">Effective rate</th>
              <th className="px-3 py-2 text-right">Est. tax</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {components.map((component) => (
              <tr key={component.distribution_id}>
                <td className="px-3 py-2">
                  <span className="block text-ink">
                    {ESTIMATE_LABELS[component.estimate_type] ?? component.estimate_type}
                  </span>
                  <span className="font-mono text-[11px] text-faint">
                    {component.amount_unit}
                    {component.publication_stage
                      ? ` · ${component.publication_stage}`
                      : ""}
                  </span>
                </td>
                <td className="px-3 py-2 text-right font-mono">
                  {formatUsdRange(
                    component.distribution_dollars,
                    component.distribution_dollars_min,
                    component.distribution_dollars_max,
                  )}
                </td>
                <td className="px-3 py-2 text-right font-mono text-muted">
                  {formatRatePct(component.effective_rate)}
                  <span className="block text-[11px] text-faint">
                    fed {formatRatePct(component.federal_rate)}
                    {component.state_rate
                      ? ` + st ${formatRatePct(component.state_rate)}`
                      : ""}
                  </span>
                </td>
                <td className="px-3 py-2 text-right font-mono">
                  {formatUsdRange(
                    component.estimated_tax_dollars,
                    component.estimated_tax_dollars_min,
                    component.estimated_tax_dollars_max,
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {warnings.length > 0 ? (
        <ul className="space-y-1 text-xs text-muted">
          {warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      ) : null}

      <Disclaimer />
    </div>
  );
}

function StatCard({
  label,
  value,
  emphasize = false,
}: {
  label: string;
  value: string;
  emphasize?: boolean;
}) {
  return (
    <div
      className={`rounded-md border px-4 py-3 ${
        emphasize ? "border-accent/25 bg-accent-soft" : "border-line bg-paper"
      }`}
    >
      <p
        className={`text-[11px] font-semibold uppercase tracking-[0.12em] ${
          emphasize ? "text-accent" : "text-faint"
        }`}
      >
        {label}
      </p>
      <p
        className={`mt-1 font-serif text-2xl tracking-tight ${
          emphasize ? "text-accent" : "text-ink"
        }`}
      >
        {value}
      </p>
    </div>
  );
}
