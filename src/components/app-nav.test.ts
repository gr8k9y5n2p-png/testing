import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

describe("AppNav primary tabs", () => {
  it("shows exactly Compare, Portfolios, and Lists after the logo home control", () => {
    const nav = readFileSync(join(here, "AppNav.tsx"), "utf8");
    const labels = [...nav.matchAll(/label:\s*"([^"]+)"/g)].map((match) => match[1]);
    const hrefs = [...nav.matchAll(/href:\s*"([^"]+)"/g)].map((match) => match[1]);

    assert.deepEqual(labels, ["Compare", "Portfolios", "Lists"]);
    assert.deepEqual(hrefs, ["/compare", "/portfolio", "/lists"]);
    assert.doesNotMatch(nav, /label:\s*"Search"/);
    assert.doesNotMatch(nav, /href:\s*"\/"/);
    assert.doesNotMatch(nav, /label:\s*"Portfolio"/);
    assert.doesNotMatch(nav, /label:\s*"Account"/);
    assert.doesNotMatch(nav, /label:\s*"Modules"/);
  });
});

describe("AppHeader logo home", () => {
  it("uses the wordmark as the homepage Search control with an active home state", () => {
    const header = readFileSync(join(here, "AppHeader.tsx"), "utf8");
    assert.match(header, /href="\/"/);
    assert.match(header, /aria-label="Aftertax home"/);
    assert.match(header, /pathname === "\/"/);
    assert.match(header, /aria-current=\{home \? "page" : undefined\}/);
    assert.match(header, /bg-accent-soft/);
    assert.match(header, /underline/);
    assert.doesNotMatch(header, /Search/);
  });

  it("keeps ?tab=search on the homepage Search experience", () => {
    const page = readFileSync(join(here, "../app/page.tsx"), "utf8");
    assert.match(page, /firstParam\(params\.tab\) === "search"/);
    assert.match(page, /redirect\(qs \? `\/\?\$\{qs\}` : "\/"\)/);
  });
});
