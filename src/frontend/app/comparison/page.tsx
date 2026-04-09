"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { fetchComparisonGroups, analyseComparisonGroup } from "@/lib/api";
import type {
  ComparisonGroup,
  ComparisonAnalysis,
} from "@/types/article";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "@/hooks/use-toast";
import { formatDate } from "@/lib/utils";
import { DEMO_ARTICLE_LABEL, isDemoArticle } from "@/lib/demo-articles";

function sentimentVariant(
  sentiment: string | null
): "default" | "secondary" | "destructive" {
  if (sentiment === "positive") return "default";
  if (sentiment === "negative") return "destructive";
  return "secondary";
}

function ComparisonGroupCard({ group }: { group: ComparisonGroup }) {
  const [analysis, setAnalysis] = useState<ComparisonAnalysis | null>(null);
  const [analysing, setAnalysing] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const handleAnalyse = async () => {
    setAnalysing(true);
    try {
      const result = await analyseComparisonGroup(
        group.articles.map((a) => a.id)
      );
      setAnalysis(result);
      setExpanded(true);
    } catch (err) {
      toast({
        title: "Analysis failed",
        description:
          err instanceof Error ? err.message : "Could not analyse this group.",
        variant: "destructive",
      });
    } finally {
      setAnalysing(false);
    }
  };

  return (
    <Card>
      <CardContent className="p-6 space-y-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="space-y-2 flex-1">
            <h2 className="text-lg font-semibold leading-tight">
              {group.representative_title}
            </h2>
            <div className="flex flex-wrap items-center gap-2">
              {group.countries.map((c) => (
                <span
                  key={c}
                  className="text-xs uppercase font-medium text-muted-foreground"
                >
                  {c === "gb" ? "UK" : "US"}
                </span>
              ))}
              {group.sources.map((s) => (
                <Badge key={s} variant="secondary">
                  {s}
                </Badge>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? "Collapse" : "Compare"}
            </Button>
            {!analysis && (
              <Button
                size="sm"
                onClick={handleAnalyse}
                disabled={analysing}
              >
                {analysing ? "Analysing..." : "AI Analysis"}
              </Button>
            )}
          </div>
        </div>

        {expanded && (
          <div className="space-y-4 pt-2">
            <div className="grid gap-4 sm:grid-cols-2">
              {group.articles.map((article) => (
                <div
                  key={article.id}
                  className="rounded-lg border p-4 space-y-2"
                >
                  <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                    <span className="text-xs uppercase font-medium">
                      {article.country === "gb" ? "UK" : "US"}
                    </span>
                    {article.source_name && (
                      <span>{article.source_name}</span>
                    )}
                    {article.original_sentiment && (
                      <Badge
                        variant={sentimentVariant(article.original_sentiment)}
                      >
                        {article.original_sentiment}
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm font-medium leading-snug">
                    {article.rewritten_title || article.original_title}
                  </p>
                  {article.published_at && (
                    <p className="text-xs text-muted-foreground">
                      {formatDate(article.published_at)}
                    </p>
                  )}
                  {isDemoArticle(article) ? (
                    <span className="inline-block text-xs italic text-muted-foreground">
                      {DEMO_ARTICLE_LABEL}
                    </span>
                  ) : (
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-block text-xs font-medium text-primary hover:underline"
                    >
                      Read Full Article →
                    </a>
                  )}
                </div>
              ))}
            </div>

            {analysis && (
              <div className="space-y-4 pt-2">
                <div className="bg-muted/50 rounded-lg px-4 py-3 border-l-4 border-primary/30 space-y-2">
                  <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    AI Analysis
                  </span>
                  <p className="text-sm leading-relaxed">{analysis.summary}</p>
                </div>

                {analysis.framing_differences.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-sm font-semibold">
                      Framing Differences
                    </h3>
                    <ul className="space-y-1 text-sm text-muted-foreground list-disc list-inside">
                      {analysis.framing_differences.map((diff, i) => (
                        <li key={i}>{diff}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {analysis.source_tones.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-sm font-semibold">Source Tones</h3>
                    <div className="grid gap-2 sm:grid-cols-2">
                      {analysis.source_tones.map((st, i) => (
                        <div
                          key={i}
                          className="rounded-lg border p-3 space-y-1"
                        >
                          <div className="flex items-center gap-2">
                            <span className="text-xs uppercase font-medium text-muted-foreground">
                              {st.country === "gb" ? "UK" : "US"}
                            </span>
                            <span className="text-sm font-medium">
                              {st.source_name}
                            </span>
                          </div>
                          <p className="text-sm text-muted-foreground">
                            {st.tone}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function ComparisonPage() {
  const [groups, setGroups] = useState<ComparisonGroup[]>([]);
  const [loading, setLoading] = useState(true);

  const loadGroups = useCallback(async () => {
    try {
      const data = await fetchComparisonGroups();
      setGroups(data.groups);
    } catch (err) {
      toast({
        title: "Failed to load comparisons",
        description:
          err instanceof Error
            ? err.message
            : "Could not load comparison groups.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadGroups();
  }, [loadGroups]);

  return (
    <div className="min-h-screen">
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 max-w-4xl">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Article Comparison</h1>
              <p className="text-sm text-muted-foreground">
                See how different sources cover the same story.
              </p>
            </div>
            <Link
              href="/"
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              ← Back to feed
            </Link>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6 max-w-4xl">
        {loading && (
          <div className="space-y-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="rounded-xl border p-6 space-y-3">
                <Skeleton className="h-6 w-3/4" />
                <Skeleton className="h-4 w-48" />
                <Skeleton className="h-4 w-full" />
              </div>
            ))}
          </div>
        )}

        {!loading && groups.length === 0 && (
          <p className="text-center text-muted-foreground py-12">
            No comparison groups found. Related stories from different sources
            will appear here after a refresh.
          </p>
        )}

        {!loading && groups.length > 0 && (
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground text-center">
              {groups.length} story group{groups.length !== 1 ? "s" : ""} found
            </p>
            {groups.map((group, i) => (
              <ComparisonGroupCard key={i} group={group} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
