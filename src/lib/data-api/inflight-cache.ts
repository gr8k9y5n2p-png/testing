/**
 * Process-local short-TTL cache + in-flight dedupe.
 *
 * Browser: collapses Compare + Growth & Tax duplicate posts.
 * Server: warm-instance catalog / coverage reuse. Serverless does not
 * share this across isolates — Data API work still belongs upstream.
 *
 * Consumer AbortSignals do not cancel the shared load. A sibling
 * (Upcoming vs Growth) must still receive the result.
 */

export const COMPARE_CACHE_TTL_MS = 45_000;
export const PERFORMANCE_CACHE_TTL_MS = 45_000;
export const FUNDS_SEARCH_CACHE_TTL_MS = 30_000;
export const CATALOG_CACHE_TTL_MS = 60_000;

type CacheEntry<T> = {
  value: T;
  expiresAt: number;
};

export function abortable<T>(
  promise: Promise<T>,
  signal?: AbortSignal,
): Promise<T> {
  if (!signal) return promise;
  if (signal.aborted) {
    return Promise.reject(
      signal.reason ?? new DOMException("Aborted", "AbortError"),
    );
  }
  return new Promise((resolve, reject) => {
    const onAbort = () => {
      reject(signal.reason ?? new DOMException("Aborted", "AbortError"));
    };
    signal.addEventListener("abort", onAbort, { once: true });
    promise.then(
      (value) => {
        signal.removeEventListener("abort", onAbort);
        resolve(value);
      },
      (error) => {
        signal.removeEventListener("abort", onAbort);
        reject(error);
      },
    );
  });
}

export function createInflightCache<T>(ttlMs: number) {
  const values = new Map<string, CacheEntry<T>>();
  const inflight = new Map<string, Promise<T>>();

  function get(key: string): T | undefined {
    const hit = values.get(key);
    if (!hit) return undefined;
    if (hit.expiresAt <= Date.now()) {
      values.delete(key);
      return undefined;
    }
    return hit.value;
  }

  function set(key: string, value: T) {
    values.set(key, { value, expiresAt: Date.now() + ttlMs });
  }

  function remember(
    key: string,
    load: () => Promise<T>,
    signal?: AbortSignal,
  ): Promise<T> {
    const cached = get(key);
    if (cached !== undefined) {
      return abortable(Promise.resolve(cached), signal);
    }

    let pending = inflight.get(key);
    if (!pending) {
      pending = load().then(
        (value) => {
          set(key, value);
          inflight.delete(key);
          return value;
        },
        (error) => {
          inflight.delete(key);
          throw error;
        },
      );
      inflight.set(key, pending);
    }

    return abortable(pending, signal);
  }

  function remove(key: string) {
    values.delete(key);
  }

  function clear() {
    values.clear();
    inflight.clear();
  }

  return { get, set, remember, remove, clear };
}
