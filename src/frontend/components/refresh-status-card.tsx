"use client";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { formatDate } from "@/lib/utils";
import type { RefreshStatusResponse, StatsResponse } from "@/types/article";

interface RefreshStatusCardProps {
  stats: StatsResponse | null;
  refreshStatus: RefreshStatusResponse | null;
}

type BadgeVariant = "default" | "secondary" | "destructive" | "outline";

function formatArticleCount(count: number) {
  return `${count} article${count === 1 ? "" : "s"}`;
}

function getRefreshPresentation(
  stats: StatsResponse | null,
  refreshStatus: RefreshStatusResponse | null
): {
  badge: string;
  badgeVariant: BadgeVariant;
  title: string;
  description: string;
} {
  if (!refreshStatus) {
    if (stats?.latest_fetch) {
      return {
        badge: "Ready",
        badgeVariant: "outline",
        title: "Ready to refresh",
        description:
          "No refresh is running. Cached headlines still reflect the latest successful fetch.",
      };
    }

    return {
      badge: "Idle",
      badgeVariant: "outline",
      title: "No refresh history yet",
      description:
        "Browse cached articles now, then add your NewsAPI key whenever you want to fetch fresh headlines.",
    };
  }

  if (refreshStatus.status === "processing") {
    return {
      badge: "Processing",
      badgeVariant: "default",
      title: "Refresh in progress",
      description:
        "Fetching and processing articles in the background while cached headlines stay available.",
    };
  }

  if (refreshStatus.status === "failed") {
    return {
      badge: "Failed",
      badgeVariant: "destructive",
      title: "Latest refresh failed",
      description: refreshStatus.message,
    };
  }

  if (refreshStatus.status === "completed") {
    if (refreshStatus.new_articles > 0) {
      return {
        badge: "Completed",
        badgeVariant: "secondary",
        title: `Latest refresh added ${formatArticleCount(refreshStatus.new_articles)}.`,
        description: `Processed ${formatArticleCount(refreshStatus.processed_articles)} in the latest run.`,
      };
    }

    return {
      badge: "Completed",
      badgeVariant: "secondary",
      title: "Latest refresh finished with no new articles.",
      description: `Processed ${formatArticleCount(refreshStatus.processed_articles)} without adding anything new to the cache.`,
    };
  }

  if (stats?.latest_fetch) {
    return {
      badge: "Ready",
      badgeVariant: "outline",
      title: "Ready to refresh",
      description:
        "No refresh is running. Cached headlines still reflect the latest successful fetch.",
    };
  }

  return {
    badge: "Idle",
    badgeVariant: "outline",
    title: "No refresh history yet",
    description:
      "Browse cached articles now, then add your NewsAPI key whenever you want to fetch fresh headlines.",
  };
}

export function RefreshStatusCard({
  stats,
  refreshStatus,
}: RefreshStatusCardProps) {
  if (!stats && !refreshStatus) {
    return null;
  }

  const presentation = getRefreshPresentation(stats, refreshStatus);
  const lastRefreshed = stats?.latest_fetch;
  const startedAt = refreshStatus?.status === "processing"
    ? refreshStatus.started_at
    : null;
  const finishedAt =
    refreshStatus?.status === "completed" || refreshStatus?.status === "failed"
      ? refreshStatus.finished_at
      : null;

  return (
    <Card
      className="mb-6 gap-4 border-dashed"
      role="status"
      aria-live="polite"
      aria-label="Refresh status"
    >
      <CardHeader className="gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-2">
          <Badge variant={presentation.badgeVariant}>{presentation.badge}</Badge>
          <div className="space-y-1">
            <CardTitle>{presentation.title}</CardTitle>
            <CardDescription>{presentation.description}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="grid gap-2 text-sm text-muted-foreground">
        {lastRefreshed && (
          <p>
            Last refreshed{" "}
            <time dateTime={lastRefreshed}>{formatDate(lastRefreshed)}</time>.
          </p>
        )}
        {startedAt && (
          <p>
            Started <time dateTime={startedAt}>{formatDate(startedAt)}</time>.
          </p>
        )}
        {finishedAt && (
          <p>
            Last refresh finished{" "}
            <time dateTime={finishedAt}>{formatDate(finishedAt)}</time>.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
