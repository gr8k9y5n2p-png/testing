import {
  BILLING_NOT_CONFIGURED,
  BILLING_SIGN_IN,
  CHECKOUT_API_PATH,
  PORTAL_API_PATH,
} from "./billing-copy.ts";

export type BillingActionResult = {
  url?: string;
  detail: string;
  needsAccount?: boolean;
  configured: boolean;
};

async function postBilling(path: string): Promise<BillingActionResult> {
  try {
    const response = await fetch(path, {
      method: "POST",
      credentials: "same-origin",
      headers: { accept: "application/json" },
    });
    const body = (await response.json()) as {
      url?: string;
      detail?: string;
      needs_account?: boolean;
    };
    if (body.url) {
      return { url: body.url, detail: body.detail ?? "", configured: true };
    }
    return {
      detail: body.detail ?? BILLING_NOT_CONFIGURED,
      needsAccount: Boolean(body.needs_account) || response.status === 401,
      configured: response.status !== 501,
    };
  } catch {
    return { detail: BILLING_NOT_CONFIGURED, configured: false };
  }
}

export async function startCheckout(): Promise<BillingActionResult> {
  return postBilling(CHECKOUT_API_PATH);
}

export async function startCustomerPortal(): Promise<BillingActionResult> {
  return postBilling(PORTAL_API_PATH);
}

export function billingActionCopy(
  result: BillingActionResult,
  signedIn: boolean,
): string {
  if (result.needsAccount || !signedIn) return BILLING_SIGN_IN;
  return result.detail || BILLING_NOT_CONFIGURED;
}
