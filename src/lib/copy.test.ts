import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

describe("Sample Estimates empty copy", () => {
  it("uses Undisclosed / N/A language and does not pitch seed sample math", () => {
    const source = readFileSync(join(here, "copy.ts"), "utf8");
    assert.match(source, /UPCOMING_UNAVAILABLE_HEADLINE = "Not available \/ undisclosed"/);
    assert.match(source, /No unpaid announced estimates from the Data API/);
    assert.match(source, /No paid history from the Data API/);
    assert.match(source, /SEARCH_UPCOMING_HEADING = "Upcoming \/ Announced"/);
    assert.match(
      source,
      /After ex-date \(America\/Chicago\) they move to Paid History below/,
    );
    assert.match(source, /SEARCH_PAID_HISTORY_HEADING = "Paid History"/);
    assert.match(source, /selected calendar year/);
    assert.match(source, /ILLUSTRATION_PAID_HISTORY_DETAIL/);
    assert.match(source, /prior calendar year only/);
    assert.match(source, /LISTS_HEADING = "Lists"/);
    assert.match(source, /LISTS_DIST_COLUMN = "Estimated \$ Distribution\/share"/);
    assert.match(source, /never invented from paid history/);
    assert.doesNotMatch(source, /in this sample/);
  });
});
