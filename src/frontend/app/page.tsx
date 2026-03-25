"use client";

import { Suspense, useEffect, useState, useCallback, useRef } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useApiKey } from "@/hooks/use-api-key";
import { useDebounce } from "@/hooks/use-debounce";
import {
  fetchArticles,
  fetchCategories,
  fetchRefreshStatus,
  fetchSources,
  fetchStats,
  RefreshRequestError,
  refreshArticles,
} from "@/lib/api";
import type {
  Article,
  Category,
  RefreshStatusResponse,
  Source,
  StatsResponse,
} from "@/types/article";
import { AboutModal } from "@/components/about-modal";
import { ApiKeySetup } from "@/components/api-key-setup";
import { Header } from "@/components/header";
import { GoodNewsToggle } from "@/components/good-news-toggle";
import { RefreshStatusCard } from "@/components/refresh-status-card";
import { CategoryFilter } from "@/components/category-filter";
import { CountryFilter } from "@/components/country-filter";
import { SourceFilter } from "@/components/source-filter";
import { StatsBar } from "@/components/stats-bar";
import { ArticleFeed } from "@/components/article-feed";
import {
  SettingsDialog,
  type ApiKeyFeedback,
} from "@/components/settings-dialog";
import { toast } from "@/hooks/use-toast";
import {
  getNextObservedProcessingKey,
  getRefreshProcessingObservationKey,
  shouldResumeRefreshPolling,
} from "@/lib/refresh-status";

const REFRESH_STATUS_POLL_INTERVAL_MS = 1000;
const REFRESH_STATUS_TIMEOUT_MS = 120000;
const DUPLICATE_REFRESH_MESSAGE = "Refresh already in progress.";

interface ArticleQueryState {
  search?: string;
  good_news_only?: boolean;
  source?: string;
  category?: string;
  country?: string;
}

function articleQueryMatches(
  left: ArticleQueryState,
  right: ArticleQueryState
) {
  return (
    left.search === right.search &&
    left.good_news_only === right.good_news_only &&
    left.source === right.source &&
    left.category === right.category &&
    left.country === right.country
  );
}

function HomeContent() {
  const { apiKey, setApiKey, clearApiKey, hasApiKey, isLoaded } = useApiKey();
  const router = useRouter();
  const searchParams = useSearchParams();
  const onboardingRef = useRef<HTMLDivElement>(null);
  const currentQueryRef = useRef(searchParams.toString());
  const articleQueryRef = useRef<ArticleQueryState>({});
  const latestArticleRequestIdRef = useRef(0);
  const lastObservedProcessingKeyRef = useRef<string | null>(null);
  const lastTimedOutRefreshStatusRef = useRef<RefreshStatusResponse | null>(null);
  const refreshStatusPollRef = useRef<Promise<RefreshStatusResponse | null> | null>(
    null
  );

  const [articles, setArticles] = useState<Article[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [refreshStatus, setRefreshStatus] =
    useState<RefreshStatusResponse | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [aboutOpen, setAboutOpen] = useState(false);
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
  const [countryFilter, setCountryFilter] = useState(
    searchParams.get("country") || "all"
  );
  const [categoryFilter, setCategoryFilter] = useState(
    searchParams.get("category") || "all"
  );

  const debouncedSearch = useDebounce(searchValue);
  const effectiveSourceFilter =
    sourceFilter === "all" ||
    sources.length === 0 ||
    sources.some((source) => source.source_name === sourceFilter)
      ? sourceFilter
      : "all";
  const effectiveCategoryFilter =
    categoryFilter === "all" ||
    categories.length === 0 ||
    categories.some((cat) => cat.name === categoryFilter)
      ? categoryFilter
      : "all";
  const currentArticleQuery: ArticleQueryState = {
    search: debouncedSearch || undefined,
    good_news_only: goodNewsOnly || undefined,
    source: effectiveSourceFilter !== "all" ? effectiveSourceFilter : undefined,
    category: effectiveCategoryFilter !== "all" ? effectiveCategoryFilter : undefined,
    country: countryFilter !== "all" ? countryFilter : undefined,
  };
  const currentArticleQueryKey = JSON.stringify(currentArticleQuery);

  articleQueryRef.current = currentArticleQuery;

  useEffect(() => {
    currentQueryRef.current = searchParams.toString();

    const nextSearchValue = searchParams.get("search") || "";
    const nextGoodNewsOnly = searchParams.get("good_news") === "true";
    const nextSourceFilter = searchParams.get("source") || "all";
    const nextCountryFilter = searchParams.get("country") || "all";
    const nextCategoryFilter = searchParams.get("category") || "all";

    setSearchValue((currentValue) =>
      currentValue === nextSearchValue ? currentValue : nextSearchValue
    );
    setGoodNewsOnly((currentValue) =>
      currentValue === nextGoodNewsOnly ? currentValue : nextGoodNewsOnly
    );
    setSourceFilter((currentValue) =>
      currentValue === nextSourceFilter ? currentValue : nextSourceFilter
    );
    setCountryFilter((currentValue) =>
      currentValue === nextCountryFilter ? currentValue : nextCountryFilter
    );
    setCategoryFilter((currentValue) =>
      currentValue === nextCategoryFilter ? currentValue : nextCategoryFilter
    );
  }, [searchParams]);

  useEffect(() => {
    if (searchValue !== debouncedSearch) {
      return;
    }

    const params = new URLSearchParams();
    if (debouncedSearch) params.set("search", debouncedSearch);
    if (goodNewsOnly) params.set("good_news", "true");
    if (effectiveSourceFilter !== "all") {
      params.set("source", effectiveSourceFilter);
    }
    if (countryFilter !== "all") {
      params.set("country", countryFilter);
    }
    if (effectiveCategoryFilter !== "all") {
      params.set("category", effectiveCategoryFilter);
    }
    const nextQuery = params.toString();

    if (nextQuery === currentQueryRef.current) {
      return;
    }

    currentQueryRef.current = nextQuery;
    router.push(nextQuery ? `?${nextQuery}` : "/", { scroll: false });
  }, [
    countryFilter,
    debouncedSearch,
    effectiveCategoryFilter,
    effectiveSourceFilter,
    goodNewsOnly,
    router,
    searchValue,
  ]);

  const loadArticles = useCallback(async (
    pageNum: number,
    append = false,
    throwOnError = false
  ) => {
    const requestId = ++latestArticleRequestIdRef.current;
    const requestQuery = articleQueryRef.current;

    setLoading(true);

    try {
      const data = await fetchArticles({
        page: pageNum,
        ...requestQuery,
      });

      if (
        latestArticleRequestIdRef.current !== requestId ||
        !articleQueryMatches(articleQueryRef.current, requestQuery)
      ) {
        return;
      }

      setArticles((prev) =>
        append ? [...prev, ...data.articles] : data.articles
      );
      setHasMore(data.has_more);
      setPage(data.page);
    } catch (err) {
      if (
        latestArticleRequestIdRef.current !== requestId ||
        !articleQueryMatches(articleQueryRef.current, requestQuery)
      ) {
        return;
      }

      toast({
        title: "Failed to load articles",
        description: err instanceof Error ? err.message : "Please try again later.",
        variant: "destructive",
      });

      if (throwOnError) {
        throw err;
      }
    } finally {
      if (latestArticleRequestIdRef.current === requestId) {
        setLoading(false);
      }
    }
  }, []);

  const loadMetadata = useCallback(async () => {
    const [sourcesResult, categoriesResult, statsResult, refreshStatusResult] =
      await Promise.allSettled([
        fetchSources(),
        fetchCategories(),
        fetchStats(),
        fetchRefreshStatus(),
      ]);

    if (sourcesResult.status === "fulfilled") {
      setSources(sourcesResult.value.sources);
    }

    if (categoriesResult.status === "fulfilled") {
      setCategories(categoriesResult.value.categories);
    }

    if (statsResult.status === "fulfilled") {
      setStats(statsResult.value);
    }

    if (refreshStatusResult.status === "fulfilled") {
      setRefreshStatus(refreshStatusResult.value);
    }
  }, []);

  const waitForRefreshCompletion = useCallback(async () => {
    if (refreshStatusPollRef.current) {
      return refreshStatusPollRef.current;
    }

    const deadline = Date.now() + REFRESH_STATUS_TIMEOUT_MS;
    const pollPromise = (async () => {
      let latestObservedStatus: RefreshStatusResponse | null = null;

      while (Date.now() < deadline) {
        const status = await fetchRefreshStatus();
        latestObservedStatus = status;
        setRefreshStatus(status);
        lastTimedOutRefreshStatusRef.current = null;

        lastObservedProcessingKeyRef.current = getNextObservedProcessingKey({
          refreshStatus: status,
        });

        if (status.status !== "processing") {
          return status;
        }

        await new Promise((resolve) =>
          window.setTimeout(resolve, REFRESH_STATUS_POLL_INTERVAL_MS)
        );
      }

      lastObservedProcessingKeyRef.current = getNextObservedProcessingKey({
        refreshStatus: null,
        timedOut: true,
      });
      lastTimedOutRefreshStatusRef.current = latestObservedStatus;
      return null;
    })();

    refreshStatusPollRef.current = pollPromise;

    try {
      return await pollPromise;
    } finally {
      if (refreshStatusPollRef.current === pollPromise) {
        refreshStatusPollRef.current = null;
      }
    }
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
  }, [currentArticleQueryKey, isLoaded, loadArticles]);

  useEffect(() => {
    if (!isLoaded) return;
    void loadMetadata();
  }, [isLoaded, loadMetadata]);

  useEffect(() => {
    const processingKey = getRefreshProcessingObservationKey(refreshStatus);

    if (
      !shouldResumeRefreshPolling({
        isLoaded,
        refreshStatus,
        refreshing,
        lastObservedProcessingKey: lastObservedProcessingKeyRef.current,
        timedOutObservationActive:
          refreshStatus === lastTimedOutRefreshStatusRef.current,
      }) ||
      processingKey === null
    ) {
      return;
    }

    let cancelled = false;
    lastObservedProcessingKeyRef.current = processingKey;
    lastTimedOutRefreshStatusRef.current = null;

    const resumeRefreshPolling = async () => {
      setRefreshing(true);

      try {
        const terminalStatus = await waitForRefreshCompletion();

        if (!terminalStatus || cancelled) {
          return;
        }

        await Promise.all([loadArticles(1), loadMetadata()]);
      } catch (err) {
        if (!cancelled) {
          toast({
            title: "Unable to refresh status",
            description:
              err instanceof Error
                ? err.message
                : "Failed to load the latest refresh state.",
            variant: "destructive",
          });
        }
      } finally {
        if (!cancelled) {
          setRefreshing(false);
        }
      }
    };

    void resumeRefreshPolling();

    return () => {
      cancelled = true;
    };
  }, [
    isLoaded,
    loadArticles,
    loadMetadata,
    refreshStatus,
    refreshing,
    waitForRefreshCompletion,
  ]);

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
            ? `Added ${refreshStatus.new_articles} new article${refreshStatus.new_articles === 1 ? "" : "s"}.`
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
        onAboutClick={() => setAboutOpen(true)}
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

        <nav aria-label="Article filters" className="flex flex-wrap items-center gap-4 mb-4">
          <GoodNewsToggle
            checked={goodNewsOnly}
            onCheckedChange={setGoodNewsOnly}
          />
          <CountryFilter
            value={countryFilter}
            onValueChange={setCountryFilter}
          />
          <CategoryFilter
            categories={categories}
            value={effectiveCategoryFilter}
            onValueChange={setCategoryFilter}
          />
          <SourceFilter
            sources={sources}
            value={effectiveSourceFilter}
            onValueChange={setSourceFilter}
          />
        </nav>

        <RefreshStatusCard refreshStatus={refreshStatus} stats={stats} />

        <StatsBar stats={stats} />

        <ArticleFeed
          articles={articles}
          hasMore={hasMore}
          hasApiKey={hasApiKey}
          loading={loading}
          onLoadMore={handleLoadMore}
        />
      </main>

      <AboutModal open={aboutOpen} onOpenChange={setAboutOpen} />

      <SettingsDialog
        open={settingsOpen}
        onOpenChange={setSettingsOpen}
        apiKey={apiKey}
        onUpdateKey={handleSaveApiKey}
        onGuardrailsUpdated={async () => {
          await Promise.all([loadArticles(1, false, true), loadMetadata()]);
        }}
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
