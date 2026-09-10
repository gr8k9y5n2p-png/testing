import { GrowthTaxTypeLegend } from "@/components/illustrate/GrowthAndTaxChart";
import { growthTaxChartPad, growthTaxTableLayout } from "@/lib/charts/growth-tax-layout";
import { fundSeriesColor } from "@/lib/charts/series-colors";
import {
  SHARED_CHART_WIDTH,
  type ChartPad,
  type YearLayout,
} from "@/lib/charts/shared-axis";
import {
  GROWTH_TAX_ESTIMATE_TYPES,
  GROWTH_TAX_TYPE_COLORS,
  GROWTH_TAX_TYPE_LABELS,
  formatGrowthTaxCell,
  type GrowthTaxByTypeModel,
} from "@/lib/illustrate/growth-tax-by-type";

export function GrowthAndTaxTable({
  model,
  loading = false,
  className = "",
  axis,
  pad: padProp,
  width = SHARED_CHART_WIDTH,
}: {
  model: GrowthTaxByTypeModel;
  loading?: boolean;
  className?: string;
  axis?: YearLayout;
  pad?: ChartPad;
  width?: number;
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

  const pad = padProp ?? growthTaxChartPad(0);
  const layout = growthTaxTableLayout(
    model.years,
    model.tickers.length,
    width,
    pad,
    axis,
  );

  return (
    <div className={`w-full ${className}`}>
      <div
        data-growth-tax-table
        role="table"
        aria-label="Distribution tax by calendar year"
        className="w-full text-sm"
      >
        <div
          role="row"
          className="grid min-w-0"
          style={{ gridTemplateColumns: layout.template }}
        >
          {layout.columns.map((column, index) => {
            if (column.kind === "stub") {
              return (
                <div
                  key={`h-stub`}
                  role="columnheader"
                  className="min-w-0 py-1.5 pr-2 text-left text-[10px] font-semibold uppercase tracking-[0.12em] text-faint"
                >
                  {"\u00a0"}
                </div>
              );
            }
            if (column.kind === "ticker") {
              const year = model.years[column.yearIndex];
              const ticker = model.tickers[column.seriesIndex];
              const compact = model.tickers.length >= 4;
              return (
                <div
                  key={`h-${year}-${ticker}`}
                  role="columnheader"
                  title={`${year} ${ticker}`}
                  className={`min-w-0 overflow-hidden px-0.5 py-1.5 text-center font-mono text-[11px] font-medium text-ink ${
                    column.yearIndex > 0 && column.seriesIndex === 0
                      ? "border-l border-line"
                      : ""
                  }`}
                >
                  <span className="sr-only">
                    {year} {ticker}
                  </span>
                  {compact ? (
                    <span
                      aria-hidden
                      className="mx-auto block size-1.5 rounded-full"
                      style={{ background: fundSeriesColor(column.seriesIndex) }}
                    />
                  ) : (
                    <span aria-hidden className="block truncate">
                      {ticker}
                    </span>
                  )}
                </div>
              );
            }
            return (
              <div
                key={`h-${column.kind}-${index}`}
                aria-hidden
                className={
                  column.kind === "lead" && column.yearIndex > 0
                    ? "border-l border-line"
                    : ""
                }
              />
            );
          })}
        </div>

        {GROWTH_TAX_ESTIMATE_TYPES.map((type) => (
          <div
            key={type}
            role="row"
            className="grid min-w-0 border-t border-line"
            style={{ gridTemplateColumns: layout.template }}
          >
            {layout.columns.map((column, index) => {
              if (column.kind === "stub") {
                return (
                  <div
                    key={`${type}-stub`}
                    role="rowheader"
                    className="min-w-0 py-1.5 pr-2 text-left text-[12px] font-medium text-muted"
                  >
                    <span className="inline-flex items-center gap-1.5">
                      <span
                        aria-hidden
                        className="inline-block size-1.5 shrink-0 rounded-full"
                        style={{ background: GROWTH_TAX_TYPE_COLORS[type] }}
                      />
                      {GROWTH_TAX_TYPE_LABELS[type]}
                    </span>
                  </div>
                );
              }
              if (column.kind === "ticker") {
                const year = model.years[column.yearIndex];
                const row = model.series[column.seriesIndex];
                const cell = row?.years[column.yearIndex];
                const value = cell?.amounts[type] ?? null;
                const status = cell?.status ?? "empty";
                return (
                  <div
                    key={`${type}-${year}-${row?.ticker ?? column.seriesIndex}`}
                    role="cell"
                    className={`min-w-0 overflow-hidden px-0.5 py-1.5 text-center font-mono text-[10px] tabular-nums sm:text-[12px] ${
                      value == null ? "text-faint" : "text-ink"
                    } ${
                      column.yearIndex > 0 && column.seriesIndex === 0
                        ? "border-l border-line"
                        : ""
                    }`}
                  >
                    <span className="inline-flex items-center justify-center gap-0.5">
                      {formatGrowthTaxCell(value, status, "type", model.unit)}
                      {status === "announced" && value != null ? <HatchGlyph /> : null}
                    </span>
                  </div>
                );
              }
              return (
                <div
                  key={`${type}-${column.kind}-${index}`}
                  aria-hidden
                  className={
                    column.kind === "lead" && column.yearIndex > 0
                      ? "border-l border-line"
                      : ""
                  }
                />
              );
            })}
          </div>
        ))}

        <div
          role="row"
          className="grid min-w-0 border-t border-line-strong"
          style={{ gridTemplateColumns: layout.template }}
        >
          {layout.columns.map((column, index) => {
            if (column.kind === "stub") {
              return (
                <div
                  key="total-stub"
                  role="rowheader"
                  className="min-w-0 py-2 pr-2 text-left text-[12px] font-semibold text-ink"
                >
                  Total
                </div>
              );
            }
            if (column.kind === "ticker") {
              const year = model.years[column.yearIndex];
              const row = model.series[column.seriesIndex];
              const cell = row?.years[column.yearIndex];
              const status = cell?.status ?? "empty";
              return (
                <div
                  key={`total-${year}-${row?.ticker ?? column.seriesIndex}`}
                  role="cell"
                  className={`min-w-0 overflow-hidden px-0.5 py-2 text-center font-mono text-[10px] font-medium tabular-nums sm:text-[12px] ${
                    cell?.total == null ? "text-faint" : "text-ink"
                  } ${
                    column.yearIndex > 0 && column.seriesIndex === 0
                      ? "border-l border-line"
                      : ""
                  }`}
                >
                  <span className="inline-flex items-center justify-center gap-0.5">
                    {formatGrowthTaxCell(cell?.total ?? null, status, "total", model.unit)}
                    {status === "announced" && cell?.total != null ? <HatchGlyph /> : null}
                  </span>
                </div>
              );
            }
            return (
              <div
                key={`total-${column.kind}-${index}`}
                aria-hidden
                className={
                  column.kind === "lead" && column.yearIndex > 0
                    ? "border-l border-line"
                    : ""
                }
              />
            );
          })}
        </div>
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
