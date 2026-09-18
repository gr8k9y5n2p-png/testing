/**
 * Shared JSON snapshots for the account store.
 *
 * Vercel serverless instances do not share `/tmp`. Production uses Redis
 * (preferred, one REST GET/SET) or private Blob. Private `get(pathname)`
 * can 404 or hang after `put`; reads therefore list the prefix and fetch
 * the newest blob URL with a Bearer token. One wall-clock budget covers
 * the whole read or write — stacked per-call 8s timeouts were how
 * signup/checkout hit the 20–45s client TimeoutError after #281.
 *
 * A miss is an empty document (`null`). Budget overruns throw — they must
 * not look like empty, or the next write would wipe hashes.
 */

import {
  Deadline,
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
/** Whole read or write — not per SDK call. Signup = read + write ≤ ~5s. */
export const BLOB_SNAPSHOT_TIMEOUT_MS = 2_500;
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

export type BlobPutResult = {
  url?: string;
  downloadUrl?: string;
  pathname?: string;
};

export type BlobSnapshotDeps = {
  get: (pathname: string, options: BlobGetOptions) => Promise<BlobGetResult>;
  put: (
    pathname: string,
    payload: string,
    options: BlobPutOptions,
  ) => Promise<BlobPutResult | unknown>;
  list?: (options: {
    prefix: string;
    limit: number;
    abortSignal?: AbortSignal;
  }) => Promise<BlobListResult>;
  fetchImpl?: typeof fetch;
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
  let lastMatch: BlobListRow | null = null;
  return {
    async read() {
      const deadline = new Deadline(timeoutMs);
      return deadline.race(
        readBlobSnapshot(pathname, env, deps, deadline, () => lastMatch, (row) => {
          lastMatch = row;
        }),
        BLOB_SNAPSHOT_TIMEOUT_MESSAGE,
      );
    },
    async write(payload: string) {
      const deadline = new Deadline(timeoutMs);
      const putFn = deps?.put ?? (await loadBlobSdk()).put;
      const result = await deadline.race(
        Promise.resolve(
          putFn(pathname, payload, {
            access: "private",
            addRandomSuffix: false,
            allowOverwrite: true,
            cacheControlMaxAge: 60,
            contentType: "application/json",
            abortSignal: abortSignalTimeout(deadline.remaining()),
          }),
        ),
        BLOB_SNAPSHOT_TIMEOUT_MESSAGE,
      );
      const url =
        result && typeof result === "object" && "url" in result
          ? String((result as BlobPutResult).url ?? "")
          : "";
      if (url) {
        const downloadUrl =
          result && typeof result === "object" && "downloadUrl" in result
            ? String((result as BlobPutResult).downloadUrl ?? "")
            : "";
        lastMatch = {
          pathname,
          url,
          downloadUrl: downloadUrl || undefined,
        };
      }
    },
  };
}

async function readBlobSnapshot(
  pathname: string,
  env: NodeJS.ProcessEnv,
  deps: BlobSnapshotDeps | undefined,
  deadline: Deadline,
  getLastMatch: () => BlobListRow | null,
  setLastMatch: (row: BlobListRow) => void,
): Promise<string | null> {
  const sdk = deps ?? (await loadBlobSdk());
  const fetchImpl = deps?.fetchImpl ?? fetch;

  const cached = getLastMatch();
  if (cached) {
    const fromCache = await tryFetchPrivateBlob(cached, env, deadline, fetchImpl);
    if (fromCache !== undefined) return fromCache;
  }

  const listed = await tryListAccountBlobs(sdk, pathname, deadline);
  if (listed) {
    const match = pickNewestAccountBlob(listed, pathname);
    if (!match) return null;
    setLastMatch(match);
    const fetched = await tryFetchPrivateBlob(match, env, deadline, fetchImpl);
    if (fetched !== undefined) return fetched;
    const fromUrl = await tryGetBlobText(sdk.get, match.url, deadline);
    if (fromUrl !== undefined) return fromUrl;
    throw new Error("Blob account store read failed.");
  }

  const fromPath = await tryGetBlobText(sdk.get, pathname, deadline);
  return fromPath ?? null;
}

async function tryListAccountBlobs(
  sdk: BlobSnapshotDeps,
  pathname: string,
  deadline: Deadline,
): Promise<BlobListRow[] | null> {
  const listFn = sdk.list;
  if (!listFn) return null;
  try {
    const { blobs } = await deadline.race(
      listFn({
        prefix: accountsBlobListPrefix(pathname),
        limit: 20,
        abortSignal: abortSignalTimeout(deadline.remaining()),
      }),
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
  deadline: Deadline,
): Promise<string | undefined> {
  if (deadline.remaining() <= 0) {
    throw new Error(BLOB_SNAPSHOT_TIMEOUT_MESSAGE);
  }
  try {
    const result = await deadline.race(
      getFn(ref, {
        access: "private",
        useCache: false,
        abortSignal: abortSignalTimeout(deadline.remaining()),
      }),
      BLOB_SNAPSHOT_TIMEOUT_MESSAGE,
    );
    if (!result || result.statusCode === 404) return undefined;
    if (result.statusCode && result.statusCode !== 200) return undefined;
    if (!result.stream) return undefined;
    return await deadline.race(
      new Response(result.stream).text(),
      BLOB_SNAPSHOT_TIMEOUT_MESSAGE,
    );
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
  deadline: Deadline,
  fetchImpl: typeof fetch,
): Promise<string | undefined> {
  const token = env.BLOB_READ_WRITE_TOKEN?.trim();
  const url = match.downloadUrl ?? match.url;
  if (!url) return undefined;
  if (deadline.remaining() <= 0) {
    throw new Error(BLOB_SNAPSHOT_TIMEOUT_MESSAGE);
  }
  try {
    const response = await deadline.race(
      fetchImpl(url, {
        cache: "no-store",
        signal: abortSignalTimeout(deadline.remaining()),
        headers: token ? { authorization: `Bearer ${token}` } : undefined,
      }),
      BLOB_SNAPSHOT_TIMEOUT_MESSAGE,
    );
    if (response.status === 404) return undefined;
    if (!response.ok) return undefined;
    return await deadline.race(response.text(), BLOB_SNAPSHOT_TIMEOUT_MESSAGE);
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

function isTimeoutMessage(error: unknown): boolean {
  return error instanceof Error && error.message === BLOB_SNAPSHOT_TIMEOUT_MESSAGE;
}

type BlobSdk = {
  get: BlobSnapshotDeps["get"];
  put: BlobSnapshotDeps["put"];
  list: NonNullable<BlobSnapshotDeps["list"]>;
};

async function loadBlobSdk(): Promise<BlobSdk> {
  const modLib = (await import("@vercel/blob")) as BlobSdk;
  return modLib;
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
