import {
  GROWTH_TAX_ESTIMATE_TYPES,
  GROWTH_TAX_TYPE_COLORS,
  GROWTH_TAX_TYPE_LABELS,
  formatGrowthTaxCell,
  type GrowthTaxByTypeModel,
} from "@/lib/illustrate/growth-tax-by-type";
import { GrowthTaxTypeLegend } from "@/components/illustrate/GrowthAndTaxChart";

export function GrowthAndTaxTable({
  model,
  loading = false,
  className = "",
}: {
  model: GrowthTaxByTypeModel;
  loading?: boolean;
  className?: string;
}) {
  if (loading) {
    return (
      <div
        className={`min-h-[140px] animate-pulse rounded-md bg-paper ${className}`}
        aria-busy
        aria-label="Loading tax by estimate type"
      />
    );
  }

  if (model.tickers.length === 0) {
    return null;
  }

  return (
    <div className={`w-full ${className}`}>
      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse text-sm">
          <thead>
            <tr>
              <th className="py-1.5 pr-3 text-left text-[10px] font-semibold uppercase tracking-[0.12em] text-faint">
                {"\u00a0"}
              </th>
              {model.years.map((year, yearIndex) =>
                model.tickers.map((ticker, tickerIndex) => (
                  <th
                    key={`${year}-${ticker}`}
                    className={`px-1.5 py-1.5 text-center font-mono text-[11px] font-medium text-ink ${
                      yearIndex > 0 && tickerIndex === 0 ? "border-l border-line" : ""
                    }`}
                  >
                    {ticker}
                  </th>
                )),
              )}
            </tr>
          </thead>
          <tbody>
            {GROWTH_TAX_ESTIMATE_TYPES.map((type) => (
              <tr key={type} className="border-t border-line">
                <th
                  scope="row"
                  className="py-1.5 pr-3 text-left text-[12px] font-medium text-muted"
                >
                  <span className="inline-flex items-center gap-1.5">
                    <span
                      aria-hidden
                      className="inline-block size-1.5 rounded-full"
                      style={{ background: GROWTH_TAX_TYPE_COLORS[type] }}
                    />
                    {GROWTH_TAX_TYPE_LABELS[type]}
                  </span>
                </th>
                {model.years.map((year, yearIndex) =>
                  model.series.map((row, tickerIndex) => {
                    const cell = row.years[yearIndex];
                    const value = cell?.amounts[type] ?? null;
                    const status = cell?.status ?? "empty";
                    return (
                      <td
                        key={`${type}-${year}-${row.ticker}`}
                        className={`px-1.5 py-1.5 text-center font-mono text-[12px] tabular-nums ${
                          value == null ? "text-faint" : "text-ink"
                        } ${yearIndex > 0 && tickerIndex === 0 ? "border-l border-line" : ""}`}
                      >
                        <span className="inline-flex items-center justify-center gap-0.5">
                          {formatGrowthTaxCell(value, status)}
                          {status === "announced" && value != null ? (
                            <HatchGlyph />
                          ) : null}
                        </span>
                      </td>
                    );
                  }),
                )}
              </tr>
            ))}
            <tr className="border-t border-line-strong">
              <th
                scope="row"
                className="py-2 pr-3 text-left text-[12px] font-semibold text-ink"
              >
                Total
              </th>
              {model.years.map((year, yearIndex) =>
                model.series.map((row, tickerIndex) => {
                  const cell = row.years[yearIndex];
                  const status = cell?.status ?? "empty";
                  return (
                    <td
                      key={`total-${year}-${row.ticker}`}
                      className={`px-1.5 py-2 text-center font-mono text-[12px] font-medium tabular-nums ${
                        cell?.total == null ? "text-faint" : "text-ink"
                      } ${yearIndex > 0 && tickerIndex === 0 ? "border-l border-line" : ""}`}
                    >
                      <span className="inline-flex items-center justify-center gap-0.5">
                        {formatGrowthTaxCell(cell?.total ?? null, status, "total")}
                        {status === "announced" && cell?.total != null ? (
                          <HatchGlyph />
                        ) : null}
                      </span>
                    </td>
                  );
                }),
              )}
            </tr>
          </tbody>
        </table>
      </div>
      <GrowthTaxTypeLegend className="mt-4" />
    </div>
  );
}

function HatchGlyph() {
  return (
    <span
      aria-label="Announced unpaid"
      title="Announced (unpaid)"
      className="inline-block size-2 shrink-0 rounded-[1px]"
      style={{
        background: "#9bb8b4",
        backgroundImage:
          "repeating-linear-gradient(135deg, rgba(255,255,255,0.7) 0 1px, transparent 1px 2.5px)",
      }}
    />
  );
}
