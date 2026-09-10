import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

describe("live Search / Sample Estimates repository", () => {
  it("does not import or merge SAMPLE_FUNDS", () => {
    const source = readFileSync(join(here, "repository.ts"), "utf8");
    assert.doesNotMatch(source, /SAMPLE_FUNDS|from ["']\.\/seed["']|mergeFunds/);
    assert.match(source, /loadFundsFromDataApi/);
    assert.match(source, /loadUpcomingAnnouncedFromDataApi/);
    assert.match(source, /loadTaxYearsFromDataApi/);
    assert.match(source, /apiFunds \?\? \[\]/);
    assert.match(source, /if \(upcoming\.length\)/);
    assert.match(source, /Never merge or fall back to seed\.ts/);
  });

  it("keeps ABALX seed math out of the live repository path", () => {
    const source = readFileSync(join(here, "repository.ts"), "utf8");
    const seed = readFileSync(join(here, "seed.ts"), "utf8");
    assert.match(seed, /ticker:\s*"ABALX"/);
    assert.match(seed, /Test \/ mock fixtures only/);
    assert.doesNotMatch(source, /ABALX/);
  });

  it("does not attach seed NAV on live Search illustrate/compare clients", () => {
    const illustrate = readFileSync(
      join(here, "../lib/illustrate/client.ts"),
      "utf8",
    );
    const compare = readFileSync(
      join(here, "../lib/illustrate/compare-client.ts"),
      "utf8",
    );
    assert.doesNotMatch(illustrate, /seedNavLookup/);
    assert.doesNotMatch(compare, /seedNavLookup/);
  });
});
