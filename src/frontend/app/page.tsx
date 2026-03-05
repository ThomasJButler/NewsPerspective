"use client";

import { Suspense, useEffect, useState, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useApiKey } from "@/hooks/use-api-key";
import { useDebounce } from "@/hooks/use-debounce";
import {
  fetchArticles,
  fetchSources,
  fetchStats,
  refreshArticles,
} from "@/lib/api";
import type { Article, Source, StatsResponse } from "@/types/article";
import { ApiKeySetup } from "@/components/api-key-setup";
import { Header } from "@/components/header";
import { GoodNewsToggle } from "@/components/good-news-toggle";
import { SourceFilter } from "@/components/source-filter";
import { StatsBar } from "@/components/stats-bar";
import { ArticleFeed } from "@/components/article-feed";
import { SettingsDialog } from "@/components/settings-dialog";
import { toast } from "@/hooks/use-toast";

function HomeContent() {
  const { apiKey, setApiKey, clearApiKey, hasApiKey, isLoaded } = useApiKey();
  const router = useRouter();
  const searchParams = useSearchParams();

  const [articles, setArticles] = useState<Article[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  const [searchValue, setSearchValue] = useState(
    searchParams.get("search") || ""
  );
  const [goodNewsOnly, setGoodNewsOnly] = useState(
    searchParams.get("good_news") === "true"
  );
  const [sourceFilter, setSourceFilter] = useState(
    searchParams.get("source") || "all"
  );

  const debouncedSearch = useDebounce(searchValue);

  useEffect(() => {
    const params = new URLSearchParams();
    if (debouncedSearch) params.set("search", debouncedSearch);
    if (goodNewsOnly) params.set("good_news", "true");
    if (sourceFilter !== "all") params.set("source", sourceFilter);
    const qs = params.toString();
    router.replace(qs ? `?${qs}` : "/", { scroll: false });
  }, [debouncedSearch, goodNewsOnly, sourceFilter, router]);

  const loadArticles = useCallback(
    async (pageNum: number, append = false) => {
      setLoading(true);
      try {
        const data = await fetchArticles({
          page: pageNum,
          search: debouncedSearch || undefined,
          good_news_only: goodNewsOnly || undefined,
          source: sourceFilter !== "all" ? sourceFilter : undefined,
        });
        setArticles((prev) =>
          append ? [...prev, ...data.articles] : data.articles
        );
        setHasMore(data.has_more);
        setPage(data.page);
      } catch (err) {
        toast({
          title: "Failed to load articles",
          description: err instanceof Error ? err.message : "Please try again later.",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    },
    [debouncedSearch, goodNewsOnly, sourceFilter]
  );

  useEffect(() => {
    if (isLoaded) {
      loadArticles(1);
    }
  }, [isLoaded, loadArticles]);

  useEffect(() => {
    if (!isLoaded) return;
    fetchSources()
      .then((d) => setSources(d.sources))
      .catch(() => {
        // Sources/stats are non-critical — silently degrade
      });
    fetchStats()
      .then((d) => setStats(d))
      .catch(() => {});
  }, [isLoaded]);

  const handleRefresh = async () => {
    if (!apiKey) return;
    setRefreshing(true);
    try {
      await refreshArticles(apiKey);
      setTimeout(() => {
        loadArticles(1);
        fetchSources()
          .then((d) => setSources(d.sources))
          .catch(() => {});
        fetchStats()
          .then((d) => setStats(d))
          .catch(() => {});
        setRefreshing(false);
      }, 3000);
    } catch (err) {
      setRefreshing(false);
      const message = err instanceof Error ? err.message : "Refresh failed";
      toast({
        title: "Refresh failed",
        description: message.includes("401")
          ? "Invalid API key. Check your key in Settings."
          : message,
        variant: "destructive",
      });
    }
  };

  const handleLoadMore = () => {
    loadArticles(page + 1, true);
  };

  if (!isLoaded) return null;

  if (!hasApiKey) {
    return <ApiKeySetup onSubmit={setApiKey} />;
  }

  return (
    <div className="min-h-screen">
      <Header
        searchValue={searchValue}
        onSearchChange={setSearchValue}
        onSettingsClick={() => setSettingsOpen(true)}
        onRefreshClick={handleRefresh}
        refreshing={refreshing}
      />

      <main className="container mx-auto px-4 py-6 max-w-3xl">
        <div className="flex flex-wrap items-center gap-4 mb-4">
          <GoodNewsToggle
            checked={goodNewsOnly}
            onCheckedChange={setGoodNewsOnly}
          />
          <SourceFilter
            sources={sources}
            value={sourceFilter}
            onValueChange={setSourceFilter}
          />
        </div>

        <StatsBar stats={stats} />

        <ArticleFeed
          articles={articles}
          hasMore={hasMore}
          loading={loading}
          onLoadMore={handleLoadMore}
        />
      </main>

      <SettingsDialog
        open={settingsOpen}
        onOpenChange={setSettingsOpen}
        apiKey={apiKey}
        onUpdateKey={setApiKey}
        onClearKey={clearApiKey}
      />
    </div>
  );
}

export default function HomePage() {
  return (
    <Suspense>
      <HomeContent />
    </Suspense>
  );
}
