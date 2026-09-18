import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { describe, it } from "node:test";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { LISTS_PAYWALL_LEAD, LISTS_UNLOCK_KICKER } from "../copy.ts";
import { entitlementFrom, isListsEntitled } from "./entitlement.ts";
import { listsApiDenial, listsApiStatus } from "./lists-access.ts";

const here = dirname(fileURLToPath(import.meta.url));

describe("Lists entitlement gate", () => {
  it("treats Lists as locked unless subscribed or freemium-bypass", () => {
    const locked = entitlementFrom(null, {
      searches: 0,
      compareKeys: [],
      portfolioKeys: [],
    });
    assert.equal(locked.walls.lists, true);
    assert.equal(isListsEntitled(locked), false);
    assert.equal(listsApiStatus(locked), 403);
    assert.deepEqual(listsApiDenial(["FBGRX", "AGTHX"]), {
      items: [],
      tickers: ["FBGRX", "AGTHX"],
      count: 0,
      entitled: false,
      detail: LISTS_PAYWALL_LEAD,
    });

    const bypassed = entitlementFrom(
      null,
      { searches: 1, compareKeys: [], portfolioKeys: [] },
      { NEXT_PUBLIC_FREEMIUM_DISABLED: "1" },
    );
    assert.equal(bypassed.walls.lists, false);
    assert.equal(isListsEntitled(bypassed), true);
    assert.equal(listsApiStatus(bypassed), 200);
  });

  it("wires GET /api/lists and the Lists page to the same entitlement wall", () => {
    const route = readFileSync(join(here, "../../app/api/lists/route.ts"), "utf8");
    const page = readFileSync(join(here, "../../app/lists/page.tsx"), "utf8");
    const body = readFileSync(
      join(here, "../../components/lists/ListsPageBody.tsx"),
      "utf8",
    );
    const workspace = readFileSync(
      join(here, "../../components/lists/ListsWorkspace.tsx"),
      "utf8",
    );
    assert.match(route, /listsApiStatus/);
    assert.match(route, /listsApiDenial/);
    assert.match(route, /status: 403/);
    assert.match(page, /ListsPageBody/);
    assert.match(body, /SoftWall active=\{billing\.walls\.lists\}/);
    assert.match(body, /surface="lists"/);
    assert.match(workspace, /if \(locked\) return/);
  });

  it("keeps the Unlock Access preview as a swappable public asset without invented dist numbers", () => {
    const preview = readFileSync(
      join(here, "../../components/lists/ListsUnlockPreview.tsx"),
      "utf8",
    );
    const svgPath = join(here, "../../../public/lists-unlock-preview.svg");
    assert.equal(existsSync(svgPath), true);
    const svg = readFileSync(svgPath, "utf8");
    assert.match(preview, /LISTS_UNLOCK_PREVIEW_SRC = "\/lists-unlock-preview.svg"/);
    assert.match(preview, /src = LISTS_UNLOCK_PREVIEW_SRC/);
    assert.match(svg, />Lists</);
    assert.match(svg, />Save</);
    assert.match(svg, />Open</);
    assert.match(svg, /AAAXX/);
    assert.match(svg, /BBBXX/);
    assert.doesNotMatch(svg, /\$\d/);
    assert.doesNotMatch(svg, /\d{4}-\d{2}-\d{2}/);
    assert.equal(LISTS_UNLOCK_KICKER, "Unlock Access");
  });
});
