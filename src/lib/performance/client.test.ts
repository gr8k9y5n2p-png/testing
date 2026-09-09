import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

function read(relative: string): string {
  return readFileSync(join(here, relative), "utf8");
}

describe("performance client live vs fixture wiring", () => {
  it("resolves request mode instead of defaulting to fixture", () => {
    const client = read("client.ts");
    assert.match(client, /resolvePerformanceMode\(request\.mode\)/);
    assert.match(client, /raw\.mode \?\? defaultPerformanceMode\(\)/);
    assert.doesNotMatch(client, /params\.set\("mode", request\.mode\?\.trim\(\) \|\| "fixture"\)/);
    assert.doesNotMatch(client, /mode: request\.mode \?\? "fixture"/);
  });

  it("does not fall back to same-origin mocks when the Data API is remote", () => {
    const client = read("client.ts");
    assert.doesNotMatch(
      client,
      /if \(remote && response\.status >= 500\) \{\s*response = await fetch\(fallback/,
    );
    assert.doesNotMatch(
      client,
      /if \(remote && !init\?\.signal\?\.aborted\) \{\s*response = await fetch\(fallback/,
    );
    assert.match(
      client,
      /if \(remote && response\.status >= 500\) \{\s*throw new IllustrateRequestError/,
    );
    assert.match(client, /if \(!remote\) \{\s*try \{\s*return mockPerformanceResponse/);
  });

  it("keeps uncovered / 404 packs as skippable No Performance", () => {
    const client = read("client.ts");
    assert.match(client, /performancePackIsUsable/);
    assert.match(client, /performanceFromFetchError/);
    const coverage = read("coverage.ts");
    assert.match(coverage, /covered === false/);
    assert.match(coverage, /status === 404/);
  });
});
