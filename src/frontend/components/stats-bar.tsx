"use client";

import type { StatsResponse } from "@/types/article";

interface StatsBarProps {
  stats: StatsResponse | null;
}

export function StatsBar({ stats }: StatsBarProps) {
  if (!stats || stats.total_articles === 0) return null;

  return (
    <p className="text-sm text-muted-foreground text-center py-2">
      {stats.total_articles} article{stats.total_articles !== 1 ? "s" : ""}{" "}
      processed · {stats.rewritten_count} headline
      {stats.rewritten_count !== 1 ? "s" : ""} improved
    </p>
  );
}
