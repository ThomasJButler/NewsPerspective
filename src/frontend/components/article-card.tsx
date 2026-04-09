"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { TldrSection } from "@/components/tldr-section";
import { getVisibleHeadline } from "@/lib/headlines";
import { formatDate } from "@/lib/utils";
import { DEMO_ARTICLE_LABEL, isDemoArticle } from "@/lib/demo-articles";
import type { Article } from "@/types/article";

function sentimentVariant(
  sentiment: string | null
): "default" | "secondary" | "destructive" {
  if (sentiment === "positive") return "default";
  if (sentiment === "negative") return "destructive";
  return "secondary";
}

interface ArticleCardProps {
  article: Article;
}

export function ArticleCard({ article }: ArticleCardProps) {
  const [imgError, setImgError] = useState(false);
  const headline = getVisibleHeadline({
    wasRewritten: article.was_rewritten,
    rewrittenTitle: article.rewritten_title,
    originalTitle: article.original_title,
  });
  const showOriginalHeadline = article.was_rewritten && headline !== article.original_title;
  const showImage = Boolean(article.image_url) && !imgError;
  const isDemo = isDemoArticle(article);

  return (
    <Card className="overflow-hidden">
      <CardContent className="p-0">
        {showImage && (
          <div className="relative aspect-video w-full overflow-hidden">
            <Image
              src={article.image_url!}
              alt=""
              fill
              unoptimized
              sizes="(min-width: 768px) 768px, 100vw"
              className="object-cover"
              onError={() => setImgError(true)}
            />
          </div>
        )}

        <div className="space-y-3 p-6">
          <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            {article.country && (
              <span className="text-xs uppercase font-medium">
                {article.country === "gb" ? "UK" : "US"}
              </span>
            )}
            {article.source_name && <span>{article.source_name}</span>}
            {article.source_name && article.published_at && (
              <span aria-hidden="true">·</span>
            )}
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
            {isDemo && (
              <Badge variant="outline" className="text-xs">
                Demo
              </Badge>
            )}
          </div>

          <Link href={`/article/${article.id}`}>
            <h2 className="text-xl font-semibold leading-tight hover:underline">
              {headline}
            </h2>
          </Link>

          {article.tldr && <TldrSection tldr={article.tldr} />}

          {showOriginalHeadline && (
            <details className="text-sm">
              <summary className="text-muted-foreground cursor-pointer hover:text-foreground">
                Original headline
              </summary>
              <p className="mt-1 text-muted-foreground italic">
                {article.original_title}
              </p>
            </details>
          )}

          {isDemo ? (
            <span className="inline-block text-sm italic text-muted-foreground">
              {DEMO_ARTICLE_LABEL}
            </span>
          ) : (
            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block text-sm font-semibold text-[color:var(--brand)] hover:underline underline-offset-4"
            >
              Read Full Article →
            </a>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
