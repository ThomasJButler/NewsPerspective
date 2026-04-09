"use client";

import { formatDate } from "@/lib/utils";
import type { StatsResponse } from "@/types/article";

interface StatsBarProps {
  stats: StatsResponse | null;
}

export function StatsBar({ stats }: StatsBarProps) {
  if (!stats || stats.total_articles === 0) return null;

  return (
    <p
      className="flex flex-wrap items-center justify-center gap-x-2 gap-y-1 text-sm text-muted-foreground text-center py-2"
      aria-live="polite"
    >
      <span>
        {stats.total_articles} article{stats.total_articles !== 1 ? "s" : ""}{" "}
        processed
      </span>
      <span aria-hidden="true">·</span>
      <span>
        {stats.rewritten_count} headline
        {stats.rewritten_count !== 1 ? "s" : ""} improved
      </span>
      <span aria-hidden="true">·</span>
      <span>{stats.good_news_count} good news</span>
      <span aria-hidden="true">·</span>
      <span>
        {stats.sources_count} source{stats.sources_count !== 1 ? "s" : ""}
      </span>
      {stats.latest_fetch && (
        <>
          <span aria-hidden="true">·</span>
          <span>
            updated{" "}
            <time dateTime={stats.latest_fetch}>
              {formatDate(stats.latest_fetch)}
            </time>
          </span>
        </>
      )}
    </p>
  );
}
