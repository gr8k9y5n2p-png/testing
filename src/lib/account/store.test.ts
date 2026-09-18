import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { signInAccount, signUpAccount } from "./auth.ts";
import { InMemoryJsonSnapshot } from "./json-snapshot.ts";
import { hashPassword, verifyPassword } from "./passwords.ts";
import {
  ACCOUNT_STORE_NOT_CONFIGURED,
  SharedJsonAccountStore,
  createAccountStoreFromEnv,
  isEphemeralVercelAccountStore,
  loadAccountsFromFile,
  mergeAccountRecords,
  parseAccountRecords,
  MemoryAccountStore,
  resolveAccountStoreKind,
  serializeAccountRecords,
} from "./store.ts";
import { handleAccountSignIn, handleAccountSignUp } from "./http.ts";

describe("account store selection", () => {
  it("uses the local file store when no durable backend is configured", () => {
    assert.equal(resolveAccountStoreKind({}), "file");
    assert.equal(isEphemeralVercelAccountStore({}), false);
    assert.equal(
      isEphemeralVercelAccountStore({ VERCEL: "1" }),
      true,
    );
    assert.equal(
      isEphemeralVercelAccountStore({
        VERCEL: "1",
        AFTERTAX_ACCOUNTS_PATH: "/var/data/accounts.json",
      }),
      false,
    );
  });

  it("prefers Redis, then Blob, and honors AFTERTAX_ACCOUNT_STORE=file", () => {
    const redis = {
      UPSTASH_REDIS_REST_URL: "https://example.upstash.io",
      UPSTASH_REDIS_REST_TOKEN: "token",
      BLOB_READ_WRITE_TOKEN: "vercel_blob_rw_x",
    };
    assert.equal(resolveAccountStoreKind(redis), "redis");
    assert.equal(
      resolveAccountStoreKind({ BLOB_READ_WRITE_TOKEN: "vercel_blob_rw_x" }),
      "blob",
    );
    assert.equal(
      resolveAccountStoreKind({ BLOB_STORE_ID: "store_123", VERCEL: "1" }),
      "blob",
    );
    assert.equal(
      resolveAccountStoreKind({
        ...redis,
        AFTERTAX_ACCOUNT_STORE: "file",
      }),
      "file",
    );
    assert.equal(
      isEphemeralVercelAccountStore({
        VERCEL: "1",
        BLOB_READ_WRITE_TOKEN: "vercel_blob_rw_x",
      }),
      false,
    );
  });

  it("does not treat Vercel OIDC alone as a Blob store", () => {
    assert.equal(
      resolveAccountStoreKind({
        VERCEL: "1",
        VERCEL_OIDC_TOKEN: "oidc-not-enough",
      }),
      "file",
    );
  });
});

describe("shared durable account JSON", () => {
  it("lets instance B verify the same scrypt hash instance A just wrote", async () => {
    const box = { raw: null as string | null };
    const writer = new SharedJsonAccountStore(new InMemoryJsonSnapshot(box));
    const reader = new SharedJsonAccountStore(new InMemoryJsonSnapshot(box));
    await signUpAccount(writer, {
      email: "ada@example.com",
      password: "wholesaler",
    });
    const signedIn = await signInAccount(reader, {
      email: "ada@example.com",
      password: "wholesaler",
    });
    assert.equal(signedIn.email, "ada@example.com");
    const stored = parseAccountRecords(box.raw);
    assert.equal(stored.length, 1);
    assert.equal(verifyPassword("wholesaler", stored[0].passwordHash), true);
    assert.match(stored[0].passwordHash, /^scrypt\$/);
    assert.doesNotMatch(box.raw ?? "", /wholesaler/);
  });

  it("merges leftover file-store accounts into an empty durable snapshot once", async () => {
    const dir = mkdtempSync(join(tmpdir(), "aftertax-accounts-"));
    const filePath = join(dir, "accounts.json");
    const hash = hashPassword("wholesaler");
    writeFileSync(
      filePath,
      serializeAccountRecords([
        {
          id: "acct_11111111-1111-1111-1111-111111111111",
          email: "eric@example.com",
          passwordHash: hash,
          stripeCustomerId: null,
          stripeSubscriptionId: null,
          subscriptionStatus: null,
          cancelAtPeriodEnd: false,
          currentPeriodEnd: null,
          usage: { searches: 0, compareKeys: [], portfolioKeys: [] },
          createdAt: "2026-01-01T00:00:00.000Z",
          updatedAt: "2026-01-01T00:00:00.000Z",
        },
      ]),
    );
    const box = { raw: null as string | null };
    const store = new SharedJsonAccountStore(new InMemoryJsonSnapshot(box), {
      legacyFilePath: filePath,
    });
    const signedIn = await signInAccount(store, {
      email: "eric@example.com",
      password: "wholesaler",
    });
    assert.equal(signedIn.email, "eric@example.com");
    assert.equal(loadAccountsFromFile(filePath)[0].passwordHash, hash);
    const durable = parseAccountRecords(box.raw);
    assert.equal(durable[0].passwordHash, hash);
  });

  it("reuses a fresh hydrate cache so checkout updateBilling does not re-read Blob", async () => {
    let reads = 0;
    const box = { raw: null as string | null };
    const store = new SharedJsonAccountStore({
      async read() {
        reads += 1;
        return box.raw;
      },
      async write(payload) {
        box.raw = payload;
      },
    });
    const row = await store.create({
      email: "ada@example.com",
      passwordHash: hashPassword("wholesaler"),
    });
    assert.equal(reads, 1);
    assert.equal((await store.findById(row.id))?.email, "ada@example.com");
    assert.equal(reads, 1);
    const billed = await store.updateBilling(row.id, {
      stripeCustomerId: "cus_cached",
    });
    assert.equal(billed?.stripeCustomerId, "cus_cached");
    assert.equal(reads, 1);
  });

  it("keeps durable hashes when the same email exists in the leftover file", () => {
    const durableHash = hashPassword("durable-pass");
    const fileHash = hashPassword("file-pass");
    const merged = mergeAccountRecords(
      [
        {
          id: "acct_11111111-1111-1111-1111-111111111111",
          email: "ada@example.com",
          passwordHash: durableHash,
          stripeCustomerId: null,
          stripeSubscriptionId: null,
          subscriptionStatus: null,
          cancelAtPeriodEnd: false,
          currentPeriodEnd: null,
          usage: { searches: 0, compareKeys: [], portfolioKeys: [] },
          createdAt: "2026-01-01T00:00:00.000Z",
          updatedAt: "2026-01-01T00:00:00.000Z",
        },
      ],
      [
        {
          id: "acct_22222222-2222-2222-2222-222222222222",
          email: "ada@example.com",
          passwordHash: fileHash,
          stripeCustomerId: null,
          stripeSubscriptionId: null,
          subscriptionStatus: null,
          cancelAtPeriodEnd: false,
          currentPeriodEnd: null,
          usage: { searches: 0, compareKeys: [], portfolioKeys: [] },
          createdAt: "2026-01-01T00:00:00.000Z",
          updatedAt: "2026-01-01T00:00:00.000Z",
        },
      ],
    );
    assert.equal(merged.added, 0);
    assert.equal(merged.records[0].passwordHash, durableHash);
  });
});

describe("ephemeral Vercel account HTTP", () => {
  it("refuses sign-up and sign-in instead of writing a /tmp row that other instances cannot see", async () => {
    const prior = process.env.VERCEL;
    const priorBlob = process.env.BLOB_READ_WRITE_TOKEN;
    const priorStore = process.env.BLOB_STORE_ID;
    const priorRedisUrl = process.env.UPSTASH_REDIS_REST_URL;
    const priorRedisToken = process.env.UPSTASH_REDIS_REST_TOKEN;
    const priorKvUrl = process.env.KV_REST_API_URL;
    const priorKvToken = process.env.KV_REST_API_TOKEN;
    const priorPath = process.env.AFTERTAX_ACCOUNTS_PATH;
    const priorKind = process.env.AFTERTAX_ACCOUNT_STORE;
    process.env.VERCEL = "1";
    delete process.env.BLOB_READ_WRITE_TOKEN;
    delete process.env.BLOB_STORE_ID;
    delete process.env.UPSTASH_REDIS_REST_URL;
    delete process.env.UPSTASH_REDIS_REST_TOKEN;
    delete process.env.KV_REST_API_URL;
    delete process.env.KV_REST_API_TOKEN;
    delete process.env.AFTERTAX_ACCOUNTS_PATH;
    delete process.env.AFTERTAX_ACCOUNT_STORE;
    try {
      const store = new MemoryAccountStore();
      const signup = await handleAccountSignUp(
        new Request("http://localhost/api/account/signup", {
          method: "POST",
          body: JSON.stringify({
            email: "ada@aftertax.com",
            password: "password1",
          }),
        }),
        store,
      );
      assert.equal(signup.status, 503);
      const signupBody = (await signup.json()) as { detail: string };
      assert.equal(signupBody.detail, ACCOUNT_STORE_NOT_CONFIGURED);
      const signin = await handleAccountSignIn(
        new Request("http://localhost/api/account/signin", {
          method: "POST",
          body: JSON.stringify({
            email: "ada@aftertax.com",
            password: "password1",
          }),
        }),
        store,
      );
      assert.equal(signin.status, 503);
    } finally {
      if (prior == null) delete process.env.VERCEL;
      else process.env.VERCEL = prior;
      if (priorBlob == null) delete process.env.BLOB_READ_WRITE_TOKEN;
      else process.env.BLOB_READ_WRITE_TOKEN = priorBlob;
      if (priorStore == null) delete process.env.BLOB_STORE_ID;
      else process.env.BLOB_STORE_ID = priorStore;
      if (priorRedisUrl == null) delete process.env.UPSTASH_REDIS_REST_URL;
      else process.env.UPSTASH_REDIS_REST_URL = priorRedisUrl;
      if (priorRedisToken == null) delete process.env.UPSTASH_REDIS_REST_TOKEN;
      else process.env.UPSTASH_REDIS_REST_TOKEN = priorRedisToken;
      if (priorKvUrl == null) delete process.env.KV_REST_API_URL;
      else process.env.KV_REST_API_URL = priorKvUrl;
      if (priorKvToken == null) delete process.env.KV_REST_API_TOKEN;
      else process.env.KV_REST_API_TOKEN = priorKvToken;
      if (priorPath == null) delete process.env.AFTERTAX_ACCOUNTS_PATH;
      else process.env.AFTERTAX_ACCOUNTS_PATH = priorPath;
      if (priorKind == null) delete process.env.AFTERTAX_ACCOUNT_STORE;
      else process.env.AFTERTAX_ACCOUNT_STORE = priorKind;
    }
  });
});

describe("account store docs", () => {
  it("documents Blob and Redis env vars and the /tmp root cause", () => {
    const here = dirname(fileURLToPath(import.meta.url));
    const readme = readFileSync(join(here, "../../../README.md"), "utf8");
    const env = readFileSync(join(here, "../../../.env.example"), "utf8");
    for (const source of [readme, env]) {
      assert.match(source, /BLOB_READ_WRITE_TOKEN/);
      assert.match(source, /BLOB_STORE_ID/);
      assert.match(source, /UPSTASH_REDIS_REST_URL/);
      assert.match(source, /UPSTASH_REDIS_REST_TOKEN/);
      assert.match(source, /\/tmp/);
    }
    assert.match(readme, /useCache: false/);
    assert.match(readme, /cannot be recovered/);
    assert.match(readme, /2\.5s wall-clock budget/);
    assert.match(readme, /8s overall budget/);
    assert.match(env, /AFTERTAX_CHECKOUT_TIMEOUT_MS/);
  });
});

describe("account HTTP store timeout", () => {
  it("returns 504 with the timeout detail instead of hanging", async () => {
    const store = new MemoryAccountStore();
    store.create = async () => {
      throw new Error("Account storage timed out. Try again.");
    };
    const signup = await handleAccountSignUp(
      new Request("http://localhost/api/account/signup", {
        method: "POST",
        body: JSON.stringify({
          email: "ada@aftertax.com",
          password: "password1",
        }),
      }),
      store,
    );
    assert.equal(signup.status, 504);
    const body = (await signup.json()) as { detail: string };
    assert.match(body.detail, /timed out/);
  });
});

describe("createAccountStoreFromEnv", () => {
  it("builds a file store for local tests when AFTERTAX_ACCOUNTS_PATH is set", async () => {
    const dir = mkdtempSync(join(tmpdir(), "aftertax-accounts-"));
    const filePath = join(dir, "accounts.json");
    const store = createAccountStoreFromEnv({
      AFTERTAX_ACCOUNT_STORE: "file",
      AFTERTAX_ACCOUNTS_PATH: filePath,
    });
    await store.create({
      email: "ada@aftertax.com",
      passwordHash: hashPassword("wholesaler"),
    });
    const row = await store.findByEmail("ada@aftertax.com");
    assert.equal(row?.email, "ada@aftertax.com");
    assert.equal(
      verifyPassword(
        "wholesaler",
        JSON.parse(readFileSync(filePath, "utf8"))[0].passwordHash,
      ),
      true,
    );
  });
});
