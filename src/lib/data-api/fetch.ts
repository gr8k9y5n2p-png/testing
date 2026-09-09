import { dataApiUrl, isRemoteDataApi } from "@/lib/data-api/config";

export async function fetchDataApi(
  path: string,
  init?: RequestInit & { fallbackPath?: string },
): Promise<Response> {
  const remote = isRemoteDataApi();
  const { fallbackPath, ...fetchInit } = init ?? {};
  const endpoint = dataApiUrl(path);
  const fallback =
    fallbackPath ?? `/api${path.startsWith("/") ? path : `/${path}`}`;
  const headers: HeadersInit = {
    Accept: "application/json",
    ...(fetchInit.body ? { "Content-Type": "application/json" } : {}),
    ...fetchInit.headers,
  };

  try {
    const response = await fetch(endpoint, {
      ...fetchInit,
      headers,
      cache: fetchInit.cache ?? "no-store",
    });
    if (
      !remote &&
      !response.ok &&
      response.status >= 500 &&
      fallback !== endpoint
    ) {
      return fetch(fallback, {
        ...fetchInit,
        headers,
        cache: fetchInit.cache ?? "no-store",
      });
    }
    return response;
  } catch (error) {
    if (!remote && fallback !== endpoint && !fetchInit.signal?.aborted) {
      return fetch(fallback, {
        ...fetchInit,
        headers,
        cache: fetchInit.cache ?? "no-store",
      });
    }
    throw error;
  }
}
