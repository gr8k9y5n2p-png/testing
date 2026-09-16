import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  PORTFOLIO_PAYLOAD_VERSION,
  SAVED_ASSETS_CONTRACT,
  SAVED_ASSETS_ENDPOINTS,
} from "./contract.ts";

const here = dirname(fileURLToPath(import.meta.url));

describe("saved-assets Modules contract", () => {
  it("exports the account-scoped HTTP surface Modules can import", () => {
    assert.equal(SAVED_ASSETS_CONTRACT.apiPath, "/api/saved-assets");
    assert.deepEqual(SAVED_ASSETS_CONTRACT.types, ["list", "portfolio"]);
    assert.equal(PORTFOLIO_PAYLOAD_VERSION, 1);
    assert.equal(SAVED_ASSETS_ENDPOINTS.collection, "/api/saved-assets");
    assert.match(SAVED_ASSETS_CONTRACT.auth, /Account session/);
    assert.equal(SAVED_ASSETS_CONTRACT.accountCookie, "aftertax_account");
  });

  it("documents list tickers[] and portfolio { version, books }", () => {
    const contract = readFileSync(join(here, "contract.ts"), "utf8");
    const docs = readFileSync(join(here, "../../../docs/saved-assets.md"), "utf8");
    for (const source of [contract, docs]) {
      assert.match(source, /tickers: string\[\]/);
      assert.match(source, /version/);
      assert.match(source, /books/);
      assert.match(source, /aftertax_account/);
      assert.match(source, /\/api\/saved-assets/);
    }
  });
});
