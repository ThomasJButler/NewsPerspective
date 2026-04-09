"use client";

import { formatDate } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type { RefreshStatusResponse, StatsResponse } from "@/types/article";

interface RefreshStatusCardProps {
  stats: StatsResponse | null;
  refreshStatus: RefreshStatusResponse | null;
}

type Tone = "processing" | "completed" | "failed" | "idle";

interface Presentation {
  tone: Tone;
  title: string;
  description: string | null;
  timestamp: string | null;
  timestampLabel: string | null;
}

function formatArticleCount(count: number) {
  return `${count} article${count === 1 ? "" : "s"}`;
}

function getPresentation(
  stats: StatsResponse | null,
  refreshStatus: RefreshStatusResponse | null
): Presentation {
  const latestFetch = stats?.latest_fetch ?? null;

  if (refreshStatus?.status === "processing") {
    return {
      tone: "processing",
      title: "Refresh in progress",
      description:
        "Fetching and processing articles while cached headlines stay available.",
      timestamp: refreshStatus.started_at,
      timestampLabel: "started",
    };
  }

  if (refreshStatus?.status === "failed") {
    return {
      tone: "failed",
      title: "Latest refresh failed",
      description: refreshStatus.message,
      timestamp: refreshStatus.finished_at,
      timestampLabel: "finished",
    };
  }

  if (refreshStatus?.status === "completed") {
    const newCount = refreshStatus.new_articles;
    if (newCount > 0) {
      return {
        tone: "completed",
        title: `Added ${formatArticleCount(newCount)}`,
        description: null,
        timestamp: refreshStatus.finished_at,
        timestampLabel: "finished",
      };
    }
    return {
      tone: "completed",
      title: "Refresh finished with no new articles",
      description: null,
      timestamp: refreshStatus.finished_at,
      timestampLabel: "finished",
    };
  }

  if (latestFetch) {
    return {
      tone: "idle",
      title: "Ready to refresh",
      description: null,
      timestamp: latestFetch,
      timestampLabel: "last refreshed",
    };
  }

  return {
    tone: "idle",
    title: "No refresh history yet",
    description:
      "Browse cached articles, then add your NewsAPI key to fetch fresh headlines.",
    timestamp: null,
    timestampLabel: null,
  };
}

const TONE_STYLES: Record<
  Tone,
  { border: string; dot: string; ring: string }
> = {
  processing: {
    border: "border-l-[color:var(--brand)]",
    dot: "bg-[color:var(--brand)]",
    ring: "bg-[color:var(--brand)]",
  },
  completed: {
    border: "border-l-[color:var(--brand)]",
    dot: "bg-[color:var(--brand)]",
    ring: "bg-transparent",
  },
  failed: {
    border: "border-l-destructive",
    dot: "bg-destructive",
    ring: "bg-transparent",
  },
  idle: {
    border: "border-l-border",
    dot: "bg-muted-foreground/50",
    ring: "bg-transparent",
  },
};

export function RefreshStatusCard({
  stats,
  refreshStatus,
}: RefreshStatusCardProps) {
  if (!stats && !refreshStatus) {
    return null;
  }

  const presentation = getPresentation(stats, refreshStatus);
  const styles = TONE_STYLES[presentation.tone];
  const isProcessing = presentation.tone === "processing";

  return (
    <div
      role="status"
      aria-live="polite"
      aria-label="Refresh status"
      className={cn(
        "mb-4 flex items-center gap-3 rounded-md border border-l-4 bg-muted/20 px-4 py-2.5",
        styles.border
      )}
    >
      <span
        className="relative flex h-2.5 w-2.5 shrink-0"
        aria-hidden="true"
      >
        {isProcessing && (
          <span
            className={cn(
              "absolute inline-flex h-full w-full rounded-full opacity-60 animate-ping",
              styles.ring
            )}
          />
        )}
        <span
          className={cn(
            "relative inline-flex h-2.5 w-2.5 rounded-full",
            styles.dot
          )}
        />
      </span>

      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium leading-tight">{presentation.title}</p>
        {presentation.description && (
          <p className="text-xs text-muted-foreground leading-snug mt-0.5 break-words">
            {presentation.description}
          </p>
        )}
      </div>

      {presentation.timestamp && presentation.timestampLabel && (
        <div className="shrink-0 text-xs text-muted-foreground whitespace-nowrap">
          <span className="hidden sm:inline">
            {presentation.timestampLabel}{" "}
          </span>
          <time dateTime={presentation.timestamp}>
            {formatDate(presentation.timestamp)}
          </time>
        </div>
      )}
    </div>
  );
}
