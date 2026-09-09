import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  demoEngineNotes,
  isMockChromeNote,
  userFacingNotes,
} from "./user-facing-notes.ts";

describe("user-facing MOCK chrome", () => {
  it("drops the GTM-failing Search / Portfolio banners", () => {
    assert.equal(
      isMockChromeNote(
        "MOCK /illustrate — sample seed math, not the Data team service. Set NEXT_PUBLIC_ILLUSTRATE_URL to swap.",
      ),
      true,
    );
    assert.equal(
      isMockChromeNote(
        "MOCK /illustrate/portfolio. Set NEXT_PUBLIC_DATA_API_URL to use the Data team endpoint.",
      ),
      true,
    );
    assert.equal(
      isMockChromeNote(
        "MOCK /illustrate/portfolio/compare — sample seed math, not the Data team service.",
      ),
      true,
    );
    assert.deepEqual(
      userFacingNotes([
        "MOCK /illustrate — sample seed math, not the Data team service.",
        "Selected rows span more than one publication_stage / as_of snapshot.",
      ]),
      ["Selected rows span more than one publication_stage / as_of snapshot."],
    );
  });

  it("keeps real coverage / API notes", () => {
    assert.equal(isMockChromeNote("Coverage gap: live ingest today is Capital Group."), false);
    assert.deepEqual(userFacingNotes(["No unpaid announced estimates."]), [
      "No unpaid announced estimates.",
    ]);
  });

  it("emits no MOCK banners when the live Data API is configured", () => {
    const prior = process.env.NEXT_PUBLIC_DATA_API_URL;
    process.env.NEXT_PUBLIC_DATA_API_URL = "https://data.example.test";
    try {
      assert.deepEqual(
        demoEngineNotes("MOCK /illustrate — sample seed math, not the Data team service."),
        [],
      );
    } finally {
      if (prior == null) delete process.env.NEXT_PUBLIC_DATA_API_URL;
      else process.env.NEXT_PUBLIC_DATA_API_URL = prior;
    }
  });
});
