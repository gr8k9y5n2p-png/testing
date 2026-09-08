import { formatOptionalDate, formatUsd } from "@/lib/format";
import {
  PAID_HISTORY_EMPTY,
  TAX_DRAG_CARD_DETAIL,
  TAX_IMPACT_DELTA_DETAIL,
  UPCOMING_UNAVAILABLE_HEADLINE,
  YEAR_TAX_DETAIL,
  YEAR_TAX_EMPTY,
  YEAR_TAX_HEADING,
} from "@/lib/illustrate/portfolio-compare-copy";
import {
  formatMoreLessTax,
  formatStageLabel,
  formatTaxDragPct,
  paidHistoryRowsForSide,
  totalUpcomingTax,
  upcomingHoldingsForSide,
  type TaxPolarity,
} from "@/lib/illustrate/portfolio-compare-map";
import type { PortfolioCompareResponse } from "@/lib/illustrate/portfolio-compare-types";
import { TAX_DRAG_NA_LABEL } from "@/lib/illustrate/tax-drag-chart";
import {
  calendarYearTaxTable,
  hasCalendarYearTax,
  type YearTaxTableModel,
} from "@/lib/illustrate/portfolio-year-tax";

export type PortfolioCompareExportHolding = {
  ticker: string;
  fundName: string;
  weightPct: number | null;
  holdingDollars: number;
};

export type PortfolioCompareExportUpcoming = {
  ticker: string;
  distributionDollars: number | null;
  estimatedTax: number | null;
  available: boolean;
  stageLabel: string;
  announcedDate: string | null;
  recordDate: string | null;
  exDate: string | null;
  payableDate: string | null;
};

export type PortfolioCompareExportSide = {
  label: string;
  taxDrag: number;
  taxDragLabel: string;
  totalUpcomingTax: number;
  holdings: PortfolioCompareExportHolding[];
  upcoming: PortfolioCompareExportUpcoming[];
  paidHistory: PortfolioCompareExportUpcoming[];
};

export type PortfolioCompareExportModel = {
  title: string;
  bookDollars: number;
  generatedAt: string;
  source: "mock" | "live" | "unknown";
  current: PortfolioCompareExportSide;
  proposed: PortfolioCompareExportSide;
  yearTax: YearTaxTableModel;
  delta: {
    estimatedTax: number;
    headline: string;
    polarity: TaxPolarity;
  };
};

function sideModel(
  result: PortfolioCompareResponse,
  side: "current" | "proposed",
): PortfolioCompareExportSide {
  const allocation = result[side];
  return {
    label: allocation.label,
    taxDrag: allocation.totals.effective_tax_on_holding,
    taxDragLabel: formatTaxDragPct(allocation.totals.effective_tax_on_holding),
    totalUpcomingTax: totalUpcomingTax(allocation),
    holdings: allocation.holdings.map((holding) => ({
      ticker: (holding.ticker || holding.fund_identifier || "—").toUpperCase(),
      fundName: holding.fund_name || "",
      weightPct: holding.weight_pct ?? null,
      holdingDollars: holding.holding_dollars,
    })),
    upcoming: upcomingHoldingsForSide(allocation, side).map((row) => ({
      ticker: row.ticker,
      distributionDollars: row.distributionDollars,
      estimatedTax: row.estimatedTax,
      available: row.available,
      stageLabel: formatStageLabel(row.stage),
      announcedDate: row.announcedDate,
      recordDate: row.recordDate,
      exDate: row.exDate,
      payableDate: row.payableDate,
    })),
    paidHistory: paidHistoryRowsForSide(allocation, side).map((row) => ({
      ticker: row.ticker,
      distributionDollars: row.distributionDollars,
      estimatedTax: row.estimatedTax,
      available: row.available,
      stageLabel: formatStageLabel(row.stage),
      announcedDate: row.announcedDate,
      recordDate: row.recordDate,
      exDate: row.exDate,
      payableDate: row.payableDate,
    })),
  };
}

export function toPortfolioCompareExportModel(
  result: PortfolioCompareResponse,
  bookDollars: number,
): PortfolioCompareExportModel {
  const impact = formatMoreLessTax(result.deltas.estimated_tax);
  return {
    title: "Portfolio comparison",
    bookDollars,
    generatedAt: new Date().toISOString(),
    source: result.source ?? "unknown",
    current: sideModel(result, "current"),
    proposed: sideModel(result, "proposed"),
    yearTax: calendarYearTaxTable(result),
    delta: {
      estimatedTax: result.deltas.estimated_tax,
      headline: impact.headline,
      polarity: impact.polarity,
    },
  };
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function money(value: number | null): string {
  return value == null ? TAX_DRAG_NA_LABEL : formatUsd(value, 0);
}

function distMoney(row: PortfolioCompareExportUpcoming): string {
  if (!row.available || row.distributionDollars == null) {
    return UPCOMING_UNAVAILABLE_HEADLINE;
  }
  return formatUsd(row.distributionDollars, 0);
}

function weight(value: number | null): string {
  if (value == null || !Number.isFinite(value)) return "—";
  const rounded = Math.round(value * 100) / 100;
  return `${Number.isInteger(rounded) ? String(rounded) : rounded.toFixed(2)}%`;
}

function sideHtml(side: PortfolioCompareExportSide): string {
  const holdings = side.holdings
    .map(
      (holding) => `
        <tr>
          <td class="mono">${escapeHtml(holding.ticker)}</td>
          <td>${escapeHtml(holding.fundName)}</td>
          <td class="num">${escapeHtml(weight(holding.weightPct))}</td>
          <td class="num">${escapeHtml(money(holding.holdingDollars))}</td>
        </tr>`,
    )
    .join("");
  const upcoming = distributionRowsHtml(side.upcoming);
  const paid = distributionRowsHtml(side.paidHistory);

  return `
    <section class="col">
      <h2>${escapeHtml(side.label)}</h2>
      <p class="metric">Tax drag <strong>${escapeHtml(side.taxDragLabel)}</strong> <span class="muted">${escapeHtml(TAX_DRAG_CARD_DETAIL)}</span></p>
      <p class="metric">Total tax impact <strong>${escapeHtml(
        side.upcoming.some((row) => row.available)
          ? money(side.totalUpcomingTax)
          : UPCOMING_UNAVAILABLE_HEADLINE,
      )}</strong></p>
      <h3>Holdings</h3>
      <table>
        <thead><tr><th>Ticker</th><th>Fund</th><th>Weight</th><th>Dollars</th></tr></thead>
        <tbody>${holdings}</tbody>
      </table>
      <h3>Upcoming / announced</h3>
      <table>
        <thead><tr><th>Ticker</th><th>Est. dist $</th><th>Est. tax</th><th>Announced</th><th>Record</th><th>Ex-div</th><th>Payable</th><th>Stage</th></tr></thead>
        <tbody>${upcoming || `<tr><td colspan="8" class="muted">${UPCOMING_UNAVAILABLE_HEADLINE}</td></tr>`}</tbody>
      </table>
      <h3>Paid history</h3>
      <table>
        <thead><tr><th>Ticker</th><th>Est. dist $</th><th>Est. tax</th><th>Announced</th><th>Record</th><th>Ex-div</th><th>Payable</th><th>Stage</th></tr></thead>
        <tbody>${paid || `<tr><td colspan="8" class="muted">${PAID_HISTORY_EMPTY}</td></tr>`}</tbody>
      </table>
    </section>`;
}

function yearTaxHtml(model: YearTaxTableModel): string {
  if (!hasCalendarYearTax(model)) {
    return `<p class="muted">${escapeHtml(YEAR_TAX_EMPTY)}</p>`;
  }
  const header = model.years
    .map((year) => `<th class="num">${year}</th>`)
    .join("");
  const group = (label: string, rows: YearTaxTableModel["current"]) => {
    if (!rows.length) return "";
    const body = rows
      .map((row) => {
        const cells = row.cells
          .map(
            (cell) =>
              `<td class="num ${cell == null ? "muted" : ""}">${escapeHtml(
                cell == null ? TAX_DRAG_NA_LABEL : money(cell),
              )}</td>`,
          )
          .join("");
        return `<tr><td class="mono">${escapeHtml(row.ticker)}</td>${cells}</tr>`;
      })
      .join("");
    return `<tr><th colspan="${model.years.length + 1}">${escapeHtml(label)}</th></tr>${body}`;
  };
  return `
    <table>
      <thead><tr><th>Ticker</th>${header}</tr></thead>
      <tbody>
        ${group("Current", model.current)}
        ${group("Proposed", model.proposed)}
      </tbody>
    </table>`;
}

function dateCell(value: string | null): string {
  return escapeHtml(formatOptionalDate(value));
}

function distributionRowsHtml(rows: PortfolioCompareExportUpcoming[]): string {
  return rows
    .map(
      (row) => `
        <tr>
          <td class="mono">${escapeHtml(row.ticker)}</td>
          <td class="num">${escapeHtml(distMoney(row))}</td>
          <td class="num">${escapeHtml(
            !row.available || row.estimatedTax == null
              ? TAX_DRAG_NA_LABEL
              : money(row.estimatedTax),
          )}</td>
          <td class="muted">${dateCell(row.announcedDate)}</td>
          <td class="muted">${dateCell(row.recordDate)}</td>
          <td class="muted">${dateCell(row.exDate)}</td>
          <td class="muted">${dateCell(row.payableDate)}</td>
          <td class="muted">${escapeHtml(row.stageLabel)}</td>
        </tr>`,
    )
    .join("");
}

export function renderPortfolioComparePrintHtml(
  model: PortfolioCompareExportModel,
): string {
  const polarity =
    model.delta.polarity === "less"
      ? "#0f7a4b"
      : model.delta.polarity === "more"
        ? "#b42318"
        : "#5c6b5e";
  const generated = new Date(model.generatedAt).toLocaleString("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  });

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>${escapeHtml(model.title)} — Aftertax</title>
  <style>
    @page { size: letter landscape; margin: 0.6in; }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: #1a1d1a;
      background: #fff;
      font: 12px/1.45 "Source Sans 3", "Source Sans Pro", ui-sans-serif, system-ui, sans-serif;
    }
    h1 { font: 600 22px/1.2 "Source Serif 4", Georgia, serif; margin: 0 0 4px; }
    h2 { font: 600 11px/1.2 ui-sans-serif, system-ui, sans-serif; letter-spacing: 0.14em; text-transform: uppercase; color: #8b958c; margin: 0 0 8px; }
    h3 { font: 600 12px/1.2 ui-sans-serif, system-ui, sans-serif; margin: 14px 0 6px; }
    .meta { color: #5c6b5e; font-size: 11px; margin: 0 0 16px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
    .years { margin-top: 18px; }
    .col { break-inside: avoid; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 4px 6px; border-bottom: 1px solid #e6e9e4; text-align: left; vertical-align: top; }
    th { font-size: 10px; letter-spacing: 0.12em; text-transform: uppercase; color: #8b958c; }
    .num, .mono { font-family: "IBM Plex Mono", ui-monospace, monospace; font-size: 11px; }
    .num { text-align: right; }
    .muted { color: #5c6b5e; }
    .metric { margin: 0 0 2px; color: #5c6b5e; }
    .summary { margin-top: 18px; display: grid; grid-template-columns: 1fr 1fr 1fr; border: 1px solid #e6e9e4; border-radius: 12px; overflow: hidden; }
    .summary div { padding: 10px 12px; }
    .summary strong { display: block; font: 600 20px/1.2 "Source Serif 4", Georgia, serif; margin-top: 2px; }
    .delta { background: ${model.delta.polarity === "less" ? "#e4f1ea" : model.delta.polarity === "more" ? "#f6e4e0" : "#f7f8f6"}; }
    .delta strong { color: ${polarity}; }
    .foot { margin-top: 14px; font-size: 10px; color: #8b958c; }
  </style>
</head>
<body>
  <h1>${escapeHtml(model.title)}</h1>
  <p class="meta">Portfolio value ${escapeHtml(money(model.bookDollars))} · ${escapeHtml(generated)}${model.source === "mock" ? " · demo data" : ""}</p>
  <div class="grid">
    ${sideHtml(model.current)}
    ${sideHtml(model.proposed)}
  </div>
  <section class="years">
    <h2>${escapeHtml(YEAR_TAX_HEADING)}</h2>
    <p class="muted">${escapeHtml(YEAR_TAX_DETAIL)}</p>
    ${yearTaxHtml(model.yearTax)}
  </section>
  <section class="summary" aria-label="Portfolio tax summary">
    <div>
      <span>Current tax drag</span>
      <strong>${escapeHtml(model.current.taxDragLabel)}</strong>
      <span class="muted">${escapeHtml(TAX_DRAG_CARD_DETAIL)}</span>
    </div>
    <div>
      <span>Proposed tax drag</span>
      <strong>${escapeHtml(model.proposed.taxDragLabel)}</strong>
      <span class="muted">${escapeHtml(TAX_DRAG_CARD_DETAIL)}</span>
    </div>
    <div class="delta">
      <span>Tax impact Δ</span>
      <strong>${escapeHtml(model.delta.headline)}</strong>
      <span class="muted">${escapeHtml(TAX_IMPACT_DELTA_DETAIL)}</span>
    </div>
  </section>
  <p class="foot">Aftertax · estimates / illustrative only · not tax advice · weights × portfolio value → dollars</p>
</body>
</html>`;
}

export type ExportToPdfOptions = {
  /** Sets `document.title` so Save as PDF can pick up a filename hint. */
  title?: string;
};

/**
 * Print/PDF-ready helper for Website Engineering.
 * Opens the system print dialog (Save as PDF). Website wires the button + freemium gate.
 */
export function exportToPdf(
  model: PortfolioCompareExportModel,
  options: ExportToPdfOptions = {},
): void {
  if (typeof window === "undefined") {
    throw new Error("exportToPdf runs in the browser");
  }

  const html = renderPortfolioComparePrintHtml(model);
  const title = options.title ?? `${model.title} — Aftertax`;
  const frame = document.createElement("iframe");
  frame.setAttribute("title", title);
  frame.setAttribute("aria-hidden", "true");
  Object.assign(frame.style, {
    position: "fixed",
    right: "0",
    bottom: "0",
    width: "0",
    height: "0",
    border: "0",
  });
  document.body.appendChild(frame);

  const doc = frame.contentDocument;
  const win = frame.contentWindow;
  if (!doc || !win) {
    frame.remove();
    throw new Error("exportToPdf could not open a print document");
  }

  doc.open();
  doc.write(html);
  doc.close();
  doc.title = title;

  const cleanup = () => {
    window.setTimeout(() => frame.remove(), 500);
  };
  win.addEventListener("afterprint", cleanup, { once: true });
  window.setTimeout(() => {
    win.focus();
    win.print();
  }, 50);
}
