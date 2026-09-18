/**
 * Shared JSON snapshots for the account store.
 *
 * Vercel serverless instances do not share `/tmp`. Production uses Redis
 * (preferred: REST GET + EVAL compare-and-swap) or private Blob. A stale
 * unconditional PUT used to clobber newer signups (lost update). Writes
 * therefore CAS: Redis Lua SET-if-GET-matches; Blob `accounts.vN.json`
 * with allowOverwrite false so a stale put cannot replace a newer gen.
 *
 * Private `get(pathname)` can 404 or hang after `put`; reads list the
 * prefix (highest generation wins) and fetch that URL with a Bearer token.
 * Isolate last-URL reuse expires in 2.5s so another instance's write is
 * visible. One wall-clock budget covers the whole read or write.
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

export type JsonSnapshotReadOptions = {
  /** Skip isolate last-URL reuse and list the newest durable document. */
  fresh?: boolean;
};

export type JsonSnapshot = {
  read(options?: JsonSnapshotReadOptions): Promise<string | null>;
  write(payload: string): Promise<void>;
  /**
   * Atomic replace if `expected` still is the durable document (`null` = missing).
   * Returns false on conflict so the caller can hydrate and retry.
   */
  compareAndSwap?(expected: string | null, next: string): Promise<boolean>;
};

export async function compareAndSwapSnapshot(
  snapshot: JsonSnapshot,
  expected: string | null,
  next: string,
): Promise<boolean> {
  if (snapshot.compareAndSwap) {
    return snapshot.compareAndSwap(expected, next);
  }
  await snapshot.write(next);
  return true;
}

export const DEFAULT_ACCOUNTS_BLOB_PATH = "aftertax/accounts.json";
export const DEFAULT_ACCOUNTS_REDIS_KEY = "aftertax:accounts";
/** Whole read or write — not per SDK call. Signup = read + write ≤ ~5s. */
export const BLOB_SNAPSHOT_TIMEOUT_MS = 2_500;
export const BLOB_LAST_MATCH_MS = 2_500;
export const BLOB_SNAPSHOT_TIMEOUT_MESSAGE =
  "Account storage timed out. Try again.";
/** Lua: SET only when GET still matches the expected document (missing = ""). */
export const REDIS_CAS_SCRIPT = [
  "local current = redis.call('GET', KEYS[1])",
  "if current == false then",
  "  current = ''",
  "end",
  "if current == ARGV[1] then",
  "  redis.call('SET', KEYS[1], ARGV[2])",
  "  return 1",
  "end",
  "return 0",
].join("\n");

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

  async compareAndSwap(expected: string | null, next: string): Promise<boolean> {
    if ((this.box.raw ?? null) !== (expected ?? null)) return false;
    this.box.raw = next;
    return true;
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
  allowOverwrite: boolean;
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
  del?: (urlOrPathname: string | string[]) => Promise<void>;
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

export function accountsBlobVersionPath(
  pathname: string,
  generation: number,
): string {
  if (generation <= 0) return pathname;
  return `${accountsBlobListPrefix(pathname)}.v${generation}.json`;
}

export function accountsBlobGeneration(
  blobPathname: string,
  basePathname: string,
): number | null {
  if (blobPathname === basePathname) return 0;
  const prefix = accountsBlobListPrefix(basePathname);
  const escaped = prefix.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = blobPathname.match(new RegExp(`^${escaped}\\.v(\\d+)\\.json$`, "i"));
  return match ? Number(match[1]) : null;
}

function blobGenerationRank(blobPathname: string, basePathname: string): number {
  const generation = accountsBlobGeneration(blobPathname, basePathname);
  if (generation != null) return generation;
  return blobPathname === basePathname ? 0 : -1;
}

/**
 * Prefer the highest generation (`accounts.json` = 0, `accounts.vN.json` = N).
 * Same generation: newest `uploadedAt`. Random-suffix siblings rank below.
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
  return (
    matches.slice().sort((a, b) => {
      const ga = blobGenerationRank(a.pathname, pathname);
      const gb = blobGenerationRank(b.pathname, pathname);
      if (ga !== gb) return gb - ga;
      const ta = a.uploadedAt ? Date.parse(String(a.uploadedAt)) : 0;
      const tb = b.uploadedAt ? Date.parse(String(b.uploadedAt)) : 0;
      return tb - ta;
    })[0] ?? null
  );
}

type CachedBlobMatch = BlobListRow & { generation: number; at: number };

export function createBlobJsonSnapshot(
  env: NodeJS.ProcessEnv = process.env,
  deps?: BlobSnapshotDeps,
  options: BlobSnapshotOptions = {},
): JsonSnapshot {
  const pathname = accountsBlobPath(env);
  const timeoutMs = options.timeoutMs ?? BLOB_SNAPSHOT_TIMEOUT_MS;
  let lastMatch: CachedBlobMatch | null = null;
  let lastRead: { raw: string | null; generation: number } | null = null;

  const rememberMatch = (row: BlobListRow, generation?: number): CachedBlobMatch => {
    const gen = generation ?? accountsBlobGeneration(row.pathname, pathname) ?? 0;
    const cached = { ...row, generation: gen, at: Date.now() };
    lastMatch = cached;
    return cached;
  };

  const putPayload = async (
    target: string,
    payload: string,
    allowOverwrite: boolean,
    deadline: Deadline,
  ): Promise<BlobPutResult | unknown> => {
    const putFn = deps?.put ?? (await loadBlobSdk()).put;
    return deadline.race(
      Promise.resolve(
        putFn(target, payload, {
          access: "private",
          addRandomSuffix: false,
          allowOverwrite,
          cacheControlMaxAge: 60,
          contentType: "application/json",
          abortSignal: abortSignalTimeout(deadline.remaining()),
        }),
      ),
      BLOB_SNAPSHOT_TIMEOUT_MESSAGE,
    );
  };

  const rememberPut = (
    target: string,
    generation: number,
    payload: string,
    result: BlobPutResult | unknown,
  ): void => {
    const url =
      result && typeof result === "object" && "url" in result
        ? String((result as BlobPutResult).url ?? "")
        : "";
    const downloadUrl =
      result && typeof result === "object" && "downloadUrl" in result
        ? String((result as BlobPutResult).downloadUrl ?? "")
        : "";
    lastRead = { raw: payload, generation };
    if (url) {
      rememberMatch(
        {
          pathname: target,
          url,
          downloadUrl: downloadUrl || undefined,
        },
        generation,
      );
    } else {
      rememberMatch({ pathname: target, url: target }, generation);
    }
  };

  const deleteSuperseded = async (generation: number): Promise<void> => {
    const delFn = deps ? deps.del : (await loadBlobSdk()).del;
    if (!delFn) return;
    const stale = [accountsBlobVersionPath(pathname, generation - 1)];
    if (generation > 0) stale.push(pathname);
    try {
      await delFn(stale);
    } catch {
      /* best-effort — leftover gens are ignored when listing */
    }
  };

  return {
    async read(readOptions?: JsonSnapshotReadOptions) {
      const deadline = new Deadline(timeoutMs);
      if (readOptions?.fresh) {
        lastMatch = null;
      } else if (lastMatch && Date.now() - lastMatch.at >= BLOB_LAST_MATCH_MS) {
        lastMatch = null;
      }
      const raw = await deadline.race(
        readBlobSnapshot(
          pathname,
          env,
          deps,
          deadline,
          () => lastMatch,
          (row) => {
            rememberMatch(row);
          },
        ),
        BLOB_SNAPSHOT_TIMEOUT_MESSAGE,
      );
      lastRead = {
        raw,
        generation: lastMatch?.generation ?? 0,
      };
      return raw;
    },
    async write(payload: string) {
      const deadline = new Deadline(timeoutMs);
      const result = await putPayload(pathname, payload, true, deadline);
      rememberPut(pathname, 0, payload, result);
    },
    async compareAndSwap(expected: string | null, next: string) {
      const deadline = new Deadline(timeoutMs);
      if (!lastRead || lastRead.raw !== expected) {
        lastMatch = null;
        const current = await deadline.race(
          readBlobSnapshot(
            pathname,
            env,
            deps,
            deadline,
            () => null,
            (row) => {
              rememberMatch(row);
            },
          ),
          BLOB_SNAPSHOT_TIMEOUT_MESSAGE,
        );
        lastRead = {
          raw: current,
          generation: lastMatch?.generation ?? 0,
        };
        if (current !== expected) return false;
      }
      const nextGeneration = (lastRead.generation ?? 0) + 1;
      const target = accountsBlobVersionPath(pathname, nextGeneration);
      try {
        const result = await putPayload(target, next, false, deadline);
        rememberPut(target, nextGeneration, next, result);
        void deleteSuperseded(nextGeneration);
        return true;
      } catch (error) {
        if (isBlobAlreadyExists(error)) {
          lastMatch = null;
          lastRead = null;
          return false;
        }
        throw error;
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
        limit: 100,
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
  del?: BlobSnapshotDeps["del"];
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

export function isBlobAlreadyExists(error: unknown): boolean {
  if (!error || typeof error !== "object") return false;
  const status =
    "status" in error
      ? Number((error as { status?: unknown }).status)
      : "statusCode" in error
        ? Number((error as { statusCode?: unknown }).statusCode)
        : NaN;
  if (status === 409 || status === 412) return true;
  const code =
    "code" in error ? String((error as { code?: unknown }).code) : "";
  if (/already.?exist/i.test(code)) return true;
  return error instanceof Error && /already.?exist/i.test(error.message);
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
    async compareAndSwap(expected: string | null, next: string) {
      const result = await redisCommand(cfg, fetchImpl, [
        "EVAL",
        REDIS_CAS_SCRIPT,
        1,
        cfg.key,
        expected ?? "",
        next,
      ]);
      return result === 1 || result === "1" || result === true;
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
