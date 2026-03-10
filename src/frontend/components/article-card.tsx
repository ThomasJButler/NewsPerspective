"use client";

import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { TldrSection } from "@/components/tldr-section";
import { formatDate, getVisibleHeadline } from "@/lib/utils";
import type { Article } from "@/types/article";

interface ArticleCardProps {
  article: Article;
}

export function ArticleCard({ article }: ArticleCardProps) {
  const headline = getVisibleHeadline({
    wasRewritten: article.was_rewritten,
    rewrittenTitle: article.rewritten_title,
    originalTitle: article.original_title,
  });
  const showOriginalHeadline = article.was_rewritten && headline !== article.original_title;

  return (
    <Card>
      <CardContent className="pt-6 space-y-3">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          {article.source_name && <span>{article.source_name}</span>}
          {article.source_name && article.published_at && (
            <span aria-hidden="true">·</span>
          )}
          {article.published_at && (
            <time dateTime={article.published_at}>
              {formatDate(article.published_at)}
            </time>
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

        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block text-sm font-medium text-primary hover:underline"
        >
          Read Full Article →
        </a>
      </CardContent>
    </Card>
  );
}
