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

/** One wall-clock budget for a chain of Blob / Stripe calls. */
export class Deadline {
  private readonly end: number;

  constructor(ms: number) {
    this.end = Date.now() + Math.max(1, ms);
  }

  remaining(): number {
    return Math.max(0, this.end - Date.now());
  }

  async race<T>(work: Promise<T>, message: string): Promise<T> {
    const left = this.remaining();
    if (left <= 0) throw new Error(message);
    return withTimeout(work, left, message);
  }
}
