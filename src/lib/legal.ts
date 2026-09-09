import {
  CONTACT_EMAIL,
  LEGAL_LAST_UPDATED,
  LEGAL_OPERATOR,
} from "./legal-copy.ts";

export { CONTACT_EMAIL, LEGAL_LAST_UPDATED, LEGAL_OPERATOR } from "./legal-copy.ts";

const LEGAL_SITE = "getaftertax.com";

export type LegalBlock = {
  title: string;
  paragraphs: string[];
};

export type LegalSection = {
  number: number;
  title: string;
  paragraphs: string[];
  blocks?: LegalBlock[];
};

export type LegalDocument = {
  slug: "terms" | "privacy";
  title: string;
  lastUpdated: string;
  operator: string;
  site: string;
  intro: string[];
  sections: LegalSection[];
};

export const TERMS: LegalDocument = {
  slug: "terms",
  title: "Terms of Use",
  lastUpdated: LEGAL_LAST_UPDATED,
  operator: LEGAL_OPERATOR,
  site: LEGAL_SITE,
  intro: [
    `These Terms of Use govern your access to and use of ${LEGAL_SITE} and the Aftertax product (together, “Aftertax”). Aftertax is operated by ${LEGAL_OPERATOR}.`,
  ],
  sections: [
    {
      number: 1,
      title: "Agreement",
      paragraphs: [
        "By accessing or using Aftertax, you agree to these Terms of Use. If you do not agree, do not use Aftertax.",
      ],
    },
    {
      number: 2,
      title: "What Aftertax is",
      paragraphs: [
        "Aftertax is an online product that provides illustrative estimates of the taxable impact of fund distributions.",
      ],
    },
    {
      number: 3,
      title: "Not tax, legal, or investment advice",
      paragraphs: [
        "Aftertax does not provide tax, legal, or investment advice. Aftertax is not a recommendation to buy, sell, or hold any fund. Figures may be incomplete or incorrect. Consult a qualified professional before acting.",
      ],
    },
    {
      number: 4,
      title: "Accounts and access",
      paragraphs: [
        "Some features of Aftertax require an account. Aftertax may also be offered as a private beta protected by a password. You are responsible for keeping your account credentials and any beta password confidential, and for activity under your access.",
      ],
    },
    {
      number: 5,
      title: "Subscriptions",
      paragraphs: [
        "When subscriptions are enabled, Aftertax is offered at $39 per user per month. Payments are processed by Stripe. Until subscriptions are enabled, paid features may be unavailable.",
      ],
    },
    {
      number: 6,
      title: "Acceptable use",
      paragraphs: [
        "You may use Aftertax only for lawful purposes. You may not misuse Aftertax, interfere with its operation, or use it in a way that infringes the rights of Aftertax LLC or others.",
      ],
    },
    {
      number: 7,
      title: "Data and accuracy",
      paragraphs: [
        "Aftertax figures may be incomplete or incorrect. Aftertax does not invent future distributions. Do not treat missing, undisclosed, or unavailable distribution data as a zero amount or as a forecast.",
      ],
    },
    {
      number: 8,
      title: "Intellectual property",
      paragraphs: [
        "Aftertax LLC and its licensors own Aftertax, including the site, product, text, design, and related intellectual property. These Terms of Use do not transfer ownership of that intellectual property to you.",
      ],
    },
    {
      number: 9,
      title: "Confidentiality of beta",
      paragraphs: [
        "If you receive access to a private beta, you agree to keep non-public beta features, data, passwords, and materials confidential and not to share them except as Aftertax permits.",
      ],
    },
    {
      number: 10,
      title: "Disclaimers",
      paragraphs: [
        "AFTERTAX IS PROVIDED “AS IS.” To the fullest extent permitted by law, Aftertax LLC disclaims all warranties, including implied warranties of merchantability, fitness for a particular purpose, and non-infringement.",
      ],
    },
    {
      number: 11,
      title: "Limitation of liability",
      paragraphs: [
        "To the fullest extent permitted by law, Aftertax LLC’s total liability arising out of or related to Aftertax is limited to the greater of the fees you paid to Aftertax LLC for Aftertax in the 12 months before the claim or $100.",
      ],
    },
    {
      number: 12,
      title: "Indemnity",
      paragraphs: [
        "You agree to indemnify and hold harmless Aftertax LLC from claims arising out of your use of Aftertax or your violation of these Terms of Use.",
      ],
    },
    {
      number: 13,
      title: "Changes",
      paragraphs: [
        "Aftertax LLC may update these Terms of Use. The Last updated date at the top of this page will change when updates are posted. Continued use of Aftertax after an update means you accept the updated Terms of Use.",
      ],
    },
    {
      number: 14,
      title: "Governing law",
      paragraphs: [
        "These Terms of Use are governed by the laws of the United States and the state of organization of Aftertax LLC, without regard to conflict-of-law rules.",
      ],
    },
    {
      number: 15,
      title: "Contact",
      paragraphs: [`Questions about these Terms of Use: ${CONTACT_EMAIL}.`],
    },
  ],
};

export const PRIVACY: LegalDocument = {
  slug: "privacy",
  title: "Privacy Policy",
  lastUpdated: LEGAL_LAST_UPDATED,
  operator: LEGAL_OPERATOR,
  site: LEGAL_SITE,
  intro: [
    `This Privacy Policy describes how ${LEGAL_OPERATOR} collects, uses, and shares information when you use ${LEGAL_SITE} and the Aftertax product.`,
  ],
  sections: [
    {
      number: 1,
      title: "Scope",
      paragraphs: [
        `This Privacy Policy applies to ${LEGAL_SITE} and the Aftertax product operated by ${LEGAL_OPERATOR}.`,
      ],
    },
    {
      number: 2,
      title: "Information we collect",
      paragraphs: [
        "We collect the following categories of information:",
      ],
      blocks: [
        {
          title: "Information you provide",
          paragraphs: [
            "Account details, portfolio inputs, and messages you send to Aftertax.",
          ],
        },
        {
          title: "Stripe",
          paragraphs: [
            "If you subscribe, Stripe processes payment information.",
          ],
        },
        {
          title: "Automatic",
          paragraphs: [
            "Technical logs, including device, browser, and usage information.",
          ],
        },
        {
          title: "Beta",
          paragraphs: [
            "Beta access logs, including access to password-protected beta features.",
          ],
        },
      ],
    },
    {
      number: 3,
      title: "How we use information",
      paragraphs: [
        "We use this information to provide and operate Aftertax. We do not sell personal information.",
      ],
    },
    {
      number: 4,
      title: "Fund data",
      paragraphs: [
        "Aftertax uses fund and distribution data to generate illustrative estimates. Aftertax does not invent future distributions.",
      ],
    },
    {
      number: 5,
      title: "Sharing",
      paragraphs: [
        "We share information with processors that help us operate Aftertax: Vercel, Render, Stripe, and Cloudflare.",
      ],
    },
    {
      number: 6,
      title: "Cookies",
      paragraphs: [
        "Aftertax uses cookies that are essential to operate the site.",
      ],
    },
    {
      number: 7,
      title: "Retention",
      paragraphs: [
        "We retain information as needed to provide Aftertax.",
      ],
    },
    {
      number: 8,
      title: "Security",
      paragraphs: [
        "We use measures designed to protect the information we hold.",
      ],
    },
    {
      number: 9,
      title: "Children",
      paragraphs: ["Aftertax is not directed to children."],
    },
    {
      number: 10,
      title: "Rights",
      paragraphs: [
        `You may contact Aftertax about your information at ${CONTACT_EMAIL}.`,
      ],
    },
    {
      number: 11,
      title: "International",
      paragraphs: ["Aftertax processes information in the United States."],
    },
    {
      number: 12,
      title: "Changes",
      paragraphs: [
        "Aftertax may update this Privacy Policy. The Last updated date at the top of this page will change when updates are posted.",
      ],
    },
    {
      number: 13,
      title: "Contact",
      paragraphs: [CONTACT_EMAIL],
    },
  ],
};

export function legalPlainText(document: LegalDocument): string {
  const parts = [
    document.title,
    document.lastUpdated,
    document.operator,
    document.site,
    ...document.intro,
  ];
  for (const section of document.sections) {
    parts.push(section.title, ...section.paragraphs);
    for (const block of section.blocks ?? []) {
      parts.push(block.title, ...block.paragraphs);
    }
  }
  return parts.join("\n");
}
