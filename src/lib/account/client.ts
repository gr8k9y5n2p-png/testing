import type { PublicAccount } from "./store.ts";

export type AccountMeResponse = { account: PublicAccount | null };

async function parseError(response: Response): Promise<Error> {
  let detail = "Couldn’t complete that.";
  try {
    const body = (await response.json()) as { detail?: string };
    if (typeof body.detail === "string" && body.detail.trim()) {
      detail = body.detail;
    }
  } catch {
    /* keep default */
  }
  return new Error(detail);
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    credentials: "same-origin",
    ...init,
    headers: {
      accept: "application/json",
      ...(init?.body ? { "content-type": "application/json" } : {}),
      ...init?.headers,
    },
  });
  if (!response.ok) throw await parseError(response);
  return (await response.json()) as T;
}

export async function fetchAccountMe(): Promise<PublicAccount | null> {
  const body = await requestJson<AccountMeResponse>("/api/account/me");
  return body.account ?? null;
}

export async function signUpAccountClient(
  email: string,
  password: string,
): Promise<PublicAccount> {
  const body = await requestJson<{ account: PublicAccount }>("/api/account/signup", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  return body.account;
}

export async function signInAccountClient(
  email: string,
  password: string,
): Promise<PublicAccount> {
  const body = await requestJson<{ account: PublicAccount }>("/api/account/signin", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  return body.account;
}

export async function signOutAccountClient(): Promise<void> {
  await requestJson<{ ok: boolean }>("/api/account/signout", { method: "POST" });
}

export async function requestPasswordResetClient(
  email: string,
): Promise<{ ok: true; detail: string }> {
  return requestJson<{ ok: true; detail: string }>("/api/account/forgot", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export async function resetAccountPasswordClient(
  token: string,
  password: string,
): Promise<PublicAccount> {
  const body = await requestJson<{ account: PublicAccount }>("/api/account/reset", {
    method: "POST",
    body: JSON.stringify({ token, password }),
  });
  return body.account;
}
