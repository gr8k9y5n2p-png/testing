import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  LIST_HYDRATE_MAX_ATTEMPTS,
  listHydrateBackoffMs,
  listRowsAfterFailedHydrate,
  listRowsFromApiResponse,
  needsListHydrate,
} from "./hydrate.ts";
import { emptyListRow } from "./rows.ts";

const here = dirname(fileURLToPath(import.meta.url));

describe("Lists client hydrate", () => {
  it("retries missing, loading, and not_found rows — not a locked miss", () => {
    assert.equal(needsListHydrate(undefined, 0), true);
    assert.equal(needsListHydrate(emptyListRow("FBGRX", "loading"), 0), true);
    assert.equal(needsListHydrate(emptyListRow("FBGRX", "not_found"), 0), true);
    assert.equal(needsListHydrate(emptyListRow("FBGRX", "not_found"), 1), true);
    assert.equal(
      needsListHydrate(emptyListRow("FBGRX", "not_found"), LIST_HYDRATE_MAX_ATTEMPTS),
      false,
    );
    const upcoming = { ...emptyListRow("FBGRX", "upcoming"), found: true };
    assert.equal(needsListHydrate(upcoming, 0), false);
    assert.equal(listHydrateBackoffMs(0), 0);
    assert.ok(listHydrateBackoffMs(1) > 0);
  });

  it("does not map a failed /api/lists response to not_found", () => {
    assert.throws(
      () => listRowsFromApiResponse(["FBGRX"], { items: [] }, false),
      /lists hydrate failed/,
    );
    const rows = listRowsFromApiResponse(
      ["FBGRX"],
      {
        items: [
          {
            ...emptyListRow("FBGRX", "upcoming"),
            found: true,
            nav: 312.26,
            distPerShare: 21.021,
          },
        ],
      },
      true,
    );
    assert.equal(rows[0]?.status, "upcoming");
    assert.ok(rows[0]?.nav != null && Math.abs(rows[0].nav - 312.26) < 1e-6);
    assert.ok(
      rows[0]?.distPerShare != null &&
        Math.abs(rows[0].distPerShare - 21.021) < 1e-6,
    );
    const failed = listRowsAfterFailedHydrate(["FBGRX"]);
    assert.equal(failed[0]?.status, "not_found");
  });

  it("keeps ListsWorkspace on no-store retry instead of first-paint NOT FOUND", () => {
    const workspace = readFileSync(
      join(here, "../../components/lists/ListsWorkspace.tsx"),
      "utf8",
    );
    const route = readFileSync(join(here, "../../app/api/lists/route.ts"), "utf8");
    assert.match(workspace, /cache:\s*"no-store"/);
    assert.match(workspace, /LIST_HYDRATE_MAX_ATTEMPTS/);
    assert.match(workspace, /listRowsFromApiResponse/);
    assert.match(route, /status:\s*503/);
    assert.match(route, /Cache-Control": "no-store"/);
    assert.match(route, /upstream/);
  });
});
