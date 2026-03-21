"use client";

import { ArticleCard } from "@/components/article-card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { Article } from "@/types/article";

interface ArticleFeedProps {
  articles: Article[];
  hasMore: boolean;
  hasApiKey: boolean;
  loading: boolean;
  onLoadMore: () => void;
}

export function ArticleFeed({
  articles,
  hasMore,
  hasApiKey,
  loading,
  onLoadMore,
}: ArticleFeedProps) {
  if (loading && articles.length === 0) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="rounded-xl border overflow-hidden">
            <Skeleton className="aspect-video w-full" />
            <div className="p-6 space-y-3">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-6 w-full" />
              <Skeleton className="h-16 w-full" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (articles.length === 0) {
    return (
      <p className="text-center text-muted-foreground py-12">
        {hasApiKey
          ? "No articles found. Try adjusting your filters or refresh to fetch new articles."
          : "No cached articles found. Try adjusting your filters or add your NewsAPI key to fetch fresh headlines."}
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {articles.map((article) => (
        <ArticleCard key={article.id} article={article} />
      ))}
      {hasMore && (
        <div className="text-center py-4">
          <Button variant="outline" onClick={onLoadMore} disabled={loading}>
            {loading ? "Loading..." : "Load More"}
          </Button>
        </div>
      )}
    </div>
  );
}
