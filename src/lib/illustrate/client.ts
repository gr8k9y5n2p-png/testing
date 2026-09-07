import type {
  IllustrateErrorBody,
  IllustrateRequest,
  IllustrateResponse,
} from "@/lib/illustrate/types";

/**
 * Typed Aftertax client for POST /illustrate.
 * Default: local mock at /api/illustrate.
 * Swap to the Data team service with one env var:
 *   NEXT_PUBLIC_ILLUSTRATE_URL=http://localhost:8000/illustrate
 */
export function getIllustrateEndpoint(): string {
  return process.env.NEXT_PUBLIC_ILLUSTRATE_URL?.replace(/\/$/, "") || "/api/illustrate";
}

export function isMockIllustrate(): boolean {
  return !process.env.NEXT_PUBLIC_ILLUSTRATE_URL;
}

export class IllustrateRequestError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code?: string,
  ) {
    super(message);
  }
}

export async function postIllustrate(
  request: IllustrateRequest,
  init?: { signal?: AbortSignal },
): Promise<IllustrateResponse> {
  const response = await fetch(getIllustrateEndpoint(), {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(request),
    signal: init?.signal,
  });

  if (!response.ok) {
    let detail = `Illustrate failed (${response.status})`;
    let code: string | undefined;
    try {
      const body = (await response.json()) as IllustrateErrorBody;
      if (body.detail) detail = body.detail;
      code = body.code;
    } catch {
      /* ignore */
    }
    throw new IllustrateRequestError(detail, response.status, code);
  }

  return (await response.json()) as IllustrateResponse;
}
