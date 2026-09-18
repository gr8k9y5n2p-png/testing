import { BILLING_NOT_CONFIGURED, BILLING_SIGN_IN } from "./billing-copy.ts";

/** Homepage login panel (`HomepageLoginPanel` id="account"). */
export const HOMEPAGE_LOGIN_HREF = "/#account";
/** Dedicated Account page with the same email/password form. */
export const ACCOUNT_LOGIN_HREF = "/account";

export type UnlockCtaKind = "redirect" | "sign_in" | "error";

export type UnlockCtaResult = {
  url?: string;
  detail: string;
  needsAccount?: boolean;
};

export function unlockCtaStatus(
  result: UnlockCtaResult,
  signedIn: boolean,
): { kind: UnlockCtaKind; detail: string } {
  if (result.url) return { kind: "redirect", detail: "" };
  if (result.needsAccount || !signedIn) {
    return { kind: "sign_in", detail: BILLING_SIGN_IN };
  }
  return {
    kind: "error",
    detail: result.detail || BILLING_NOT_CONFIGURED,
  };
}
