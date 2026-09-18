/**
 * Shared JSON snapshots for the account store.
 *
 * Vercel serverless instances do not share `/tmp`. #277 reloads the file on
 * every read, but Production still missed rows written on another instance.
 * These backends keep the same scrypt hashes and JSON shape, and they are
 * visible to every instance immediately.
 */

export type JsonSnapshot = {
  read(): Promise<string | null>;
  write(payload: string): Promise<void>;
};

export const DEFAULT_ACCOUNTS_BLOB_PATH = "aftertax/accounts.json";
export const DEFAULT_ACCOUNTS_REDIS_KEY = "aftertax:accounts";

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

type BlobListResult = {
  blobs: Array<{ pathname: string; url: string; downloadUrl?: string }>;
};

export type BlobSnapshotDeps = {
  get: (
    pathname: string,
    options: { access: "private"; useCache: false },
  ) => Promise<BlobGetResult>;
  put: (
    pathname: string,
    payload: string,
    options: {
      access: "private";
      addRandomSuffix: false;
      allowOverwrite: true;
      cacheControlMaxAge: number;
      contentType: string;
    },
  ) => Promise<unknown>;
  list?: (options: {
    prefix: string;
    limit: number;
  }) => Promise<BlobListResult>;
};

export function accountsBlobPath(
  env: NodeJS.ProcessEnv = process.env,
): string {
  return env.AFTERTAX_ACCOUNTS_BLOB_PATH?.trim() || DEFAULT_ACCOUNTS_BLOB_PATH;
}

export function createBlobJsonSnapshot(
  env: NodeJS.ProcessEnv = process.env,
  deps?: BlobSnapshotDeps,
): JsonSnapshot {
  const pathname = accountsBlobPath(env);
  return {
    async read() {
      const getFn = deps?.get ?? (await loadBlobSdk()).get;
      try {
        const result = await getFn(pathname, {
          access: "private",
          useCache: false,
        });
        if (!result || result.statusCode === 404) return null;
        if (result.statusCode && result.statusCode !== 200) return null;
        if (!result.stream) return null;
        return await new Response(result.stream).text();
      } catch (error) {
        if (isMissingBlob(error)) return null;
        const listFn = deps?.list ?? (await loadBlobSdk()).list;
        const { blobs } = await listFn({ prefix: pathname, limit: 20 });
        const match = blobs.find((row) => row.pathname === pathname);
        if (!match) return null;
        const token = env.BLOB_READ_WRITE_TOKEN?.trim();
        const response = await fetch(match.downloadUrl ?? match.url, {
          cache: "no-store",
          headers: token ? { authorization: `Bearer ${token}` } : undefined,
        });
        if (response.status === 404) return null;
        if (!response.ok) {
          throw new Error(`Blob account store read failed (${response.status}).`);
        }
        return await response.text();
      }
    },
    async write(payload: string) {
      const putFn = deps?.put ?? (await loadBlobSdk()).put;
      await putFn(pathname, payload, {
        access: "private",
        addRandomSuffix: false,
        allowOverwrite: true,
        cacheControlMaxAge: 60,
        contentType: "application/json",
      });
    },
  };
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
  const response = await fetchImpl(cfg.url, {
    method: "POST",
    headers: {
      authorization: `Bearer ${cfg.token}`,
      "content-type": "application/json",
    },
    body: JSON.stringify(command),
  });
  if (!response.ok) {
    throw new Error(`Redis account store request failed (${response.status}).`);
  }
  const body = (await response.json()) as { result?: unknown; error?: string };
  if (typeof body.error === "string" && body.error) {
    throw new Error("Redis account store rejected the command.");
  }
  return body.result;
}
