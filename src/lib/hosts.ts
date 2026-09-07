/**
 * Aftertax hosts. Prefer staging until ads are green-lit.
 * Production apex is the brand host in chrome; staging is the public deploy.
 */
export const PRODUCTION_HOST = "getaftertax.com";
export const STAGING_HOST = "staging.getaftertax.com";

export const PRODUCTION_ORIGIN = `https://${PRODUCTION_HOST}`;
export const STAGING_ORIGIN = `https://${STAGING_HOST}`;

/** Default public origin until ads are green-lit. */
export const DEFAULT_PUBLIC_ORIGIN = STAGING_ORIGIN;

/** Brand chrome (header / footer) — production apex, not www. */
export const HOST = PRODUCTION_HOST;

export function publicOrigin(): string {
  return process.env.AFTERTAX_PUBLIC_URL?.replace(/\/$/, "") || DEFAULT_PUBLIC_ORIGIN;
}

export function isStagingPublicOrigin(origin = publicOrigin()): boolean {
  return origin.includes(STAGING_HOST);
}
