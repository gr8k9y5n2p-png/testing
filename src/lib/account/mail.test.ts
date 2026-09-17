import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  DEFAULT_MAIL_FROM,
  mailFrom,
  passwordResetEmailHtml,
  passwordResetEmailText,
  passwordResetUrl,
  passwordResetUserDetail,
  resetEmailConfigured,
  resetLinkOrigin,
  sendPasswordResetEmail,
} from "./mail.ts";

describe("password-reset Resend mail", () => {
  it("defaults from noreply@getaftertax.com and requires only RESEND_API_KEY", () => {
    assert.equal(mailFrom({}), DEFAULT_MAIL_FROM);
    assert.match(DEFAULT_MAIL_FROM, /noreply@getaftertax\.com/);
    assert.equal(resetEmailConfigured({}), false);
    assert.equal(resetEmailConfigured({ RESEND_API_KEY: "re_test" }), true);
    assert.equal(
      mailFrom({ AFTERTAX_MAIL_FROM: "Aftertax <hello@getaftertax.com>" }),
      "Aftertax <hello@getaftertax.com>",
    );
  });

  it("builds production reset links on getaftertax.com", () => {
    assert.equal(
      resetLinkOrigin({ AFTERTAX_PUBLIC_URL: "https://getaftertax.com/" }),
      "https://getaftertax.com",
    );
    assert.equal(resetLinkOrigin({ VERCEL_ENV: "production" }), "https://getaftertax.com");
    assert.equal(
      passwordResetUrl("https://getaftertax.com", "ab".repeat(32)),
      `https://getaftertax.com/account/reset?token=${"ab".repeat(32)}`,
    );
  });

  it("does not claim email was sent when Resend is unset", () => {
    assert.match(passwordResetUserDetail(false), /If email sending were configured/);
    assert.match(passwordResetUserDetail(false), /no email was sent/);
    assert.doesNotMatch(passwordResetUserDetail(false), /we sent a reset link/);
    assert.match(passwordResetUserDetail(true), /noreply@getaftertax\.com/);
  });

  it("renders a transactional template with the one-time link", () => {
    const url = "https://getaftertax.com/account/reset?token=abc";
    const text = passwordResetEmailText(url);
    const html = passwordResetEmailHtml(url);
    assert.match(text, /one-time link/);
    assert.match(text, /expires in one hour/);
    assert.match(text, /getaftertax\.com\/account\/reset\?token=abc/);
    assert.match(html, /Choose a new password/);
    assert.match(html, /href="https:\/\/getaftertax\.com\/account\/reset\?token=abc"/);
    assert.doesNotMatch(html, /gmail/i);
  });

  it("POSTs to Resend when configured and skips the provider when not", async () => {
    const calls: string[] = [];
    const fetchImpl: typeof fetch = async (input, init) => {
      calls.push(`${init?.method} ${String(input)}`);
      return new Response("{}", { status: 200 });
    };
    const skipped = await sendPasswordResetEmail(
      { to: "ada@example.com", resetUrl: "https://getaftertax.com/account/reset?token=aa" },
      {},
      fetchImpl,
    );
    assert.deepEqual(skipped, { configured: false, sent: false });
    assert.deepEqual(calls, []);

    const sent = await sendPasswordResetEmail(
      { to: "ada@example.com", resetUrl: "https://getaftertax.com/account/reset?token=aa" },
      { RESEND_API_KEY: "re_test" },
      fetchImpl,
    );
    assert.deepEqual(sent, { configured: true, sent: true });
    assert.deepEqual(calls, ["POST https://api.resend.com/emails"]);
  });
});
