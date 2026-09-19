import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { describe, it } from "node:test";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { entitlementFrom, isListsEntitled } from "./entitlement.ts";
import {
  LISTS_LOCKED_DETAIL,
  listsApiDenial,
  listsApiStatus,
} from "./lists-access.ts";

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
      detail: LISTS_LOCKED_DETAIL,
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
    assert.match(body, /active=\{billing\.walls\.lists\}/);
    assert.match(body, /surface="lists"/);
    assert.match(workspace, /if \(locked\) return/);
    const wall = readFileSync(
      join(here, "../../components/paywall/SoftWall.tsx"),
      "utf8",
    );
    assert.match(wall, /UnlockAccountModal/);
    assert.match(wall, /startOrCheckout/);
    assert.doesNotMatch(wall, /accountLoginHref/);
  });

  it("uses the Modules Lists Unlock underlay as a swappable public asset", () => {
    const preview = readFileSync(
      join(here, "../../components/lists/ListsUnlockPreview.tsx"),
      "utf8",
    );
    const marketing = join(here, "../../../public/marketing");
    assert.equal(existsSync(join(marketing, "lists-unlock-preview.png")), true);
    assert.equal(existsSync(join(marketing, "lists-unlock-preview.webp")), true);
    assert.equal(existsSync(join(marketing, "lists-unlock-preview@2x.png")), true);
    assert.equal(existsSync(join(here, "../../../public/lists-unlock-preview.svg")), false);
    assert.match(
      preview,
      /LISTS_UNLOCK_PREVIEW_SRC = "\/marketing\/lists-unlock-preview.png"/,
    );
    assert.match(preview, /src = LISTS_UNLOCK_PREVIEW_SRC/);
    assert.match(preview, /LISTS_UNLOCK_PREVIEW_ALT/);
    assert.match(preview, /Ticker chips and the ticker column are strongly blurred/);
    assert.match(preview, /NAV · Estimated \$/);
    assert.match(preview, /LTCG · STCG · Ordinary/);
    assert.match(preview, /Announced Date · Record Date · Ex-Date/);
    const copy = readFileSync(join(here, "../copy.ts"), "utf8");
    assert.match(copy, /LISTS_UNLOCK_KICKER = "Unlock Access"/);
    assert.match(copy, /LISTS_PAYWALL_LEAD = "Lists is included with Aftertax access."/);
    assert.match(copy, /Illustrative Lists layout — not live estimates/);
    assert.match(copy, new RegExp(`LISTS_PAYWALL_LEAD = "${LISTS_LOCKED_DETAIL}"`));
  });
});
