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
    assert.match(portfolio, /relative z-20 h-full lg:\[grid-area:holdings-c\]/);
    assert.match(portfolio, /relative z-20 h-full lg:\[grid-area:holdings-p\]/);
  });

  it("seeds BillingProvider from the aftertax_freemium cookie on the server", () => {
    const layout = read("../../app/layout.tsx");
    const provider = read("../BillingProvider.tsx");
    assert.match(layout, /initialUsage=\{initialUsage\}/);
    assert.match(layout, /FREEMIUM_COOKIE/);
    assert.match(layout, /usageFromCookieValue/);
    assert.match(provider, /initialUsage/);
    assert.match(provider, /writeBrowserUsage/);
    assert.match(provider, /readBrowserUsage/);
  });

  it("uses Unlock full access — never Upgrade — on soft-wall CTAs", () => {
    const copy = read("../../lib/copy.ts");
    const billing = read("../../lib/stripe/billing-copy.ts");
    const wall = read("SoftWall.tsx");
    assert.match(copy, /paywallCta: "Unlock full access"/);
    assert.match(billing, /UNLOCK_BILLING_LABEL = "Unlock full access"/);
    assert.match(wall, /Unlock full access/);
    assert.doesNotMatch(copy, /Upgrade/);
    assert.doesNotMatch(billing, /Upgrade/);
    assert.doesNotMatch(wall, /Upgrade/);
  });

  it("always re-enables Unlock and opens the Create account modal when signed out", () => {
    const wall = read("SoftWall.tsx");
    const modal = read("../UnlockAccountModal.tsx");
    const menu = read("../ManageBillingButton.tsx");
    const form = read("../AccountAuthForm.tsx");
    assert.match(modal, /try \{/);
    assert.match(modal, /finally \{\s*setBusy\(false\)/);
    assert.match(wall, /unlockCtaPreview/);
    assert.match(wall, /UnlockAccountModal/);
    assert.match(wall, /startOrCheckout/);
    assert.match(wall, /continueAfterAuth/);
    assert.match(wall, /role="status"/);
    assert.doesNotMatch(wall, /scrollIntoView/);
    assert.doesNotMatch(wall, /accountLoginHref/);
    assert.doesNotMatch(wall, /HOMEPAGE_LOGIN_HREF/);
    assert.match(modal, /variant="unlock"/);
    assert.match(modal, /initialAction="signup"/);
    assert.match(modal, /ACCOUNT_SIGN_UP/);
    assert.match(modal, /billing\.unlock/);
    assert.match(modal, /createPortal/);
    assert.match(form, /ACCOUNT_HAVE_ACCOUNT/);
    assert.match(menu, /UnlockAccountModal/);
    assert.match(menu, /startOrCheckout/);
    assert.match(menu, /finally \{\s*setPortalBusy\(false\)/);
  });

  it("paywalls the entire Lists tab with Unlock Access + a swappable preview", () => {
    const page = read("../../app/lists/page.tsx");
    const body = read("../lists/ListsPageBody.tsx");
    const workspace = read("../lists/ListsWorkspace.tsx");
    const wall = read("SoftWall.tsx");
    const preview = read("../lists/ListsUnlockPreview.tsx");
    assert.match(page, /ListsPageBody/);
    assert.match(body, /active=\{billing\.walls\.lists\}/);
    assert.match(body, /surface="lists"/);
    assert.match(workspace, /billing\.walls\.lists/);
    assert.match(workspace, /if \(locked\) return/);
    assert.match(wall, /surface === "lists"/);
    assert.match(wall, /LISTS_UNLOCK_KICKER/);
    assert.match(wall, /ListsUnlockPreview/);
    assert.match(wall, /UnlockAccountModal/);
    assert.match(wall, /startOrCheckout/);
    assert.match(preview, /LISTS_UNLOCK_PREVIEW_SRC/);
    assert.match(preview, /src = LISTS_UNLOCK_PREVIEW_SRC/);
    assert.doesNotMatch(wall, /Upgrade/);
    assert.doesNotMatch(wall, /scrollIntoView/);
    assert.doesNotMatch(wall, /accountLoginHref/);
  });

  it("does not enable the friends-beta invite gate", () => {
    const friends = read("../../lib/friends-beta.ts");
    assert.match(friends, /FRIENDS_BETA_PASSWORD/);
    assert.doesNotMatch(friends, /NEXT_PUBLIC_FRIENDS_BETA=true/);
  });
});
