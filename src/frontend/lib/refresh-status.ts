import type { RefreshStatusResponse } from "@/types/article";

type RefreshProcessingStatus = Pick<
  RefreshStatusResponse,
  "status" | "started_at"
>;

export function getRefreshProcessingObservationKey(
  refreshStatus: RefreshProcessingStatus | null
): string | null {
  if (refreshStatus?.status !== "processing") {
    return null;
  }

  return refreshStatus.started_at ?? "processing";
}

export function getNextObservedProcessingKey({
  refreshStatus,
  timedOut = false,
}: {
  refreshStatus: RefreshProcessingStatus | null;
  timedOut?: boolean;
}): string | null {
  if (timedOut) {
    return null;
  }

  return getRefreshProcessingObservationKey(refreshStatus);
}

export function shouldResumeRefreshPolling({
  isLoaded,
  refreshStatus,
  refreshing,
  lastObservedProcessingKey,
  timedOutObservationActive = false,
}: {
  isLoaded: boolean;
  refreshStatus: RefreshProcessingStatus | null;
  refreshing: boolean;
  lastObservedProcessingKey: string | null;
  timedOutObservationActive?: boolean;
}): boolean {
  const processingKey = getRefreshProcessingObservationKey(refreshStatus);

  return (
    isLoaded &&
    !refreshing &&
    !timedOutObservationActive &&
    processingKey !== null &&
    lastObservedProcessingKey !== processingKey
  );
}
