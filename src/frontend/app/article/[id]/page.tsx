"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { fetchArticle } from "@/lib/api";
import { TldrSection } from "@/components/tldr-section";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDate } from "@/lib/utils";
import type { Article } from "@/types/article";

function sentimentVariant(
  sentiment: string | null
): "default" | "secondary" | "destructive" {
  if (sentiment === "positive") return "default";
  if (sentiment === "negative") return "destructive";
  return "secondary";
}

export default function ArticleDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [article, setArticle] = useState<Article | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchArticle(id)
      .then(setArticle)
      .catch(() => setNotFound(true))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-3xl space-y-4">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-8 w-full" />
        <Skeleton className="h-20 w-full" />
      </div>
    );
  }

  if (notFound || !article) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-3xl text-center">
        <h1 className="text-2xl font-bold mb-4">Article not found</h1>
        <Link href="/" className="text-primary hover:underline">
          ← Back to news feed
        </Link>
      </div>
    );
  }

  const headline = article.was_rewritten
    ? article.rewritten_title
    : article.original_title;

  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      <Link
        href="/"
        className="text-sm text-muted-foreground hover:text-foreground mb-6 inline-block"
      >
        ← Back to news feed
      </Link>

      <article className="space-y-6">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold leading-tight">{headline}</h1>

          {article.was_rewritten && (
            <p className="text-sm text-muted-foreground italic">
              Original: {article.original_title}
            </p>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
          {article.source_name && <span>{article.source_name}</span>}
          {article.author && <span>by {article.author}</span>}
          {article.published_at && (
            <time dateTime={article.published_at}>
              {formatDate(article.published_at)}
            </time>
          )}
          {article.original_sentiment && (
            <Badge variant={sentimentVariant(article.original_sentiment)}>
              {article.original_sentiment}
            </Badge>
          )}
        </div>

        {article.image_url && (
          <img
            src={article.image_url}
            alt=""
            className="w-full rounded-lg object-cover max-h-96"
          />
        )}

        {article.tldr && <TldrSection tldr={article.tldr} />}

        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block font-medium text-primary hover:underline"
        >
          Read Full Article →
        </a>
      </article>
    </div>
  );
}
