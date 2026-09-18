import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

describe("Lists Save / Open chrome", () => {
  it("puts Save and Open at the top of ListsWorkspace", () => {
    const source = readFileSync(join(here, "ListsWorkspace.tsx"), "utf8");
    assert.match(source, /SavedAssetActions/);
    assert.match(source, /type="list"/);
    assert.match(source, /getPayload=\{\(\) => \(\{ tickers \}\)\}/);
    assert.match(source, /parseListPayload/);
    assert.match(source, /lists-heading/);
    const actionsAt = source.indexOf("<SavedAssetActions");
    const detailAt = source.indexOf("{LISTS_DETAIL}");
    assert.ok(actionsAt > 0 && detailAt > actionsAt, "Open/Save sit above the paste helper copy");
    assert.doesNotMatch(source, /NEXT_PUBLIC_FREEMIUM/);
    assert.doesNotMatch(source, /PaywallDialog/);
  });

  it("gates Lists fetches when the entitlement wall is up", () => {
    const source = readFileSync(join(here, "ListsWorkspace.tsx"), "utf8");
    const body = readFileSync(join(here, "ListsPageBody.tsx"), "utf8");
    const page = readFileSync(join(here, "../../app/lists/page.tsx"), "utf8");
    assert.match(body, /billing\.walls\.lists/);
    assert.match(body, /surface="lists"/);
    assert.match(page, /ListsPageBody/);
    assert.match(source, /useBilling/);
    assert.match(source, /const locked = billing\.walls\.lists/);
    assert.match(source, /if \(locked\) return/);
    assert.match(source, /\[locked, tickers\]/);
    assert.doesNotMatch(source, /FRIENDS_BETA_PASSWORD/);
    const wall = readFileSync(join(here, "../paywall/SoftWall.tsx"), "utf8");
    assert.match(wall, /UnlockAccountModal/);
    assert.match(wall, /startOrCheckout/);
    assert.doesNotMatch(wall, /scrollIntoView/);
    assert.doesNotMatch(wall, /accountLoginHref/);
  });
});
