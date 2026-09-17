import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

function read(relative: string): string {
  return readFileSync(join(here, relative), "utf8");
}

describe("soft-wall placement", () => {
  it("blurs Search dollar illustration and Upcoming / Paid History without blocking the search box", () => {
    const app = read("../AftertaxApp.tsx");
    const hero = read("../landing/Hero.tsx");
    assert.match(app, /SoftWall active=\{billing\.walls\.search\}/);
    assert.match(app, /<IllustratePanel/);
    assert.match(app, /<Dashboard/);
    assert.doesNotMatch(app, /if \(!result\.allowed\)/);
    assert.doesNotMatch(app, /setPaywallOpen\(true\)/);
    assert.match(hero, /FundPicker/);
    assert.match(hero, /RequestFundForm/);
    assert.doesNotMatch(hero, /SoftWall/);
  });

  it("blurs Compare modules while leaving ticker slots editable", () => {
    const compare = read("../illustrate/CompareWorkspace.tsx");
    assert.match(compare, /SoftWall active=\{billing\.walls\.compare\}/);
    assert.match(compare, /TickerField/);
    const slots = compare.indexOf("TickerField");
    const wall = compare.indexOf("<SoftWall");
    assert.ok(slots > 0 && wall > slots, "ticker slots stay outside the soft wall");
  });

  it("blurs Portfolio modules while leaving allocation ticker slots editable", () => {
    const portfolio = read("../illustrate/PortfolioCompare.tsx");
    assert.match(portfolio, /SoftWallCta surface="portfolio"/);
    assert.match(portfolio, /AllocationColumn/);
    assert.match(portfolio, /pointer-events-none select-none blur-sm/);
  });

  it("does not enable the friends-beta invite gate", () => {
    const friends = read("../../lib/friends-beta.ts");
    assert.match(friends, /FRIENDS_BETA_PASSWORD/);
    assert.doesNotMatch(friends, /NEXT_PUBLIC_FRIENDS_BETA=true/);
  });
});
