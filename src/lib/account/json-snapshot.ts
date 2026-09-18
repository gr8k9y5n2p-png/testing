/**
 * Shared JSON snapshots for the account store.
 *
 * Vercel serverless instances do not share `/tmp`. #277 reloads the file on
 * every read, but Production still missed rows written on another instance.
 * These backends keep the same scrypt hashes and JSON shape, and they are
 * visible to every instance immediately.
 *
 * Private Blob `get(pathname)` can 404 (or hang) even after a successful
 * `put`. Reads list first, pick the newest matching blob, then `get(url)`.
 * A miss is an empty document (`null`). Timeouts throw — they must not be
 * treated as empty, or the next write would wipe hashes.
 */

import {
  abortSignalTimeout,
  isAbortOrTimeoutError,
  withTimeout,
} from "../with-timeout.ts";

export type JsonSnapshot = {
  read(): Promise<string | null>;
  write(payload: string): Promise<void>;
};

export const DEFAULT_ACCOUNTS_BLOB_PATH = "aftertax/accounts.json";
export const DEFAULT_ACCOUNTS_REDIS_KEY = "aftertax:accounts";
export const BLOB_SNAPSHOT_TIMEOUT_MS = 8_000;
export const BLOB_SNAPSHOT_TIMEOUT_MESSAGE =
  "Account storage timed out. Try again.";

export type RedisRestConfig = {
  url: string;
  token: string;
  key: string;
};

export function redisRestConfig(
  env: NodeJS.ProcessEnv = process.env,
): RedisRestConfig | null {
  const url = env.UPSTASH_REDIS_REST_URL?.trim() || env.KV_REST_API_URL?.trim() || "";
  const token =
    env.UPSTASH_REDIS_REST_TOKEN?.trim() || env.KV_REST_API_TOKEN?.trim() || "";
  if (!url || !token) return null;
  return {
    url,
    token,
    key: env.AFTERTAX_ACCOUNTS_REDIS_KEY?.trim() || DEFAULT_ACCOUNTS_REDIS_KEY,
  };
}

export function blobConfigured(env: NodeJS.ProcessEnv = process.env): boolean {
  return Boolean(
    env.BLOB_READ_WRITE_TOKEN?.trim() || env.BLOB_STORE_ID?.trim(),
  );
}

/** In-memory box two store instances can share (instance A write / instance B read). */
export class InMemoryJsonSnapshot implements JsonSnapshot {
  private readonly box: { raw: string | null };

  constructor(box: { raw: string | null }) {
    this.box = box;
  }

  async read(): Promise<string | null> {
    return this.box.raw;
  }

  async write(payload: string): Promise<void> {
    this.box.raw = payload;
  }
}

type BlobGetResult = {
  statusCode?: number;
  stream?: ReadableStream<Uint8Array> | null;
} | null;

export type BlobListRow = {
  pathname: string;
  url: string;
  downloadUrl?: string;
  uploadedAt?: string | Date;
};

type BlobListResult = {
  blobs: BlobListRow[];
};

export type BlobGetOptions = {
  access: "private";
  useCache: false;
  abortSignal?: AbortSignal;
};

export type BlobPutOptions = {
  access: "private";
  addRandomSuffix: false;
  allowOverwrite: true;
  cacheControlMaxAge: number;
  contentType: string;
  abortSignal?: AbortSignal;
};

export type BlobSnapshotDeps = {
  get: (pathname: string, options: BlobGetOptions) => Promise<BlobGetResult>;
  put: (
    pathname: string,
    payload: string,
    options: BlobPutOptions,
  ) => Promise<unknown>;
  list?: (options: {
    prefix: string;
    limit: number;
    abortSignal?: AbortSignal;
  }) => Promise<BlobListResult>;
};

export type BlobSnapshotOptions = {
  timeoutMs?: number;
};

export function accountsBlobPath(
  env: NodeJS.ProcessEnv = process.env,
): string {
  return env.AFTERTAX_ACCOUNTS_BLOB_PATH?.trim() || DEFAULT_ACCOUNTS_BLOB_PATH;
}

/** List prefix that also catches random-suffix siblings of the JSON document. */
export function accountsBlobListPrefix(pathname: string): string {
  return pathname.replace(/\.json$/i, "");
}

/**
 * Prefer the exact pathname. If the store has duplicates (same pathname or
 * random-suffix siblings), take the newest `uploadedAt`.
 */
export function pickNewestAccountBlob(
  blobs: BlobListRow[],
  pathname: string,
): BlobListRow | null {
  const prefix = accountsBlobListPrefix(pathname);
  const matches = blobs.filter(
    (row) =>
      row.pathname === pathname ||
      row.pathname.startsWith(`${pathname}`) ||
      row.pathname === prefix ||
      row.pathname.startsWith(`${prefix}-`) ||
      row.pathname.startsWith(`${prefix}.`),
  );
  if (matches.length === 0) return null;
  const exact = matches.filter((row) => row.pathname === pathname);
  const pool = exact.length > 0 ? exact : matches;
  return (
    pool.slice().sort((a, b) => {
      const ta = a.uploadedAt ? Date.parse(String(a.uploadedAt)) : 0;
      const tb = b.uploadedAt ? Date.parse(String(b.uploadedAt)) : 0;
      return tb - ta;
    })[0] ?? null
  );
}

export function createBlobJsonSnapshot(
  env: NodeJS.ProcessEnv = process.env,
  deps?: BlobSnapshotDeps,
  options: BlobSnapshotOptions = {},
): JsonSnapshot {
  const pathname = accountsBlobPath(env);
  const timeoutMs = options.timeoutMs ?? BLOB_SNAPSHOT_TIMEOUT_MS;
  return {
    async read() {
      return withTimeout(
        readBlobSnapshot(pathname, env, deps, timeoutMs),
        timeoutMs,
        BLOB_SNAPSHOT_TIMEOUT_MESSAGE,
      );
    },
    async write(payload: string) {
      const putFn = deps?.put ?? (await loadBlobSdk()).put;
      await withTimeout(
        Promise.resolve(
          putFn(pathname, payload, {
            access: "private",
            addRandomSuffix: false,
            allowOverwrite: true,
            cacheControlMaxAge: 60,
            contentType: "application/json",
            abortSignal: abortSignalTimeout(timeoutMs),
          }),
        ),
        timeoutMs,
        BLOB_SNAPSHOT_TIMEOUT_MESSAGE,
      );
    },
  };
}

async function readBlobSnapshot(
  pathname: string,
  env: NodeJS.ProcessEnv,
  deps: BlobSnapshotDeps | undefined,
  timeoutMs: number,
): Promise<string | null> {
  const sdk = deps ?? (await loadBlobSdk());
  const listed = await tryListAccountBlobs(sdk, pathname, timeoutMs);
  if (listed) {
    const match = pickNewestAccountBlob(listed, pathname);
    if (!match) return null;
    const fromUrl = await tryGetBlobText(sdk.get, match.url, timeoutMs);
    if (fromUrl !== undefined) return fromUrl;
    const fetched = await tryFetchPrivateBlob(match, env, timeoutMs);
    if (fetched !== undefined) return fetched;
    const fromPath = await tryGetBlobText(sdk.get, pathname, timeoutMs);
    if (fromPath !== undefined) return fromPath;
    throw new Error("Blob account store read failed.");
  }

  const fromPath = await tryGetBlobText(sdk.get, pathname, timeoutMs);
  return fromPath ?? null;
}

async function tryListAccountBlobs(
  sdk: BlobSnapshotDeps,
  pathname: string,
  timeoutMs: number,
): Promise<BlobListRow[] | null> {
  const listFn = sdk.list;
  if (!listFn) return null;
  try {
    const { blobs } = await withTimeout(
      listFn({
        prefix: accountsBlobListPrefix(pathname),
        limit: 20,
        abortSignal: abortSignalTimeout(timeoutMs),
      }),
      timeoutMs,
      BLOB_SNAPSHOT_TIMEOUT_MESSAGE,
    );
    return blobs ?? [];
  } catch (error) {
    if (isAbortOrTimeoutError(error) || isTimeoutMessage(error)) {
      throw error instanceof Error
        ? error
        : new Error(BLOB_SNAPSHOT_TIMEOUT_MESSAGE);
    }
    return null;
  }
}

async function tryGetBlobText(
  getFn: BlobSnapshotDeps["get"],
  ref: string,
  timeoutMs: number,
): Promise<string | undefined> {
  try {
    const result = await withTimeout(
      getFn(ref, {
        access: "private",
        useCache: false,
        abortSignal: abortSignalTimeout(timeoutMs),
      }),
      timeoutMs,
      BLOB_SNAPSHOT_TIMEOUT_MESSAGE,
    );
    if (!result || result.statusCode === 404) return undefined;
    if (result.statusCode && result.statusCode !== 200) return undefined;
    if (!result.stream) return undefined;
    return await new Response(result.stream).text();
  } catch (error) {
    if (isMissingBlob(error)) return undefined;
    if (isAbortOrTimeoutError(error) || isTimeoutMessage(error)) {
      throw error instanceof Error
        ? error
        : new Error(BLOB_SNAPSHOT_TIMEOUT_MESSAGE);
    }
    return undefined;
  }
}

async function tryFetchPrivateBlob(
  match: BlobListRow,
  env: NodeJS.ProcessEnv,
  timeoutMs: number,
): Promise<string | undefined> {
  const token = env.BLOB_READ_WRITE_TOKEN?.trim();
  const url = match.downloadUrl ?? match.url;
  if (!url) return undefined;
  try {
    const response = await withTimeout(
      fetch(url, {
        cache: "no-store",
        signal: abortSignalTimeout(timeoutMs),
        headers: token ? { authorization: `Bearer ${token}` } : undefined,
      }),
      timeoutMs,
      BLOB_SNAPSHOT_TIMEOUT_MESSAGE,
    );
    if (response.status === 404) return undefined;
    if (!response.ok) {
      throw new Error(`Blob account store read failed (${response.status}).`);
    }
    return await response.text();
  } catch (error) {
    if (isMissingBlob(error)) return undefined;
    throw error;
  }
}

function isTimeoutMessage(error: unknown): boolean {
  return error instanceof Error && error.message === BLOB_SNAPSHOT_TIMEOUT_MESSAGE;
}

type BlobSdk = {
  get: BlobSnapshotDeps["get"];
  put: BlobSnapshotDeps["put"];
  list: NonNullable<BlobSnapshotDeps["list"]>;
};

async function loadBlobSdk(): Promise<BlobSdk> {
  const mod = (await import("@vercel/blob")) as BlobSdk;
  return mod;
}

function isMissingBlob(error: unknown): boolean {
  if (!error || typeof error !== "object") return false;
  const status =
    "status" in error
      ? Number((error as { status?: unknown }).status)
      : "statusCode" in error
        ? Number((error as { statusCode?: unknown }).statusCode)
        : NaN;
  return status === 404;
}

export type RedisSnapshotDeps = {
  fetchImpl?: typeof fetch;
};

export function createRedisJsonSnapshot(
  env: NodeJS.ProcessEnv = process.env,
  deps: RedisSnapshotDeps = {},
): JsonSnapshot {
  const cfg = redisRestConfig(env);
  if (!cfg) {
    throw new Error(
      "Redis account store requires UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN (or KV_REST_API_URL / KV_REST_API_TOKEN).",
    );
  }
  const fetchImpl = deps.fetchImpl ?? fetch;
  return {
    async read() {
      const result = await redisCommand(cfg, fetchImpl, ["GET", cfg.key]);
      if (result == null) return null;
      if (typeof result === "string") return result;
      if (typeof result === "object") return JSON.stringify(result);
      return String(result);
    },
    async write(payload: string) {
      await redisCommand(cfg, fetchImpl, ["SET", cfg.key, payload]);
    },
  };
}

async function redisCommand(
  cfg: RedisRestConfig,
  fetchImpl: typeof fetch,
  command: unknown[],
): Promise<unknown> {
  const response = await withTimeout(
    fetchImpl(cfg.url, {
      method: "POST",
      headers: {
        authorization: `Bearer ${cfg.token}`,
        "content-type": "application/json",
      },
      body: JSON.stringify(command),
      signal: abortSignalTimeout(BLOB_SNAPSHOT_TIMEOUT_MS),
    }),
    BLOB_SNAPSHOT_TIMEOUT_MS,
    BLOB_SNAPSHOT_TIMEOUT_MESSAGE,
  );
  if (!response.ok) {
    throw new Error(`Redis account store request failed (${response.status}).`);
  }
  const body = (await response.json()) as { result?: unknown; error?: string };
  if (typeof body.error === "string" && body.error) {
    throw new Error("Redis account store rejected the command.");
  }
  return body.result;
}
