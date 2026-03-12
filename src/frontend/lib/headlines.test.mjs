import assert from "node:assert/strict";
import test from "node:test";

import { getVisibleHeadline } from "./headlines.ts";

test("prefers a rewritten headline when the article was rewritten", () => {
  assert.equal(
    getVisibleHeadline({
      wasRewritten: true,
      rewrittenTitle: "A calmer, clearer headline",
      originalTitle: "Original headline",
    }),
    "A calmer, clearer headline"
  );
});

test("falls back to the original headline when the rewritten title is blank", () => {
  assert.equal(
    getVisibleHeadline({
      wasRewritten: true,
      rewrittenTitle: "   ",
      originalTitle: "Original headline",
    }),
    "Original headline"
  );
});

test("uses the original headline when the article was not rewritten", () => {
  assert.equal(
    getVisibleHeadline({
      wasRewritten: false,
      rewrittenTitle: "Alternative headline",
      originalTitle: "Original headline",
    }),
    "Original headline"
  );
});
