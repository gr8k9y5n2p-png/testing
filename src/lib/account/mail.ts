import { CONTACT_EMAIL } from "../legal-copy.ts";

export const PASSWORD_RESET_TTL_MS = 60 * 60 * 1000;

export function mailFrom(env: NodeJS.ProcessEnv = process.env): string | null {
  const raw = env.AFTERTAX_MAIL_FROM?.trim() || env.RESEND_FROM?.trim() || "";
  return raw.length > 0 ? raw : null;
}

export function resetEmailConfigured(
  env: NodeJS.ProcessEnv = process.env,
): boolean {
  return Boolean(env.RESEND_API_KEY?.trim() && mailFrom(env));
}

export type PasswordResetMail = {
  to: string;
  resetUrl: string;
};

/**
 * Send the reset link when Resend is configured. Staging without mail still
 * creates the server token; the URL is logged so operators can complete the
 * flow. Production must set RESEND_API_KEY + AFTERTAX_MAIL_FROM and must not
 * depend on logs.
 */
export async function sendPasswordResetEmail(
  input: PasswordResetMail,
  env: NodeJS.ProcessEnv = process.env,
  fetchImpl: typeof fetch = fetch,
): Promise<boolean> {
  const key = env.RESEND_API_KEY?.trim();
  const from = mailFrom(env);
  if (!key || !from) {
    console.info(
      `[account] Password reset token created for ${input.to}. Email send is not configured — set RESEND_API_KEY and AFTERTAX_MAIL_FROM for production. Staging reset URL (do not use this path in production): ${input.resetUrl}. If mail does not arrive, contact ${CONTACT_EMAIL}.`,
    );
    return false;
  }

  const response = await fetchImpl("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      authorization: `Bearer ${key}`,
      "content-type": "application/json",
    },
    body: JSON.stringify({
      from,
      to: [input.to],
      subject: "Reset your Aftertax password",
      text: [
        "Reset your Aftertax password with this link:",
        "",
        input.resetUrl,
        "",
        "This link expires in one hour. If you did not request a reset, ignore this email.",
        `Need help? ${CONTACT_EMAIL}`,
      ].join("\n"),
    }),
  });

  if (!response.ok) {
    console.info(
      `[account] Resend rejected password-reset mail for ${input.to} (${response.status}). Token remains valid until expiry.`,
    );
    return false;
  }
  return true;
}

export function passwordResetUrl(origin: string, token: string): string {
  const base = origin.replace(/\/$/, "");
  return `${base}/account/reset?token=${encodeURIComponent(token)}`;
}
