import { CONTACT_EMAIL } from "../legal-copy.ts";
import { PRODUCTION_ORIGIN, publicOrigin } from "../hosts.ts";

export const PASSWORD_RESET_TTL_MS = 60 * 60 * 1000;
export const DEFAULT_MAIL_FROM = "Aftertax <noreply@getaftertax.com>";
export const RESEND_EMAILS_URL = "https://api.resend.com/emails";

export function mailFrom(env: NodeJS.ProcessEnv = process.env): string {
  const raw = env.AFTERTAX_MAIL_FROM?.trim() || env.RESEND_FROM?.trim() || "";
  return raw.length > 0 ? raw : DEFAULT_MAIL_FROM;
}

export function resetEmailConfigured(
  env: NodeJS.ProcessEnv = process.env,
): boolean {
  return Boolean(env.RESEND_API_KEY?.trim());
}

export function isProductionMailEnv(
  env: NodeJS.ProcessEnv = process.env,
): boolean {
  return env.VERCEL_ENV === "production" || env.NODE_ENV === "production";
}

/** Reset links go to the public site host, not an internal request URL. */
export function resetLinkOrigin(
  env: NodeJS.ProcessEnv = process.env,
  fallback?: string,
): string {
  const pinned = env.AFTERTAX_PUBLIC_URL?.replace(/\/$/, "");
  if (pinned) return pinned;
  if (env.VERCEL_ENV === "production") return PRODUCTION_ORIGIN;
  return fallback?.replace(/\/$/, "") || publicOrigin();
}

export type PasswordResetMail = {
  to: string;
  resetUrl: string;
};

export type PasswordResetMailResult = {
  configured: boolean;
  sent: boolean;
};

export function passwordResetEmailSubject(): string {
  return "Reset your Aftertax password";
}

export function passwordResetEmailText(resetUrl: string): string {
  return [
    "Reset your Aftertax password with this one-time link:",
    "",
    resetUrl,
    "",
    "This link expires in one hour and can be used once. If you did not request a reset, ignore this email.",
    `Need help? ${CONTACT_EMAIL}`,
  ].join("\n");
}

export function passwordResetEmailHtml(resetUrl: string): string {
  const safeUrl = escapeHtml(resetUrl);
  return `<!DOCTYPE html>
<html>
<body style="margin:0;padding:24px;background:#f7f8f6;font-family:Georgia,serif;color:#1a1d1a;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:520px;margin:0 auto;background:#ffffff;border:1px solid #e6e9e4;border-radius:8px;">
    <tr>
      <td style="padding:28px 28px 8px;font-size:11px;letter-spacing:0.16em;text-transform:uppercase;color:#5c6b5e;">Aftertax</td>
    </tr>
    <tr>
      <td style="padding:0 28px 12px;font-size:28px;line-height:1.2;">Reset your password</td>
    </tr>
    <tr>
      <td style="padding:0 28px 20px;font-size:15px;line-height:1.5;color:#5c6b5e;">
        Use this one-time link to choose a new Aftertax password. It expires in one hour.
      </td>
    </tr>
    <tr>
      <td style="padding:0 28px 24px;">
        <a href="${safeUrl}" style="display:inline-block;background:#0f7a4b;color:#ffffff;text-decoration:none;padding:12px 18px;border-radius:6px;font-family:Arial,sans-serif;font-size:14px;">
          Choose a new password
        </a>
      </td>
    </tr>
    <tr>
      <td style="padding:0 28px 28px;font-size:13px;line-height:1.5;color:#8b958c;word-break:break-all;">
        ${safeUrl}<br /><br />
        If you did not request this, you can ignore the email.<br />
        Need help? ${escapeHtml(CONTACT_EMAIL)}
      </td>
    </tr>
  </table>
</body>
</html>`;
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

/**
 * Transactional send via Resend (noreply@getaftertax.com). Not Gmail.
 * When RESEND_API_KEY is missing, the token path still runs; we log in
 * non-prod and do not claim a message was delivered.
 */
export async function sendPasswordResetEmail(
  input: PasswordResetMail,
  env: NodeJS.ProcessEnv = process.env,
  fetchImpl: typeof fetch = fetch,
): Promise<PasswordResetMailResult> {
  const configured = resetEmailConfigured(env);
  if (!configured) {
    logUnconfiguredReset(input, env);
    return { configured: false, sent: false };
  }

  const response = await fetchImpl(RESEND_EMAILS_URL, {
    method: "POST",
    headers: {
      authorization: `Bearer ${env.RESEND_API_KEY?.trim()}`,
      "content-type": "application/json",
    },
    body: JSON.stringify({
      from: mailFrom(env),
      to: [input.to],
      subject: passwordResetEmailSubject(),
      text: passwordResetEmailText(input.resetUrl),
      html: passwordResetEmailHtml(input.resetUrl),
    }),
  });

  if (!response.ok) {
    console.info(
      `[account] Resend rejected password-reset mail (${response.status}). Token remains valid until expiry. From=${mailFrom(env)}.`,
    );
    return { configured: true, sent: false };
  }
  return { configured: true, sent: true };
}

function logUnconfiguredReset(
  input: PasswordResetMail,
  env: NodeJS.ProcessEnv,
): void {
  if (isProductionMailEnv(env)) {
    console.info(
      `[account] Password reset token created. RESEND_API_KEY is not set — no email was sent. Set RESEND_API_KEY (and verify noreply@getaftertax.com on Resend). Do not log reset URLs in production.`,
    );
    return;
  }
  console.info(
    `[account] Password reset token created for ${input.to}. Email send is not configured (RESEND_API_KEY). If email were configured, the link would be ${input.resetUrl}. Contact ${CONTACT_EMAIL}.`,
  );
}

export function passwordResetUserDetail(configured: boolean): string {
  if (configured) {
    return `If an account exists for that email, we sent a reset link from noreply@getaftertax.com. Check your inbox. If a message does not arrive, contact ${CONTACT_EMAIL}.`;
  }
  return `If email sending were configured, you would receive a one-time reset link at that address. Mail is not configured on this environment, so no email was sent. Contact ${CONTACT_EMAIL}.`;
}

export function passwordResetUrl(origin: string, token: string): string {
  const base = origin.replace(/\/$/, "");
  return `${base}/account/reset?token=${encodeURIComponent(token)}`;
}
