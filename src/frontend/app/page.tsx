"use client";

import { Suspense, useEffect, useState, useCallback, useRef } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useApiKey } from "@/hooks/use-api-key";
import { useDebounce } from "@/hooks/use-debounce";
import {
  fetchArticles,
  fetchRefreshStatus,
  fetchSources,
  fetchStats,
  RefreshRequestError,
  refreshArticles,
} from "@/lib/api";
import type { Article, Source, StatsResponse } from "@/types/article";
import { ApiKeySetup } from "@/components/api-key-setup";
import { Header } from "@/components/header";
import { GoodNewsToggle } from "@/components/good-news-toggle";
import { SourceFilter } from "@/components/source-filter";
import { StatsBar } from "@/components/stats-bar";
import { ArticleFeed } from "@/components/article-feed";
import {
  SettingsDialog,
  type ApiKeyFeedback,
} from "@/components/settings-dialog";
import { toast } from "@/hooks/use-toast";

const REFRESH_STATUS_POLL_INTERVAL_MS = 1000;
const REFRESH_STATUS_TIMEOUT_MS = 120000;
const DUPLICATE_REFRESH_MESSAGE = "Refresh already in progress.";

function HomeContent() {
  const { apiKey, setApiKey, clearApiKey, hasApiKey, isLoaded } = useApiKey();
  const router = useRouter();
  const searchParams = useSearchParams();
  const onboardingRef = useRef<HTMLDivElement>(null);

  const [articles, setArticles] = useState<Article[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [apiKeyFeedback, setApiKeyFeedback] = useState<ApiKeyFeedback | null>(
    null
  );

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
  const effectiveSourceFilter =
    sourceFilter === "all" ||
    sources.length === 0 ||
    sources.some((source) => source.source_name === sourceFilter)
      ? sourceFilter
      : "all";

  useEffect(() => {
    const params = new URLSearchParams();
    if (debouncedSearch) params.set("search", debouncedSearch);
    if (goodNewsOnly) params.set("good_news", "true");
    if (effectiveSourceFilter !== "all") {
      params.set("source", effectiveSourceFilter);
    }
    const qs = params.toString();
    router.replace(qs ? `?${qs}` : "/", { scroll: false });
  }, [debouncedSearch, effectiveSourceFilter, goodNewsOnly, router]);

  const loadArticles = useCallback(
    async (pageNum: number, append = false) => {
      setLoading(true);
      try {
        const data = await fetchArticles({
          page: pageNum,
          search: debouncedSearch || undefined,
          good_news_only: goodNewsOnly || undefined,
          source:
            effectiveSourceFilter !== "all" ? effectiveSourceFilter : undefined,
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
    [debouncedSearch, effectiveSourceFilter, goodNewsOnly]
  );

  const loadMetadata = useCallback(async () => {
    const [sourcesResult, statsResult] = await Promise.allSettled([
      fetchSources(),
      fetchStats(),
    ]);

    if (sourcesResult.status === "fulfilled") {
      setSources(sourcesResult.value.sources);
    }

    if (statsResult.status === "fulfilled") {
      setStats(statsResult.value);
    }
  }, []);

  const waitForRefreshCompletion = useCallback(async () => {
    const deadline = Date.now() + REFRESH_STATUS_TIMEOUT_MS;

    while (Date.now() < deadline) {
      const status = await fetchRefreshStatus();

      if (status.status !== "processing") {
        return status;
      }

      await new Promise((resolve) =>
        window.setTimeout(resolve, REFRESH_STATUS_POLL_INTERVAL_MS)
      );
    }

    return null;
  }, []);

  const openApiKeyHelp = useCallback(
    (feedback: ApiKeyFeedback) => {
      setApiKeyFeedback(feedback);
      setSettingsOpen(true);
      onboardingRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    },
    []
  );

  useEffect(() => {
    if (isLoaded) {
      loadArticles(1);
    }
  }, [isLoaded, loadArticles]);

  useEffect(() => {
    if (!isLoaded) return;
    void loadMetadata();
  }, [isLoaded, loadMetadata]);

  const handleRefresh = async () => {
    if (!apiKey) {
      openApiKeyHelp({
        status: "missing",
        message:
          "No NewsAPI key is saved. Add one here or use the inline form before refreshing.",
      });
      toast({
        title: "NewsAPI key required",
        description:
          "Add your NewsAPI key below or in Settings before refreshing headlines.",
      });
      return;
    }
    setRefreshing(true);
    setApiKeyFeedback(null);
    try {
      const refreshResponse = await refreshArticles(apiKey);
      const currentRequestValidatedKey =
        refreshResponse.message !== DUPLICATE_REFRESH_MESSAGE;

      if (!currentRequestValidatedKey) {
        toast({
          title: "Refresh already running",
          description:
            "Another refresh request is already in progress. Waiting for its final status now.",
        });
      }

      const refreshStatus = await waitForRefreshCompletion();

      if (refreshStatus === null) {
        toast({
          title: "Refresh still running",
          description:
            "The backend is still processing articles. You can keep browsing cached articles and check back shortly.",
        });
        return;
      }

      if (refreshStatus.status === "failed") {
        throw new Error(refreshStatus.message);
      }

      await Promise.all([loadArticles(1), loadMetadata()]);

      if (currentRequestValidatedKey) {
        setApiKeyFeedback({
          status: "accepted",
          message:
            "Your saved NewsAPI key was accepted during the last refresh.",
        });
      }

      toast({
        title: currentRequestValidatedKey
          ? "Refresh complete"
          : "Refresh finished",
        description:
          refreshStatus.new_articles > 0
            ? `Processed ${refreshStatus.processed_articles} new article${refreshStatus.processed_articles === 1 ? "" : "s"}.`
            : currentRequestValidatedKey
              ? "No new articles were added this time."
              : "The in-progress refresh finished without adding new articles.",
      });
    } catch (err) {
      if (err instanceof RefreshRequestError) {
        if (err.code === "missing_api_key") {
          openApiKeyHelp({
            status: "missing",
            message:
              "No NewsAPI key is saved. Add one here or use the inline form before refreshing.",
          });
          toast({
            title: "NewsAPI key required",
            description:
              "Add your NewsAPI key below or in Settings before refreshing headlines.",
            variant: "destructive",
          });
          return;
        }

        if (err.code === "invalid_api_key") {
          openApiKeyHelp({
            status: "invalid",
            message:
              "The saved NewsAPI key was rejected. Update it in Settings and try again.",
          });
          toast({
            title: "Refresh failed",
            description: "Invalid API key. Check your key in Settings.",
            variant: "destructive",
          });
          return;
        }

        toast({
          title:
            err.code === "upstream_timeout"
              ? "NewsAPI validation timed out"
              : "Refresh failed",
          description: err.message,
          variant: "destructive",
        });
        return;
      }

      const message = err instanceof Error ? err.message : "Refresh failed";
      toast({
        title: "Refresh failed",
        description: message,
        variant: "destructive",
      });
    } finally {
      setRefreshing(false);
    }
  };

  const handleLoadMore = () => {
    loadArticles(page + 1, true);
  };

  const handleSaveApiKey = (key: string) => {
    setApiKey(key);
    setApiKeyFeedback(null);
  };

  if (!isLoaded) return null;

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
        {!hasApiKey && (
          <div ref={onboardingRef} className="mb-6">
            <ApiKeySetup onSubmit={handleSaveApiKey} variant="inline" />
          </div>
        )}

        <div className="flex flex-wrap items-center gap-4 mb-4">
          <GoodNewsToggle
            checked={goodNewsOnly}
            onCheckedChange={setGoodNewsOnly}
          />
          <SourceFilter
            sources={sources}
            value={effectiveSourceFilter}
            onValueChange={setSourceFilter}
          />
        </div>

        <StatsBar stats={stats} />

        <ArticleFeed
          articles={articles}
          hasMore={hasMore}
          hasApiKey={hasApiKey}
          loading={loading}
          onLoadMore={handleLoadMore}
        />
      </main>

      <SettingsDialog
        open={settingsOpen}
        onOpenChange={setSettingsOpen}
        apiKey={apiKey}
        onUpdateKey={handleSaveApiKey}
        onClearKey={() => {
          clearApiKey();
          setApiKeyFeedback({
            status: "missing",
            message:
              "No NewsAPI key is saved. Add one here or use the inline form before refreshing.",
          });
        }}
        feedback={apiKeyFeedback}
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
