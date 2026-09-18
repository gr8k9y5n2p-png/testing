import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

function read(relative: string): string {
  return readFileSync(join(here, relative), "utf8");
}

describe("homepage Account login panel", () => {
  it("sits to the right of Search a fund and unmounts for a signed-in session", () => {
    const hero = read("landing/Hero.tsx");
    const panel = read("HomepageLoginPanel.tsx");
    const form = read("AccountAuthForm.tsx");
    assert.match(hero, /HomepageLoginPanel/);
    assert.match(hero, /lg:grid-cols-\[minmax\(0,40rem\)_minmax\(18rem,24rem\)\]/);
    assert.match(panel, /account !== null/);
    assert.match(panel, /return null/);
    assert.match(panel, /id="account"/);
    assert.match(panel, /AccountAuthForm/);
    assert.match(form, /ACCOUNT_FORGOT_PASSWORD/);
    assert.match(form, /href="\/account\/forgot"/);
    assert.match(form, /autoComplete="username"/);
    assert.match(form, /name="account-email"/);
    assert.match(form, /name="account-password"/);
    const layout = read("../app/layout.tsx");
    assert.match(layout, /initialAccount/);
    assert.match(layout, /verifyAccountCookie/);
  });

  it("keeps friends-beta password autofill off the Account login fields", () => {
    const beta = read("../app/beta/page.tsx");
    const unlock = read("../app/api/beta/unlock/route.ts");
    const form = read("AccountAuthForm.tsx");
    assert.match(beta, /FRIENDS_BETA_PASSWORD_FIELD/);
    assert.match(beta, /autoComplete="off"/);
    assert.doesNotMatch(beta, /autoComplete="current-password"/);
    assert.match(unlock, /FRIENDS_BETA_PASSWORD_FIELD/);
    assert.doesNotMatch(form, /FRIENDS_BETA_PASSWORD/);
    assert.doesNotMatch(form, /friends-beta-password/);
  });
});
