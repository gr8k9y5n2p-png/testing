import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  CONTACT_EMAIL,
  LEGAL_BETA,
  LEGAL_COMPACT,
  LEGAL_DISCLAIMER,
  LEGAL_LAST_UPDATED,
  LEGAL_OPERATOR,
} from "./legal-copy.ts";
import { PRIVACY, TERMS, legalPlainText } from "./legal.ts";

const FORBIDDEN = [
  "plain-english",
  "plain english",
  "have an attorney",
  "attorney review",
  "with counsel",
  "specify with counsel",
  "governing state to be specified",
  "draft for aftertax",
  "kentucky",
  "lexington",
  "louisville",
  "street address",
  "123 ",
];

function assertNoForbidden(label: string, text: string) {
  const lower = text.toLowerCase();
  for (const phrase of FORBIDDEN) {
    assert.equal(lower.includes(phrase), false, `${label} contains “${phrase}”`);
  }
}

describe("locked legal copy", () => {
  it("keeps the user-facing footer, compact, beta, and contact strings", () => {
    assert.equal(
      LEGAL_DISCLAIMER,
      "Illustrative estimates only. Not tax, legal, or investment advice. Not a recommendation to buy, sell, or hold any fund. Figures may be incomplete or incorrect. Consult a qualified professional before acting.",
    );
    assert.equal(
      LEGAL_COMPACT,
      "Estimates for illustration only — not tax advice.",
    );
    assert.equal(
      LEGAL_BETA,
      "Private beta. Features and data coverage are incomplete. Please report issues to operations@getaftertax.com. Do not treat outputs as client-ready advice.",
    );
    assert.equal(CONTACT_EMAIL, "operations@getaftertax.com");
  });

  it("publishes 15 Terms sections and 13 Privacy sections", () => {
    assert.equal(TERMS.sections.length, 15);
    assert.equal(PRIVACY.sections.length, 13);
    assert.deepEqual(
      TERMS.sections.map((section) => section.number),
      Array.from({ length: 15 }, (_, index) => index + 1),
    );
    assert.deepEqual(
      PRIVACY.sections.map((section) => section.number),
      Array.from({ length: 13 }, (_, index) => index + 1),
    );
  });

  it("names operator, site, date, and contact without a street address", () => {
    for (const document of [TERMS, PRIVACY]) {
      assert.equal(document.lastUpdated, LEGAL_LAST_UPDATED);
      assert.equal(document.operator, LEGAL_OPERATOR);
      assert.equal(document.site, "getaftertax.com");
      const text = legalPlainText(document);
      assert.match(text, /operations@getaftertax\.com/);
      assert.match(text, /September 8, 2026/);
      assert.equal(/\d{1,5}\s+\w+\s+(street|st|avenue|ave|road|rd|blvd)/i.test(text), false);
    }
  });

  it("covers the cleaned Terms and Privacy topics", () => {
    const terms = legalPlainText(TERMS);
    assert.match(terms, /private beta protected by a password/i);
    assert.match(terms, /\$39 per user per month/);
    assert.match(terms, /Stripe/);
    assert.match(terms, /does not invent future distributions/i);
    assert.match(terms, /AS IS/);
    assert.match(terms, /12 months/);
    assert.match(terms, /\$100/);
    assert.match(terms, /state of organization of Aftertax LLC/);
    assert.equal(/counsel/i.test(terms), false);

    const privacy = legalPlainText(PRIVACY);
    assert.match(privacy, /portfolio inputs/);
    assert.match(privacy, /do not sell personal information/i);
    assert.match(privacy, /Vercel/);
    assert.match(privacy, /Render/);
    assert.match(privacy, /Stripe/);
    assert.match(privacy, /Cloudflare/);
    assert.match(privacy, /essential/);
    assert.match(privacy, /United States/);
    assert.equal(/not legal advice/i.test(privacy), false);
  });

  it("contains no draft or counsel meta", () => {
    assertNoForbidden("terms", legalPlainText(TERMS));
    assertNoForbidden("privacy", legalPlainText(PRIVACY));
    assertNoForbidden("disclaimer", LEGAL_DISCLAIMER);
    assertNoForbidden("compact", LEGAL_COMPACT);
    assertNoForbidden("beta", LEGAL_BETA);
  });
});
