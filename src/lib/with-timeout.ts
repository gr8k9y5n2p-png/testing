/** Bound otherwise-unbounded fetches so UI and serverless handlers cannot hang. */

export function abortSignalTimeout(ms: number): AbortSignal | undefined {
  return typeof AbortSignal !== "undefined" && "timeout" in AbortSignal
    ? AbortSignal.timeout(ms)
    : undefined;
}

export function isAbortOrTimeoutError(error: unknown): boolean {
  if (!error || typeof error !== "object") return false;
  const name = "name" in error ? String((error as { name?: unknown }).name) : "";
  if (name === "AbortError" || name === "TimeoutError") return true;
  return error instanceof Error && /timed out/i.test(error.message);
}

export async function withTimeout<T>(
  work: Promise<T>,
  ms: number,
  message: string,
): Promise<T> {
  let timer: ReturnType<typeof setTimeout> | undefined;
  try {
    return await Promise.race([
      work,
      new Promise<T>((_, reject) => {
        timer = setTimeout(() => reject(new Error(message)), ms);
      }),
    ]);
  } finally {
    if (timer) clearTimeout(timer);
  }
}
