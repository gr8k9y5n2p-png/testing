import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

describe("AppNav primary tabs", () => {
  it("shows exactly Search, Compare, Portfolios, and Lists in that order", () => {
    const nav = readFileSync(join(here, "AppNav.tsx"), "utf8");
    const labels = [...nav.matchAll(/label:\s*"([^"]+)"/g)].map((match) => match[1]);
    const hrefs = [...nav.matchAll(/href:\s*"([^"]+)"/g)].map((match) => match[1]);

    assert.deepEqual(labels, ["Search", "Compare", "Portfolios", "Lists"]);
    assert.deepEqual(hrefs, ["/", "/compare", "/portfolio", "/lists"]);
    assert.doesNotMatch(nav, /label:\s*"Portfolio"/);
    assert.doesNotMatch(nav, /label:\s*"Account"/);
    assert.doesNotMatch(nav, /label:\s*"Modules"/);
  });
});
