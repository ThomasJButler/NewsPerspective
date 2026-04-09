"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ApiRequestError, fetchArticle } from "@/lib/api";
import { TldrSection } from "@/components/tldr-section";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { getVisibleHeadline } from "@/lib/headlines";
import { formatDate } from "@/lib/utils";
import { DEMO_ARTICLE_LABEL, isDemoArticle } from "@/lib/demo-articles";
import { toast } from "@/hooks/use-toast";
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
  const [requestVersion, setRequestVersion] = useState(0);

  return (
    <ArticleDetailRequest
      key={`${id}:${requestVersion}`}
      id={id}
      onRetry={() => setRequestVersion((version) => version + 1)}
    />
  );
}

function ArticleDetailRequest({
  id,
  onRetry,
}: {
  id: string;
  onRetry: () => void;
}) {
  const [article, setArticle] = useState<Article | null>(null);
  const [errorState, setErrorState] = useState<{
    kind: "not_found" | "transient";
    message: string;
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    fetchArticle(id)
      .then((nextArticle) => {
        if (cancelled) {
          return;
        }

        setArticle(nextArticle);
      })
      .catch((err) => {
        if (cancelled) {
          return;
        }

        if (err instanceof ApiRequestError && err.status === 404) {
          setErrorState({
            kind: "not_found",
            message: "This article is no longer available in the cache.",
          });
        } else {
          setErrorState({
            kind: "transient",
            message:
              err instanceof Error
                ? err.message
                : "The article could not be loaded right now.",
          });
        }
        toast({
          title: "Failed to load article",
          description: err instanceof Error ? err.message : "Article could not be loaded.",
          variant: "destructive",
        });
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
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

  if (errorState?.kind === "not_found") {
    return (
      <div className="container mx-auto px-4 py-8 max-w-3xl text-center">
        <h1 className="text-2xl font-bold mb-4">Article not found</h1>
        <p className="mb-4 text-muted-foreground">{errorState.message}</p>
        <Link href="/" className="text-primary hover:underline">
          ← Back to news feed
        </Link>
      </div>
    );
  }

  if (errorState?.kind === "transient") {
    return (
      <div className="container mx-auto px-4 py-8 max-w-3xl text-center space-y-4">
        <h1 className="text-2xl font-bold">Unable to load article</h1>
        <p className="text-muted-foreground">{errorState.message}</p>
        <div className="flex items-center justify-center gap-3">
          <Button onClick={onRetry}>Retry</Button>
          <Link href="/" className="text-primary hover:underline">
            ← Back to news feed
          </Link>
        </div>
      </div>
    );
  }

  if (!article) {
    return null;
  }

  const headline = getVisibleHeadline({
    wasRewritten: article.was_rewritten,
    rewrittenTitle: article.rewritten_title,
    originalTitle: article.original_title,
  });
  const imageUrl = article.image_url;
  const showOriginalHeadline = article.was_rewritten && headline !== article.original_title;

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

          {showOriginalHeadline && (
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

        {imageUrl && (
          <div className="relative aspect-[16/9] max-h-96 w-full overflow-hidden rounded-lg">
            <Image
              src={imageUrl}
              alt={headline}
              fill
              unoptimized
              sizes="(min-width: 768px) 768px, 100vw"
              className="object-cover"
            />
          </div>
        )}

        {article.tldr && <TldrSection tldr={article.tldr} />}

        {isDemoArticle(article) ? (
          <span className="inline-block italic text-muted-foreground">
            {DEMO_ARTICLE_LABEL}
          </span>
        ) : (
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block font-medium text-primary hover:underline"
          >
            Read Full Article →
          </a>
        )}
      </article>
    </div>
  );
}
