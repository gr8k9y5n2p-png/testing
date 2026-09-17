import { readAccountIdFromRequest, readCookie } from "../account/session.ts";
import { getAccountStore, type AccountRecord } from "../account/store.ts";
import {
  EMPTY_USAGE,
  FREEMIUM_COOKIE,
  FREEMIUM_COOKIE_MAX_AGE_SEC,
  incrementUsage,
  isFreemiumDisabled,
  isSubscriptionEntitled,
  mergeUsage,
  normalizeUsage,
  remainingFromUsage,
  usageWalls,
  type DeviceUsage,
  type Entitlement,
  type UsageKind,
} from "../billing/limits.ts";
import { BILLING_NOT_CONFIGURED } from "./billing-copy.ts";
import { isBillingConfigured, isStripeSecretConfigured } from "./config.ts";

export type { Entitlement };

export function parseDeviceUsageCookie(
  header: string | null | undefined,
): DeviceUsage {
  const raw = readCookie(header, FREEMIUM_COOKIE);
  if (!raw) return { ...EMPTY_USAGE };
  try {
    return normalizeUsage(JSON.parse(raw));
  } catch {
    return { ...EMPTY_USAGE };
  }
}

export function serializeUsageCookie(
  usage: DeviceUsage,
  secure: boolean,
): string {
  const parts = [
    `${FREEMIUM_COOKIE}=${encodeURIComponent(JSON.stringify(usage))}`,
    "Path=/",
    "SameSite=Lax",
    `Max-Age=${FREEMIUM_COOKIE_MAX_AGE_SEC}`,
  ];
  if (secure) parts.push("Secure");
  return parts.join("; ");
}

export function entitlementFrom(
  account: AccountRecord | null,
  device: DeviceUsage,
  env: NodeJS.ProcessEnv = process.env,
): Entitlement {
  const bypass = isFreemiumDisabled(env);
  const subscribed = account ? isSubscriptionEntitled(account) : false;
  const usage = account ? mergeUsage(account.usage, device) : device;
  const remaining = remainingFromUsage(usage);
  const walls = usageWalls(usage);
  const configured = isBillingConfigured(env);
  const unlimited = bypass || subscribed;
  return {
    configured,
    secretConfigured: isStripeSecretConfigured(env),
    subscribed,
    subscriptionStatus: account?.subscriptionStatus ?? null,
    cancelAtPeriodEnd: account?.cancelAtPeriodEnd ?? false,
    currentPeriodEnd: account?.currentPeriodEnd ?? null,
    signedIn: Boolean(account),
    bypass,
    usage,
    remaining,
    walls: {
      search: unlimited ? false : walls.search,
      compare: unlimited ? false : walls.compare,
      portfolio: unlimited ? false : walls.portfolio,
    },
    detail: configured ? null : BILLING_NOT_CONFIGURED,
  };
}

export async function readEntitlement(
  request: Request,
): Promise<{ entitlement: Entitlement; account: AccountRecord | null }> {
  const device = parseDeviceUsageCookie(request.headers.get("cookie"));
  const accountId = readAccountIdFromRequest(request);
  const account = accountId ? await getAccountStore().findById(accountId) : null;
  return { entitlement: entitlementFrom(account, device), account };
}

export async function recordUsage(
  request: Request,
  kind: UsageKind,
  key?: string,
): Promise<{ entitlement: Entitlement; usage: DeviceUsage }> {
  const device = incrementUsage(
    parseDeviceUsageCookie(request.headers.get("cookie")),
    kind,
    key,
  );
  const accountId = readAccountIdFromRequest(request);
  const store = getAccountStore();
  let account = accountId ? await store.findById(accountId) : null;
  if (account) {
    account = await store.mergeDeviceUsage(
      account.id,
      incrementUsage(account.usage, kind, key),
    );
  }
  return {
    entitlement: entitlementFrom(account, device),
    usage: account ? mergeUsage(account.usage, device) : device,
  };
}

export async function mergeSignedInUsage(
  request: Request,
  incoming: DeviceUsage,
): Promise<{ entitlement: Entitlement; usage: DeviceUsage }> {
  const device = mergeUsage(
    parseDeviceUsageCookie(request.headers.get("cookie")),
    normalizeUsage(incoming),
  );
  const accountId = readAccountIdFromRequest(request);
  const store = getAccountStore();
  let account = accountId ? await store.findById(accountId) : null;
  if (account) {
    account = await store.mergeDeviceUsage(account.id, device);
  }
  const usage = account ? mergeUsage(account.usage, device) : device;
  return { entitlement: entitlementFrom(account, usage), usage };
}
