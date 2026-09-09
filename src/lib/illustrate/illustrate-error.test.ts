import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  formatIllustrateValidationErrors,
  userFacingIllustrateError,
} from "./illustrate-error.ts";

describe("illustrate validation errors", () => {
  it("surfaces FastAPI tax_rates extra_forbidden paths", () => {
    const body = {
      detail: "Validation failed",
      errors: [
        {
          type: "extra_forbidden",
          loc: ["body", "tax_rates", "ordinary"],
          msg: "Extra inputs are not permitted",
          input: 0.37,
        },
        {
          type: "extra_forbidden",
          loc: ["body", "tax_rates", "ltcg"],
          msg: "Extra inputs are not permitted",
          input: 0.2,
        },
      ],
    };
    assert.equal(
      formatIllustrateValidationErrors(body),
      "tax_rates.ordinary: Extra inputs are not permitted; tax_rates.ltcg: Extra inputs are not permitted",
    );
    assert.equal(
      userFacingIllustrateError(body, "Portfolio compare failed (422)").message,
      "tax_rates.ordinary: Extra inputs are not permitted; tax_rates.ltcg: Extra inputs are not permitted",
    );
  });

  it("keeps a string detail when there is no errors list", () => {
    assert.equal(
      userFacingIllustrateError({ detail: "current.holdings is required" }, "fallback")
        .message,
      "current.holdings is required",
    );
    assert.equal(formatIllustrateValidationErrors({ detail: "Validation failed" }), null);
  });
});
