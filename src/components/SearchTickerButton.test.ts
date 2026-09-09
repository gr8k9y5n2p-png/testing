import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

function read(relative: string): string {
  return readFileSync(join(here, relative), "utf8");
}

describe("Search-page ticker clicks select into Search a fund", () => {
  it("SearchTickerButton is a button that calls onSelect, not a Compare link", () => {
    const button = read("SearchTickerButton.tsx");
    assert.match(button, /type="button"/);
    assert.match(button, /onSelect\?\.\(fund\)/);
    assert.match(button, /aria-label=\{`Search \$\{label\}`\}/);
    assert.match(button, /event\.stopPropagation/);
    assert.doesNotMatch(button, /CompareTickerLink|compareTickersPath|\/compare\?tickers=/);
    assert.doesNotMatch(button, /from ["']next\/link["']/);
  });

  it("Highlights and Sample Estimates wire ticker/name clicks through selectFund", () => {
    const card = read("HighlightCard.tsx");
    const section = read("HighlightsSection.tsx");
    const table = read("ResultsTable.tsx");
    const app = read("AftertaxApp.tsx");
    const dashboard = read("Dashboard.tsx");

    assert.match(card, /SearchTickerButton/);
    assert.match(card, /onSelect=\{onSelect\}/);
    assert.doesNotMatch(card, /CompareTickerLink|compareTickersPath|\/compare\?tickers=/);

    assert.match(section, /onSelect=\{onSelect\}/);
    assert.match(section, /<HighlightCard/);

    assert.match(table, /SearchTickerButton/);
    assert.match(table, /onSelect=\{onIllustrate\}/);
    assert.doesNotMatch(table, /CompareTickerLink|compareTickersPath|\/compare\?tickers=/);

    assert.match(app, /<HighlightsSection[^>]*onSelect=\{selectFund\}/);
    assert.match(app, /onIllustrate=\{selectFund\}/);
    assert.match(app, /function selectFund/);
    assert.match(app, /function clearFund/);
    assert.doesNotMatch(
      app.slice(app.indexOf("<HighlightsSection"), app.indexOf("<Disclaimer")),
      /compareTickersPath|\/compare\?tickers=/,
    );

    assert.match(dashboard, /onIllustrate=\{onIllustrate\}/);
  });
});
