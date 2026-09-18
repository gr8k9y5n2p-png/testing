import {
  AccountAuthError,
  requestPasswordReset,
  resetAccountPassword,
  signInAccount,
  signUpAccount,
} from "./auth.ts";
import {
  isHttpsRequest,
  readAccountIdFromRequest,
  serializeAccountCookie,
  serializeClearedAccountCookie,
} from "./session.ts";
import {
  ACCOUNT_STORE_NOT_CONFIGURED,
  getAccountStore,
  isEphemeralVercelAccountStore,
  toPublicAccount,
  type AccountStore,
} from "./store.ts";

function json(
  body: unknown,
  status: number,
  setCookie?: string,
): Response {
  const headers = new Headers({ "content-type": "application/json" });
  if (setCookie) headers.append("set-cookie", setCookie);
  return new Response(JSON.stringify(body), { status, headers });
}

async function readJson(request: Request): Promise<unknown> {
  try {
    return await request.json();
  } catch {
    throw new AccountAuthError(400, "Invalid JSON body.");
  }
}

function requestOrigin(request: Request): string | undefined {
  try {
    return new URL(request.url).origin;
  } catch {
    return undefined;
  }
}

function rejectEphemeralVercelStore(): void {
  if (isEphemeralVercelAccountStore()) {
    throw new AccountAuthError(503, ACCOUNT_STORE_NOT_CONFIGURED);
  }
}

export async function handleAccountSignUp(
  request: Request,
  store: AccountStore = getAccountStore(),
): Promise<Response> {
  try {
    rejectEphemeralVercelStore();
    const account = await signUpAccount(store, await readJson(request));
    return json(
      { account },
      201,
      serializeAccountCookie(account.id, isHttpsRequest(request)),
    );
  } catch (error) {
    if (error instanceof AccountAuthError) {
      return json({ detail: error.detail }, error.status);
    }
    return json({ detail: "Couldn’t create that account." }, 500);
  }
}

export async function handleAccountSignIn(
  request: Request,
  store: AccountStore = getAccountStore(),
): Promise<Response> {
  try {
    rejectEphemeralVercelStore();
    const account = await signInAccount(store, await readJson(request));
    return json(
      { account },
      200,
      serializeAccountCookie(account.id, isHttpsRequest(request)),
    );
  } catch (error) {
    if (error instanceof AccountAuthError) {
      return json({ detail: error.detail }, error.status);
    }
    return json({ detail: "Couldn’t sign in." }, 500);
  }
}

export async function handleAccountSignOut(request: Request): Promise<Response> {
  return json(
    { ok: true },
    200,
    serializeClearedAccountCookie(isHttpsRequest(request)),
  );
}

export async function handleAccountMe(
  request: Request,
  store: AccountStore = getAccountStore(),
): Promise<Response> {
  const accountId = readAccountIdFromRequest(request);
  if (!accountId) {
    return json({ account: null }, 200);
  }
  const row = await store.findById(accountId);
  if (!row) return json({ account: null }, 200);
  return json({ account: toPublicAccount(row) }, 200);
}

export async function handleAccountForgot(
  request: Request,
  store: AccountStore = getAccountStore(),
): Promise<Response> {
  try {
    rejectEphemeralVercelStore();
    const result = await requestPasswordReset(store, await readJson(request), {
      origin: requestOrigin(request),
    });
    return json(result, 200);
  } catch (error) {
    if (error instanceof AccountAuthError) {
      return json({ detail: error.detail }, error.status);
    }
    return json({ detail: "Couldn’t start a password reset." }, 500);
  }
}

export async function handleAccountReset(
  request: Request,
  store: AccountStore = getAccountStore(),
): Promise<Response> {
  try {
    rejectEphemeralVercelStore();
    const account = await resetAccountPassword(store, await readJson(request));
    return json(
      { account },
      200,
      serializeAccountCookie(account.id, isHttpsRequest(request)),
    );
  } catch (error) {
    if (error instanceof AccountAuthError) {
      return json({ detail: error.detail }, error.status);
    }
    return json({ detail: "Couldn’t reset that password." }, 500);
  }
}
