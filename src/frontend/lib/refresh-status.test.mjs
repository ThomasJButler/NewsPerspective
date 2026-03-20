import assert from "node:assert/strict";
import test from "node:test";

import {
  getNextObservedProcessingKey,
  getRefreshProcessingObservationKey,
  shouldResumeRefreshPolling,
} from "./refresh-status.ts";

const processingStatus = {
  status: "processing",
  started_at: "2026-03-11T10:00:00Z",
};

test("uses started_at as the processing observation key", () => {
  assert.equal(
    getRefreshProcessingObservationKey(processingStatus),
    "2026-03-11T10:00:00Z"
  );
});

test("falls back to a stable processing key when started_at is missing", () => {
  assert.equal(
    getRefreshProcessingObservationKey({
      status: "processing",
      started_at: null,
    }),
    "processing"
  );
});

test("clears the observed processing key after a polling timeout", () => {
  assert.equal(
    getNextObservedProcessingKey({
      refreshStatus: processingStatus,
      timedOut: true,
    }),
    null
  );
});

test("allows the same in-flight refresh to be resumed after timeout", () => {
  const lastObservedProcessingKey = getNextObservedProcessingKey({
    refreshStatus: processingStatus,
    timedOut: true,
  });

  assert.equal(
    shouldResumeRefreshPolling({
      isLoaded: true,
      refreshStatus: processingStatus,
      refreshing: false,
      lastObservedProcessingKey,
      timedOutObservationActive: true,
    }),
    false
  );

  assert.equal(
    shouldResumeRefreshPolling({
      isLoaded: true,
      refreshStatus: processingStatus,
      refreshing: false,
      lastObservedProcessingKey,
      timedOutObservationActive: false,
    }),
    true
  );
});
